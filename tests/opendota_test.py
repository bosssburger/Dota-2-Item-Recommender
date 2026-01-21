import sys
sys.path.append("C:\\Users\\bosss\\OneDrive\\Documents\\Random\\Dota Item Recommender")
import data_collector.opendota_client as client
import unittest

class TestClient(unittest.TestCase):

    def test_bad_limit(self):
        json = client.get_public_matches(0)
        self.assertIsNone(json)
        json = client.get_public_matches(-1)
        self.assertIsNone(json)

    def test_success(self):
        json = client.get_public_matches(1)
        self.assertIsNotNone(json)

if __name__ == "__main__":
    unittest.main()
