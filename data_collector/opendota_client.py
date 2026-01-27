import asyncio
import aiohttp

BASE_URL = "https://api.opendota.com/api"
API_KEY = "API_KEY_HERE"

# 100 is the maximum matches per call from Open Dota
async def get_public_matches(session, limit=100, less_than_match_id=None):
    if limit <= 0:
        return None

    url = f"{BASE_URL}/publicmatches"
    
    # 70 = Divine+
    # 60 = Ancient+
    params = {
        "min_rank": 60,
        "api_key": API_KEY,
    }

    if less_than_match_id is not None:
        params["less_than_match_id"] = less_than_match_id

    async with session.get(url, params=params) as response:
        data = await response.json()
        if response.status != 200:
            return response.status
        return data
    
async def get_match(session, match_id, semaphore):
    url = f"{BASE_URL}/matches/{match_id}"

    params = {
        "api_key": API_KEY
    }

    max_request_tries = 3

    for i in range(max_request_tries):
        async with semaphore:
            async with session.get(url, params=params) as response:
                data = await response.json()
                if response.status == 200:
                    return data
                elif response.status == 429:
                    print(f"request for {match_id} status 429: retrying {i + 1}")
                    await asyncio.sleep(5)
                else:
                    return None