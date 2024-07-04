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
            getSubredditsByTopics(topic, rate_limit, master, DONE, SUBREDDITS_DONE)
        )

    await asyncio.gather(*tasks)


if __name__ == "__main__":
    # Get all subreddit names based on the topics above
    master = {}

    # Variables to track  topics done fetching subreddits
    DONE = [len(topics)]
    SUBREDDITS_DONE = [0]

    # Start scraping subreddits
    asyncio.run(main())

    # Dump all subreddits per topicsize after scraping
    master = dict(sorted(master.items()))
    with open("subreddits.json", "w") as fp:
        json.dump(master, fp, indent=4)
