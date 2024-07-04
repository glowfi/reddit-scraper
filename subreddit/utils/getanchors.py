from dotenv import dotenv_values
from helper.utils import getUserAgent
import asyncpraw

# Load DOTENV
config = dotenv_values(".env")

# Credentials
client_id = config.get("client_id")
client_secret = config.get("client_secret")
user_agent = getUserAgent()


# Get Anchors
async def getAnchors(subredditName, rate_limit):
    async with rate_limit:
        anchorTags = {}
        async with asyncpraw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent,
            username=config.get("username"),
            password=config.get("password"),
            ratelimit_seconds=300,
            timeout=32,
        ) as reddit:
            subreddit = await reddit.subreddit(subredditName)
            topbar = [widget async for widget in subreddit.widgets.topbar()]
            if len(topbar) > 0:
                probably_menu = topbar[0]
                assert isinstance(probably_menu, asyncpraw.models.Menu)
                for item in probably_menu:
                    if isinstance(item, asyncpraw.models.Submenu):
                        anchorTags[item.text] = []
                        for child in item:
                            anchorTags[item.text].append([child.text, child.url])
                    else:  # MenuLink
                        anchorTags[item.text] = item.url

    return anchorTags
