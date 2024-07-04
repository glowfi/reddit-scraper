from dotenv import dotenv_values
from helper.utils import getUserAgent
import asyncpraw

# Load DOTENV
config = dotenv_values(".env")

# Credentials
client_id = config.get("client_id")
client_secret = config.get("client_secret")
user_agent = getUserAgent()


# get moderators name
async def getModeratorsNames(redditName, rate_limit):
    async with rate_limit:
        moderators = []
        async with asyncpraw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent,
            username=config.get("username"),
            password=config.get("password"),
            ratelimit_seconds=300,
            timeout=32,
        ) as reddit:
            sredditMode = await reddit.subreddit(redditName)
            async for moderator in sredditMode.moderator:
                moderators.append(
                    [moderator.name, str(moderator.id).replace("t2_", "")]
                )
    return moderators
