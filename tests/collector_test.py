from lib import db_client
import unittest
from tqdm import tqdm

class TestClient(unittest.TestCase):

    def test_db_sanity(self):
        conn = db_client.get_db_conn()
        cursor = conn.cursor()

        match_ids = cursor.execute("SELECT match_id FROM matches").fetchall()

        for match in tqdm(match_ids):
            match_id = match[0]
            num_players = cursor.execute(f"SELECT COUNT(*) FROM players WHERE match_id == {match_id}").fetchall()
            if num_players[0][0] != 10:
                print(f"not equal match {match_id}")
            self.assertEqual(num_players[0][0], 10)

        conn.close()

    def test_lobby_types_correct(self):
        conn = db_client.get_db_conn()
        cursor = conn.cursor()

        lobby_types = cursor.execute("SELECT lobby_type FROM matches").fetchall()

        conn.close()

        for lobby in tqdm(lobby_types):
            lobby = lobby[0]

            self.assertTrue(lobby == 0 or lobby == 7)

if __name__ == "__main__":
    unittest.main()
