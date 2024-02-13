import json
import asyncio
from pprint import pprint
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
from concurrent.futures import ThreadPoolExecutor


with open("./posts.json", "r") as fp:
    posts = json.load(fp)


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


def add(author, author_id, allUsers, subreddit, subredditID):
    if author_id and author_id not in seenUsers:
        tmp = {
            "id": author_id,
            "username": author,
            "password": "pass",
            "subreddits_member": [[subredditID, subreddit]],
        }

        allUsers[author_id] = dict(sorted(tmp.copy().items()))
        seenUsers.add(author_id)

    else:
        for user in allUsers:
            subreddit_lists = allUsers.get(user).get("subreddits_member", [])
            data = [subredditID, subreddit]
            if data not in subreddit_lists:
                subreddit_lists.append(data)


def deflattenComments(currPost, allUsers):
    currPostAuthor = currPost["author"]
    currPostAuthorID = currPost["author_id"]
    add(
        currPostAuthor,
        currPostAuthorID,
        allUsers,
        currPost["subreddit"],
        currPost["subreddit_id"],
    )

    def helper(data):
        for comments in data:
            author, authorID = comments["author"], comments["author_id"]

            if author and authorID:
                add(
                    author,
                    authorID,
                    allUsers,
                    currPost["subreddit"],
                    currPost["subreddit_id"],
                )
            if "replies" in comments:
                helper(comments["replies"])

    if currPost and "comments" in currPost and currPost["comments"]:
        helper(currPost["comments"])


def getAllUsers():
    c = 0
    with ThreadPoolExecutor(max_workers=30) as executor:
        for post in posts:
            print("Post :", c)
            if "comments" in post and post:
                deflattenComments(post, allUsers)
                executor.submit(deflattenComments, post, allUsers)
                c += 1


# Global Variables
allUsers = {}
seenUsers = set()
# trophies = getTrophies()


async def getRedditorInfo(name):
    pass


async def main():
    tasks = []
    for user in allUsers:
        tasks.append(getRedditorInfo(user["username"]))

    # await


if __name__ == "__main__":
    getAllUsers()
    # with open("test.json", "w") as f:
    #     json.dump(allUsers, f, indent=4)
