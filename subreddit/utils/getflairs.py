from dotenv import dotenv_values
from helper.utils import getUserAgent
import aiohttp

# Load DOTENV
config = dotenv_values(".env")

# Credentials
client_id = config.get("client_id")
client_secret = config.get("client_secret")
user_agent = getUserAgent()


# Get Flairs
async def getFlairs(redditName, rate_limit):
    async with rate_limit:
        # Get Token
        auth = aiohttp.BasicAuth(client_id, client_secret)
        data = {
            "grant_type": "password",
            "username": config.get("username"),
            "password": config.get("password"),
        }
        headers = {"User-Agent": user_agent}

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://www.reddit.com/api/v1/access_token",
                auth=auth,
                headers=headers,
                data=data,
            ) as response:
                token = await response.json()
                token = token["access_token"]
                headers["Authorization"] = f"bearer {token}"

        # Get Flair
        allFlairs = []
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"https://oauth.reddit.com/r/{redditName}/api/link_flair_v2",
                    headers=headers,
                ) as response:
                    data = await response.json()
                    for flairs in data:
                        allFlairs.append(
                            {
                                "text": flairs["text"],
                                "color": flairs["background_color"],
                            }
                        )
        except Exception as e:
            print(f"No post flairs found for r/{redditName}!", e)

    return allFlairs
