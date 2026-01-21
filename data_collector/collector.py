import sys
import time
sys.path.append("C:\\Users\\bosss\\OneDrive\\Documents\\Random\\Dota Item Recommender")
import lib.db_client as db_client
import opendota_client
import asyncio
import aiohttp

MAX_CONCURRENT_REQUESTS = 12
BATCH_DELAY = 0.5
TIMEOUT = aiohttp.ClientTimeout(total=20)

async def collect_and_store(num_matches_hundreds=1):
    seen_match_ids = db_client.fetch_match_ids()
    
    # OpenDota API only queries a window of recent matches by default
    # But it includes a parameter for seeing earlier matches lower than a given id
    # Track the lowest match_id seen and pass that in to avoid getting the same matches over and over
    min_match_id = min(seen_match_ids) if len(seen_match_ids) > 0 else None

    semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

    async with aiohttp.ClientSession(timeout=TIMEOUT) as session:
    
        for i in range(num_matches_hundreds):
            print(f"===Fetching batch {i + 1}===")
            pub_matches = await opendota_client.get_public_matches(session, less_than_match_id=min_match_id)

            if isinstance(pub_matches, int):
                print(f"Error in fetching public matches: {pub_matches}")
                await asyncio.sleep(5)
                continue

            match_ids = []
            for m in pub_matches:
                match_id = m.get("match_id")
                lobby_type = m.get("lobby_type")

                lobby_check = lobby_type is not None and (lobby_type == 0 or lobby_type == 7)
                match_check = match_id is not None and match_id not in seen_match_ids
                if lobby_check and match_check:
                    seen_match_ids.add(match_id)
                    match_ids.append(match_id)
                    min_match_id = match_id if min_match_id is None or match_id < min_match_id else min_match_id

            tasks = [opendota_client.get_match(session, match_id, semaphore) for match_id in match_ids]
            match_response_list = await asyncio.gather(*tasks)
            non_None_results = [resp for resp in match_response_list if resp]

            db_client.store_matches(non_None_results)

            await asyncio.sleep(BATCH_DELAY)

if __name__ == "__main__":
    db_client.init_db()

    print("=====Begin match collection=====")
    start_total = time.monotonic()

    asyncio.run(collect_and_store(970))

    total_runtime = time.monotonic() - start_total
    print(f"Total runtime: {total_runtime} seconds")