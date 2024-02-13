#!/bin/python3

import json
from dotenv import dotenv_values
import uuid
import time
from datetime import timedelta
from datetime import datetime
import asyncpraw
from aiolimiter import AsyncLimiter
import asyncio


# Load DOTENV
config = dotenv_values(".env")


# Custom User agent string
def getUserAgent():
    return f"User agent by {str(uuid.uuid4())}"


# Credentials
client_id = config.get("client_id")
client_secret = config.get("client_secret")
user_agent = getUserAgent()


def epoch_age(epoch_time):
    # Convert the input to Unix epoch time if it's not already in that format
    if isinstance(epoch_time, str):
        epoch_time = int(float(epoch_time[1:]))

    current_time = int(time.time())
    age_in_seconds = current_time - epoch_time

    years = age_in_seconds // (365 * 24 * 60 * 60)

    return f"{years}yr(s)"


def getDate(timestamp):
    # Convert Unix epoch time to datetime object
    dt = datetime.utcfromtimestamp(timestamp)

    # Subtract 8 hours from the original timezone to get the local timezone
    dt = dt - timedelta(hours=8)

    # Format the date and time in desired format
    return dt.strftime("%d %B %Y")


async def getRedditorInfo(redditor_name, aid, userInfo, rate_limit):
    async with rate_limit:
        async with asyncpraw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=getUserAgent(),
            username=config.get("username"),
            password=config.get("password"),
        ) as reddit:
            try:
                redditor = await reddit.redditor(redditor_name, fetch=True)
            except Exception as e:
                with open("user_errors.txt", "a") as fp:
                    fp.write(
                        str(redditor_name) + " " + str(e) + "\n",
                    )
                print(f"Error with {redditor_name}")
                return

            if not hasattr(redditor, "id"):
                print(f"{redditor_name} Account Suspended")
                userInfo[aid]["cakeDay"] = "NA"
                userInfo[aid]["cakeDayHuman"] = "NA"
                userInfo[aid]["age"] = "NA"
                userInfo[aid]["avatar_img"] = "NA"
                userInfo[aid]["banner_img"] = "NA"
                userInfo[aid]["publicDescription"] = "NA"
                userInfo[aid]["over18"] = "NA"
                userInfo[aid]["keycolor"] = "NA"
                userInfo[aid]["primarycolor"] = "NA"
                userInfo[aid]["iconcolor"] = "NA"
                userInfo[aid]["supended"] = True
            else:
                try:
                    print(f"{redditor_name}")
                    await redditor.load()
                    if hasattr(redditor, "id"):
                        await redditor.subreddit.load()
                        print(f"Got Back {redditor_name}!")
                except Exception as e:
                    print("Handled Exception!", e)

                if redditor:
                    try:
                        userInfo[aid]["cakeDay"] = redditor.created_utc
                        userInfo[aid]["cakeDayHuman"] = getDate(redditor.created_utc)
                        userInfo[aid]["age"] = epoch_age(redditor.created_utc)
                        userInfo[aid]["avatar_img"] = redditor.icon_img
                        userInfo[aid]["banner_img"] = (
                            redditor.subreddit.banner_img if redditor.subreddit else ""
                        )
                        userInfo[aid]["publicDescription"] = (
                            redditor.subreddit.public_description
                            if redditor.subreddit
                            else ""
                        )
                        userInfo[aid]["over18"] = (
                            redditor.subreddit.over18 if redditor.subreddit else ""
                        )
                        userInfo[aid]["keycolor"] = (
                            redditor.subreddit.key_color if redditor.subreddit else ""
                        )
                        userInfo[aid]["primarycolor"] = (
                            redditor.subreddit.primary_color
                            if redditor.subreddit
                            else ""
                        )
                        userInfo[aid]["iconcolor"] = (
                            redditor.subreddit.icon_color if redditor.subreddit else ""
                        )
                        userInfo[aid]["supended"] = False

                        total_users[0] -= 1
                        print(f"More {total_users} left ...")

                    except Exception as e:
                        with open("user_errors.txt", "a") as fp:
                            fp.write(
                                str(redditor_name) + " " + str(e) + "\n",
                            )
                        print(f"Error with {redditor_name}")


with open("./users.json") as f:
    userData = json.load(f)


HIT_USERS = int(config.get("HITS_USERS"))
TIME_USERS = int(config.get("TIME_USERS"))
total_users = [len(userData)]


async def main():
    tasks = []
    rate_limit = AsyncLimiter(HIT_USERS, TIME_USERS)
    for user in userData:
        redditor_name = userData.get(user, {}).get("username", "")
        id = userData.get(user, {}).get("id", "")
        if redditor_name and id:
            tasks.append(getRedditorInfo(redditor_name, id, userData, rate_limit))

    await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())
    with open("./users.json", "w") as f:
        json.dump(userData, f)
    len(userData)
