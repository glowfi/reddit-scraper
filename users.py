#!/bin/python3

import json
from dotenv import dotenv_values
import uuid
import requests
from bs4 import BeautifulSoup
import time
from datetime import timedelta
from datetime import datetime
import random
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


def getTrophies():
    url = "https://www.reddit.com/wiki/trophies/"
    headers = {
        "User-Agent": f"{getUserAgent()}",
    }
    response = requests.get(url, headers=headers)

    html_content = response.content
    soup = BeautifulSoup(html_content, "html.parser")

    master = [
        {
            "title": "Bellwether",
            "image_link": "https://a.thumbs.redditmedia.com/GnIq6cHQCTUioRxU4opnYO0PJibxEBb_K3cyln1tXJ0.png",
        }
    ]
    tables = soup.find_all("table")
    for table in tables:
        for row in table.find_all("tr"):
            # Extract image link
            image_link = row.find("img")["src"] if row.find("img") else None
            tmp = {}
            if image_link:
                tmp["image_link"] = f"https:{image_link}"
                text = row.get_text().strip("\n")
                title = text.split("\n")[0]
                tmp["title"] = title
                master.append(tmp)
    return master


async def getRedditorInfo(redditor_name, aid, usersArr, sid, sname, rate_limit):
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
                await redditor.load()
                if hasattr(redditor, "id"):
                    await redditor.subreddit.load()
                usersArr.append(
                    {
                        "id": aid,
                        "username": redditor_name,
                        "password": "pass",
                        "cakeDay": "NA",
                        "cakeDayHuman": "NA",
                        "age": "NA",
                        "avatar_img": "NA",
                        "banner_img": "NA",
                        "publicDescription": "NA",
                        "over18": "NA",
                        "keycolor": "NA",
                        "primarycolor": "NA",
                        "iconcolor": "NA",
                        "subreddits_member": [[sid, sname]],
                        "trophies": random.choices(trophies, k=random.randint(1, 5)),
                        "supended": True,
                    }
                )
            else:
                print(f"{redditor_name}")
                await redditor.load()
                if hasattr(redditor, "id"):
                    await redditor.subreddit.load()
                usersArr.append(
                    {
                        "id": redditor.id,
                        "username": redditor_name,
                        "password": "pass",
                        "cakeDay": redditor.created_utc,
                        "cakeDayHuman": getDate(redditor.created_utc),
                        "age": epoch_age(redditor.created_utc),
                        "avatar_img": redditor.icon_img,
                        "banner_img": redditor.subreddit.banner_img,
                        "publicDescription": redditor.subreddit.public_description,
                        "over18": redditor.subreddit.over18,
                        "keycolor": redditor.subreddit.key_color,
                        "primarycolor": redditor.subreddit.primary_color,
                        "iconcolor": redditor.subreddit.icon_color,
                        "subreddits_member": [[sid, sname]],
                        "trophies": random.choices(trophies, k=random.randint(1, 5)),
                        "supended": False,
                    }
                )


async def getUsers(usersArr, seenUsers, postsData, rate_limit):
    async with rate_limit:

        async def helper(data):
            for comments in data:
                authorID = comments["author_id"]
                author = comments["author"]

                if authorID and authorID not in seenUsers:
                    await getRedditorInfo(
                        author,
                        authorID,
                        usersArr,
                        postsData["subreddit_id"],
                        postsData["subreddit"],
                        rate_limit,
                    )
                    seenUsers[authorID] = True
                elif authorID and authorID in seenUsers:
                    for user in usersArr:
                        subreddit_lists = user.get("subreddits_member", [])
                        data = [postsData["subreddit_id"], postsData["subreddit"]]
                        if data not in subreddit_lists:
                            subreddit_lists.append(data)

                await helper(comments["replies"])

        if "comments" in postsData and postsData:
            await helper(postsData["comments"])


# Global variables
usersArr = []
seenUsers = {}
trophies = getTrophies()


async def main():
    with open("./posts.json", "r") as fp:
        posts = json.load(fp)
        tasks = []
        rate_limit = AsyncLimiter(
            int(config.get("HITS_USERS")), int(config.get("TIME_USERS"))
        )

        for post in posts[:200]:
            if "comments" in post and post:
                tasks.append(getUsers(usersArr, seenUsers, post, rate_limit))

        await asyncio.gather(*tasks)

    # Create Users
    with open("users.json", "w") as f:
        json.dump(usersArr, f, indent=4)


if __name__ == "__main__":
    asyncio.run(main())
