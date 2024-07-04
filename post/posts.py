import json
from dotenv import dotenv_values

import asyncio
from aiolimiter import AsyncLimiter

from helper.utils import start_logging, getUserAgent
from post.utils.awards import getAwards
from post.utils.trophies import getTrophies
from post.utils.post_content.get_post_data import get_post_data_subreddit


# Logging
start_logging()

# Load DOTENV
config = dotenv_values(".env")

# Credentials
client_id = config.get("client_id")
client_secret = config.get("client_secret")
user_agent = getUserAgent()


async def completeTrophies(a, t):
    val1 = await getAwards()
    val2 = await getTrophies()

    a.append(val1)
    t.append(val2)


async def waiter(a, t):
    await completeTrophies(a, t)


async def main():
    tasks = []
    rate_limit = AsyncLimiter(
        int(config.get("HITS_POSTS")), int(config.get("TIME_POSTS"))
    )

    for topic in subredditJSON:
        for currSubreddit in subredditJSON[topic]:
            tasks.append(
                get_post_data_subreddit(
                    topic,
                    currSubreddit,
                    rate_limit,
                    allUsers,
                    seenUsers,
                    trophies,
                    awards,
                    finalPostsData,
                    DONE,
                    POSTS_PER_SUBREDDIT,
                    TOTAL_REQUIRED_POSTS,
                )
            )

    await asyncio.gather(*tasks)


### Global Variables

# Final post data
finalPostsData = []

# Track users
allUsers = {}
seenUsers = set()

# Awards and trophies
awards, trophies = [], []

# Global varaibles(self explainatory)
POSTS_PER_SUBREDDIT = int(config.get("POSTS_PER_SUBREDDIT"))
TOTAL_SUBREDDITS_PER_TOPICS = int(config.get("TOTAL_SUBREDDITS_PER_TOPICS"))
topicsize = int(config.get("TOPIC_SIZE"))
TOTAL_REQUIRED_POSTS = TOTAL_SUBREDDITS_PER_TOPICS * topicsize * POSTS_PER_SUBREDDIT
DONE = [0]
subredditJSON = []


# Main run function
async def run():
    with open("./subreddits.json", "r") as f:
        global subredditJSON
        subredditJSON = json.load(f)

    # Get Trophies and awards
    global awards
    global trophies
    await waiter(awards, trophies)
    awards = awards[0]
    trophies = trophies[0]

    # Get Posts
    await main()

    # Create Posts
    with open("posts.json", "w") as f:
        json.dump(finalPostsData, f, indent=4)

    # Create Users
    with open("users.json", "w") as f:
        json.dump(allUsers, f, indent=4)

    # Check allcomments done
    with open("comments-got.txt", "r") as fp:
        data1 = fp.readlines()

    with open("comments-retry.txt", "r") as fp:
        data2 = fp.readlines()

    data1 = set([i.split(" ")[-1].strip("\n") for i in data1])
    data2 = set([i.split(" ")[-1].strip("\n") for i in data2])

    with open("comments-status.txt", "w") as fp:
        status = data1 == data2
        fp.write(f"{status} Got:{len(data1)} Retry:{len(data2)}")
