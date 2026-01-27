import lightgbm as lgb
import pandas as pd
import numpy as np
import json
from pathlib import Path
from lib import db_client
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score

MIN_PAIR_OCCURRENCE = 200
MODULE_PATH = Path(__file__).parent
MODEL_PATH = MODULE_PATH / "dota_item_recommender_model.txt"

def load_ids_from_file(filename):
    file_path = (MODULE_PATH.parent / "data" / filename)
    
    f = open(file_path, "r")
    data = json.load(f)
    
    #ids = set(map(int, data.keys()))

    f.close()
    
    return data

def add_item_binary_features(dataset):
    item_cols = ["item_0", "item_1", "item_2", "item_3", "item_4", "item_5"]

    all_items = pd.concat([dataset[col] for col in item_cols])

    all_items = all_items.dropna()

    # Drop empty slots and non-buyable items like aegis
    unbuyable = {0, 117, 33, 1804, 260, 725, 727}
    all_items = all_items[~(all_items.astype(int).isin(unbuyable))]

    item_counts = all_items.value_counts()

    min_occurrences = 100
    frequent_items = item_counts[item_counts >= min_occurrences].index.tolist()

    new_item_cols = [f"has_item_{i}" for i in frequent_items]
    item_df = pd.DataFrame(0, index=dataset.index, columns=new_item_cols, dtype=np.uint8)
    dataset = pd.concat([dataset, item_df], axis=1)

    for col in item_cols:
        for item_id in frequent_items:
            dataset[f"has_item_{item_id}"] |= (dataset[col] == item_id)

    dataset.drop(columns=item_cols, inplace=True)

    return dataset

def add_enemy_binary_features(dataset):
    hero_ids = set(map(int, load_ids_from_file("hero_ids.json").keys()))

    enemy_cols = [f"enemy_hero_{hero}" for hero in hero_ids]
    enemy_df = pd.DataFrame(0, index=dataset.index, columns=enemy_cols, dtype=np.uint8) 

    dataset = pd.concat([dataset, enemy_df], axis=1)

    match_groups = dataset.groupby("match_id")

    for _, group in match_groups:
        radiant = group[group["isRadiant"] == 1]
        dire = group[group["isRadiant"] == 0]

        radiant_heroes = radiant["hero_id"].to_numpy()
        dire_heroes = dire["hero_id"].to_numpy()

        for hero_id in dire_heroes:
            dataset.loc[radiant.index, f"enemy_hero_{hero_id}"] = 1

        for hero_id in radiant_heroes:
            dataset.loc[dire.index, f"enemy_hero_{hero_id}"] = 1

    return dataset

def prepare_dataset():
    conn = db_client.get_db_conn()

    data = pd.read_sql_query("""
    SELECT 
        players.match_id,
        players.hero_id,
        players.isRadiant,
        CASE WHEN players.isRadiant = matches.radiant_win THEN 1 ELSE 0 END AS win,
        players.item_0,
        players.item_1,
        players.item_2,
        players.item_3,
        players.item_4,
        players.item_5
    FROM players
    LEFT JOIN matches ON matches.match_id == players.match_id
    """, conn)
    
    data = add_item_binary_features(data)
    data = add_enemy_binary_features(data)

    return data

def train_model(dataset):
    X = dataset.drop(columns=["win", "match_id"])
    y = dataset["win"]

    categorical = [X.columns.get_loc("hero_id")]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=21)

    train_data = lgb.Dataset(X_train, label=y_train, categorical_feature=categorical)
    test_data = lgb.Dataset(X_test, label=y_test, categorical_feature=categorical)

    params = {
        "objective": "binary",
        "metric": "auc",
        "learning_rate": 0.01,
        "num_leaves": 47,
        "max_depth": 9,
        "min_data_in_leaf": 800,
        "lambda_l1": 0.8,
        "lambda_l2": 1.5,
        "feature_fraction": 0.7,
        "bagging_fraction": 0.8,
        "bagging_freq": 5,
        "num_threads": -1,
        "verbosity": -1
    }

    model = lgb.train(
        params,
        train_data,
        valid_sets=[test_data],
        num_boost_round=1500
        # callbacks=[
        # lgb.early_stopping(150)
        # ]
    )
    print("AUC:", roc_auc_score(y_test, model.predict(X_test, num_iteration=model.best_iteration)))

    file_path = (MODULE_PATH / "feature_names.json")

    with open(file_path, "w") as f:
        json.dump(list(X.columns), f)

    return model

def predict_win_prob(features, feature_names, model):
    X = features
    X = X.reindex(columns=feature_names, fill_value=0)

    return model.predict(X, num_iteration=model.best_iteration)[0]

def load_feature_names():
    file_path = (MODULE_PATH / "feature_names.json")
    with open(file_path, "r") as f:
        return json.load(f)
    
def load_and_normalize_picks():
    conn = db_client.get_db_conn()

    pick_rate_table = pd.read_sql_query("""
        SELECT hero_id, item_id, pair_count, pick_rate
        FROM hero_item_stats
    """, conn)

    max_rate = max(pick_rate_table["pick_rate"])

    return {
        (int(row.hero_id), int(row.item_id)): [row.pair_count, row.pick_rate / max_rate]
        for _, row in pick_rate_table.iterrows()
    }

def recommend_items(base_features, candidate_items, model):
    results = []
    feature_names = load_feature_names()
    hero_item_stats = load_and_normalize_picks()

    win_prob_base = predict_win_prob(base_features, feature_names, model)
    alpha = 0.7
    
    hero_id = int(base_features.at[0, "hero_id"])
    for item_id in candidate_items:
        hero_item_count = hero_item_stats.get((hero_id, item_id), None)
        if hero_item_count is None:
            hero_item_count = 0
        else:
            hero_item_count = hero_item_count[0]
        if  hero_item_count >= MIN_PAIR_OCCURRENCE:
            features = base_features.copy()
            features[f"has_item_{item_id}"] = 1

            win_prob = predict_win_prob(features, feature_names, model)
            pick_rate = hero_item_stats.get((hero_id, item_id), None)
            if pick_rate is None:
                continue
            else:
                pick_rate = pick_rate[1]

            final_score = alpha * (win_prob - win_prob_base) + (1 - alpha) * pick_rate
            results.append((item_id, final_score))

    return sorted(results, key=lambda x: x[1], reverse=True)

def build_player_features():
    hero = input("Enter the hero_id of the hero you are playing: ")
    team = input("Enter 1 if you are radiant and 0 if you are dire: ")

    features = dict.fromkeys(load_feature_names(), 0)
    items = []
    enemy_heroes = []

    features["hero_id"] = int(hero)
    features["isRadiant"] = int(team)

    for i in range(6):
        item_id = int(input(f"Enter the item_id of item {i + 1} (0 if slot is empty): "))
        if item_id != 0:
            features[f"has_item_{item_id}"] = 1
            items.append(item_id)
    
    for i in range(5):
        enemy_hero_id = int(input(f"Enter the hero_id of enemy hero #{i + 1}: "))
        features[f"enemy_hero_{enemy_hero_id}"] = 1
        enemy_heroes.append(enemy_hero_id)

    return pd.DataFrame([features]), items, enemy_heroes, hero

def build_candidates(base_features):
    candidates = []
    for column in base_features:
        if "has_item" in column and base_features.at[0, column] != 1:
            candidates.append(int(column[9:]))
    
    return candidates

def main():
    db_client.create_pick_rate_table()
    model = lgb.Booster(model_file=MODEL_PATH)
    
    base_features, _, _, _ = build_player_features()

    candidates = build_candidates(base_features)

    top_reccs = recommend_items(base_features, candidates, model)[:10]
    item_ids = load_ids_from_file("item_ids.json")
    text_reccs = []
    for (item_id, _) in top_reccs:
        text_reccs.append(item_ids.get(str(item_id)))
    print(text_reccs)

if __name__ == "__main__":
    main()