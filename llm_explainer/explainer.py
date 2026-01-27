from ml_recommender import recommender as rec
from lib import db_client
import lightgbm as lgb
from google import genai
from google.genai import types

API_KEY = "AIzaSyC0Bmzg6Oj9Qp-2-kVieZ9EM732M_x2x-8"
CLIENT = genai.Client(api_key=API_KEY)

def convert_reccs_to_string(recc_list):
    item_ids = rec.load_ids_from_file("item_ids.json")
    result = ""

    for (item_id, score) in recc_list:
        result += item_ids.get(str(item_id)) + ": " + str(score) + "\n"

    return result

def build_prompt(curr_items, enemy_heroes, player_hero, item_reccs):
    prompt = ""
    item_ids = rec.load_ids_from_file("item_ids.json")
    hero_ids = rec.load_ids_from_file("hero_ids.json")

    prompt += "Player Hero: " + hero_ids.get(str(player_hero)) + "\n"
    prompt += "Current Items: "

    for item_id in curr_items:
        prompt += item_ids.get(str(item_id)) + ", "
    
    prompt = prompt[:-2] + "\n"

    prompt += "Enemy Heroes: "

    for hero_id in enemy_heroes:
        prompt += hero_ids.get(str(hero_id)) + ", "

    prompt = prompt[:-2] + "\n"

    prompt += "Top 5 Item Recommendations" + "\n" + item_reccs

    return prompt

def main():
    db_client.create_pick_rate_table()
    model = lgb.Booster(model_file=rec.MODEL_PATH)
    
    base_features, items, enemies, hero_id = rec.build_player_features()

    candidates = rec.build_candidates(base_features)

    top_reccs = rec.recommend_items(base_features, candidates, model)[:5]
    string_reccs = convert_reccs_to_string(top_reccs)
    prompt = build_prompt(items, enemies, hero_id, string_reccs)

    response = CLIENT.models.generate_content(
        model = "gemini-3-flash-preview",
        config=types.GenerateContentConfig(
            system_instruction="You are a Dota 2 Coach explaining the top 5 item choices for a hero in a match." \
            " You are given the hero the player is playing, the items they already have, the heroes on the enemy team, " \
            "and the top 5 recommended next items with their scores from a machine learning algorithm. For each item, provide " \
            "a comprehensive explanation of why the item is good taking into consideration the given information."
        ),
        contents = prompt,
    )

    print(response.text)


if __name__ == "__main__":
    main()