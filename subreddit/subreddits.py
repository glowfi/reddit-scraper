import json
import asyncio
from dotenv import dotenv_values
from aiolimiter import AsyncLimiter

from helper.utils import start_logging
from helper.utils import getUserAgent

from subreddit.utils.subredditsbytopic import getSubredditsByTopics
from subreddit.constants import topics

# Logging
start_logging()

# Load DOTENV
config = dotenv_values(".env")

# Credentials
client_id = config.get("client_id")
client_secret = config.get("client_secret")
user_agent = getUserAgent()


# Function to handle scraping of subreddits
async def main():
    tasks = []
    rate_limit = AsyncLimiter(int(config.get("HITS_SUB")), int(config.get("TIME_SUB")))
    topicsize = int(config.get("TOPIC_SIZE"))

    for topic in list(set(topics[:topicsize])):
        tasks.append(
            getSubredditsByTopics(
                topic, rate_limit, master, DONE, SUBREDDITS_DONE, seen_subreddits
            )
        )

    await asyncio.gather(*tasks)


### Global Variables

# Get all subreddit names based on the topics above
master = {}
seen_subreddits = {}

# Variables to track  topics done fetching subreddits
DONE = [len(topics)]
SUBREDDITS_DONE = [0]


# Main run function
async def run():
    # Start scraping subreddits
    await main()

    # Dump all subreddits per topicsize after scraping
    global master
    master = dict(sorted(master.items()))
    with open("subreddits.json", "w") as fp:
        json.dump(master, fp, indent=4)

    st = set()
    for topiks in master:
        for i in master[topiks]:
            st.add(i["title"])

    with open("count-sreddit.txt", "w") as fp:
        fp.write(f"Sreddits Count: {len(st)}")
