import sqlite3
from pathlib import Path

DB_FILENAME = "dota_item_recc.db"

def get_db_conn():
    db_path = Path(__file__).parent.parent/'data'/DB_FILENAME
    return sqlite3.connect(db_path.resolve())

def init_db():
    conn = get_db_conn()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS matches (
        match_id INTEGER PRIMARY KEY,
        duration INTEGER,
        radiant_win BOOLEAN,
        lobby_type INTEGER,
        patch INTEGER
    )""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS players (
        match_id INTEGER,
        hero_id INTEGER,
        isRadiant BOOLEAN,
        gold_per_min INTEGER,
        xp_per_min INTEGER,
        kills INTEGER,
        deaths INTEGER,
        assists INTEGER,
        item_0 INTEGER,
        item_1 INTEGER,
        item_2 INTEGER,
        item_3 INTEGER,
        item_4 INTEGER,
        item_5 INTEGER
    )""")

    conn.commit()
    conn.close()

def store_matches(response_list):
    conn = get_db_conn()
    cursor = conn.cursor()

    for match_json in response_list:
        if match_json.get("match_id") is None:
            print("Error with API response: no match_id")
        else:
            cursor.execute("""
                INSERT OR IGNORE INTO matches
                VALUES (?, ?, ?, ?, ?)""", (
                match_json["match_id"],
                match_json["duration"],
                match_json["radiant_win"],
                match_json["lobby_type"],
                match_json["patch"]
            ))

            if cursor.rowcount != 0:
                for p in match_json["players"]:
                    cursor.execute("""
                        INSERT INTO players VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", (
                        match_json["match_id"],
                        p["hero_id"],
                        p["isRadiant"],
                        p["gold_per_min"],
                        p["xp_per_min"],
                        p["kills"],
                        p["deaths"],
                        p["assists"],
                        p["item_0"],
                        p["item_1"],
                        p["item_2"],
                        p["item_3"],
                        p["item_4"],
                        p["item_5"],
                    ))
    
    conn.commit()
    conn.close()

def fetch_match_ids():
    seen_ids = set()

    conn = get_db_conn()
    cursor = conn.cursor()

    match_ids = cursor.execute("""
    SELECT match_id FROM matches
    """).fetchall()

    for id_record in match_ids:
        seen_ids.add(id_record[0])
    
    return seen_ids

def create_pick_rate_table():
    conn = get_db_conn()
    cursor = conn.cursor()

    cursor.execute("""CREATE TABLE IF NOT EXISTS hero_item_stats AS 
    SELECT
        hero_id,
        item_id,
        COUNT(*) AS pair_count,
        COUNT(*) * 1.0 /
        SUM(COUNT(*)) OVER (PARTITION BY hero_id) AS pick_rate
    FROM (
        SELECT hero_id, item_0 AS item_id FROM players WHERE item_0 != 0
        UNION ALL
        SELECT hero_id, item_1 FROM players WHERE item_1 != 0
        UNION ALL
        SELECT hero_id, item_2 FROM players WHERE item_2 != 0
        UNION ALL
        SELECT hero_id, item_3 FROM players WHERE item_3 != 0
        UNION ALL
        SELECT hero_id, item_4 FROM players WHERE item_4 != 0
        UNION ALL
        SELECT hero_id, item_5 FROM players WHERE item_5 != 0
    )
    GROUP BY hero_id, item_id;
    """)

    conn.commit()
    conn.close()