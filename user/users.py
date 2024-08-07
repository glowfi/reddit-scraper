import json
from dotenv import dotenv_values

import asyncio

from helper.utils import (
    start_logging,
    getUserAgent,
)
from user.get_user_info_alternate import getRedditorInfoAlternate
from user.utils import getProfilePics_alternate

# Logging
start_logging()

# Load DOTENV
config = dotenv_values(".env")

# Credentials
client_id = config.get("client_id")
client_secret = config.get("client_secret")
user_agent = getUserAgent()


async def main():
    tasks = []
    profilePics = getProfilePics_alternate()

    # rate_limit = AsyncLimiter(HIT_USERS, TIME_USERS)
    for user in userData:
        redditor_name = userData.get(user, {}).get("username", "")
        id = userData.get(user, {}).get("id", "")
        if redditor_name and id:
            # tasks.append(getRedditorInfo(redditor_name, id, userData, rate_limit))
            tasks.append(
                getRedditorInfoAlternate(id, userData, profilePics, total_users)
            )

    await asyncio.gather(*tasks)


# Global Variables
userData = [None]
total_users = [-1]
HIT_USERS = int(config.get("HITS_USERS"))
TIME_USERS = int(config.get("TIME_USERS"))


# Main run function
async def run():
    # Load all users generated by fetching posts
    with open("./users.json") as f:
        global userData
        userData = json.load(f)
        global total_users
        total_users = [len(userData)]

    # Get users
    await main()

    # Dump all users
    with open("./users.json", "w") as f:
        json.dump(userData, f, indent=4)
