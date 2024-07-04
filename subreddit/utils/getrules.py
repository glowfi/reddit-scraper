import asyncpraw
from dotenv import dotenv_values

from helper.utils import getUserAgent

# Load DOTENV
config = dotenv_values(".env")

# Credentials
client_id = config.get("client_id")
client_secret = config.get("client_secret")
user_agent = getUserAgent()


# Get Rules
async def getRules(redditName, rate_limit):
    async with rate_limit:
        async with asyncpraw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent,
            username=config.get("username"),
            password=config.get("password"),
            ratelimit_seconds=300,
            timeout=32,
        ) as reddit:
            allRules = []

            try:
                data = await reddit.subreddit(redditName)
                async for rule in data.rules:
                    tmp = rule.__dict__
                    obj = {}
                    obj["rule_title"] = tmp.get("short_name", "")
                    obj["rule_desc"] = tmp.get("description", "")
                    allRules.append(obj)
            except Exception as e:
                print(e)
                print(f"No rules found for r/{redditName}")

    return allRules
