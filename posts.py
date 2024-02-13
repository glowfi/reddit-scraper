#!/bin/python3

import asyncpraw
import json
import uuid
from bs4 import BeautifulSoup
import time
from datetime import timedelta
from datetime import datetime
import random
from dotenv import dotenv_values
import aiohttp
import asyncio
from aiolimiter import AsyncLimiter

# Load DOTENV
config = dotenv_values(".env")


# Custom User agent string
def getUserAgent():
    return f"User agent by {str(uuid.uuid4())}"


# Credentials
client_id = config.get("client_id")
client_secret = config.get("client_secret")
user_agent = getUserAgent()

# Headers
headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Encoding": "gzip,deflate,br",
    "Accept-Language": "en-US,en;q=0.5",
    "Connection": "keep-alive",
    "DNT": "1",
    "Host": "www.reddit.com",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "TE": "trailers",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": f"{getUserAgent()}",
}


async def getComments(url, topic, rate_limit):
    async with rate_limit:
        print("url:", url)
        try:
            res_data = []
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url=url,
                    headers=headers,
                ) as response:
                    resData = await response.json()
                    res_data = resData[1].get("data", []).get("children", [])

            async def helper(_res_data, parent_id):
                finalData = []
                for comm in _res_data:
                    # Comment txt : data->(author,author_fullname(t2),created_utc,body,id,ups)
                    # Replies : replies->data->children[]

                    tmp = {}
                    notGotValues = 0

                    tmp["subreddit_id"] = (
                        comm.get("data", {}).get("subreddit_id", "").replace("t5_", "")
                    )
                    tmp["subreddit_name"] = comm.get("data", {}).get("subreddit", "")
                    tmp["author"] = comm.get("data", {}).get("author", "")
                    tmp["author_id"] = (
                        comm.get("data", {})
                        .get("author_fullname", "")
                        .replace("t2_", "")
                    )
                    tmp["created_utc"] = comm.get("data", {}).get("created_utc", "")
                    tmp["parent_comment_id"] = parent_id
                    tmp["comment_id"] = comm.get("data", {}).get("id", "")
                    tmp["comment"] = comm.get("data", {}).get("body", "")
                    tmp["comment_html"] = comm.get("data", {}).get("body_html", "")
                    tmp["comment_ups"] = comm.get("data", {}).get("ups", "")
                    tmp["category"] = topic

                    for i in tmp:
                        if tmp[i] == "":
                            notGotValues += 1

                    if notGotValues >= 4:
                        continue

                    print(tmp)
                    try:
                        tmp["replies"] = await helper(
                            comm.get("data", {})
                            .get("replies", {})
                            .get("data", {})
                            .get("children", []),
                            comm.get("data", {}).get("id", ""),
                        )
                    except Exception as e:
                        tmp["replies"] = []

                    finalData.append(dict(sorted(tmp.copy().items())))

                return finalData

            allComments = await helper(res_data, "isParent")
            return allComments

        except Exception as e:
            print("Error Occured: ", e)


def post_content(data, subm):
    if hasattr(subm, "poll_data"):
        return {"type": "Invalid", "data": []}
    else:
        # Multi [video+img] [media_metadata.id.e (check Image or RedditVideo)] [1anj4fi]
        hasMulti = data.get("media_metadata", "")
        st = set()
        if hasMulti:
            for imageID in hasMulti:
                mediaType = hasMulti.get(imageID, {}).get("e", "")
                st.add(mediaType)
            if len(st) >= 2:
                final_data = []
                for imageID in hasMulti:
                    mediaType = hasMulti.get(imageID, {}).get("e", "")
                    if mediaType == "Image":
                        # gif
                        hasGif = (
                            hasMulti.get(imageID, {}).get("variants", {}).get("gif", {})
                        )
                        if hasGif:
                            return {"type": "gif", "id": imageID, "data": hasGif}
                        # image
                        else:
                            pass
                            dat = hasMulti.get(imageID, {}).get("p", [])
                            if dat:
                                final_data.append(
                                    {"type": "image", "id": imageID, "data": dat}
                                )
                    # videos
                    elif mediaType == "RedditVideo":
                        dat = hasMulti.get(imageID, {})
                        if dat:
                            final_data.append(
                                {
                                    "type": "video",
                                    "id": imageID,
                                    "data": {
                                        "dash_url": dat.get("dashUrl", ""),
                                        "hls_url": dat.get("hlsUrl", ""),
                                    },
                                }
                            )

                return {"type": "multi", "data": final_data}

        # Gif [preview.variants.gif] [1an7ms7]
        if data.get("preview", {}):
            hasGif = (
                data.get("preview", {})
                .get("images")[0]
                .get("variants", {})
                .get("gif", {})
                .get("resolutions", [])
            )

            if hasGif:
                return {"data": hasGif, "id": str(uuid.uuid4()), "type": "gif"}

        # Video [secure_media.reddit_video.dash_url.hls_url.fallback_url.scrubber_media_url] [1alyf9i]
        val = data.get("secure_media", {})
        if val:
            hasVideo = data.get("secure_media", {}).get("reddit_video", {})
            # print(hasVideo, "hasVideo")
            if hasVideo:
                vid_data = {
                    "dash_url": hasVideo.get("dash_url", ""),
                    "hls_url": hasVideo.get("hls_url", ""),
                    "fallback_url": hasVideo.get("fallback_url", ""),
                    "scrubber_media_url": hasVideo.get("scrubber_media_url", ""),
                }
                return {"data": vid_data, "type": "video", "id": str(uuid.uuid4())}

        # Image [preview.resolutions] [1amno06]
        if data.get("preview", {}):
            hasImage = data.get("preview", {}).get("images")[0].get("resolutions", [])
            if data:
                return {"data": hasImage, "id": str(uuid.uuid4()), "type": "image"}

        # Gallery [media_metadata.id.p] [1anhgwz]
        hasGallery = data.get("media_metadata", "")
        imageGallery = []
        if hasGallery:
            for imageID in hasGallery:
                imgs = hasGallery.get(imageID, {}).get("p", [])
                if imgs:
                    imageGallery.append({"id": imageID, "pics": imgs})

            return {"data": imageGallery, "type": "gallery", "id": str(uuid.uuid4())}

        return {"type": "text", "data": []}


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


async def getTrophies():
    url = "https://www.reddit.com/wiki/trophies/"
    headers = {
        "User-Agent": f"{getUserAgent()}",
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(
            url=url,
            headers=headers,
        ) as response:
            # html_content = response.content
            html_content = await response.read()
            soup = BeautifulSoup(html_content.decode("utf-8"), "html5lib")

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


async def getAwards():
    url = "https://asyncpraw.readthedocs.io/en/latest/code_overview/models/submission.html#asyncpraw.models.Submission"
    headers = {
        "User-Agent": f"{getUserAgent()}",
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(
            url=url,
            headers=headers,
        ) as response:
            html_content = await response.read()
            soup = BeautifulSoup(html_content.decode("utf-8"), "html5lib")

    master = []
    tables = soup.find_all("table")
    for table in tables:
        for row in table.find_all("tr"):
            # Extract image link
            image_link = row.find("img")["src"] if row.find("img") else None
            tmp = {}
            if image_link:
                text = row.find("p").text
                tmp["title"] = f"{text}"
                tmp["image_link"] = f"{image_link}"
                master.append(tmp)
    return master


def unix_to_relative_time(unix_time):
    now = datetime.now()
    diff = now - datetime.fromtimestamp(unix_time)

    years = int(diff.days / 365)
    days = abs(diff.days) % 365
    hours = abs(diff.seconds) // 3600
    minutes = abs(diff.seconds) // 60 % 60
    seconds = abs(diff.seconds) % 60

    if years > 0:
        return f"{years} year{'' if years == 1 else 's'} ago"
    elif days > 0:
        plural = "day" if days == 1 else "days"
        return f"{days} {plural} ago"
    elif hours > 0:
        plural = "hour" if hours == 1 else "hours"
        return f"{hours} {plural} ago"
    elif minutes > 0:
        plural = "minute" if minutes == 1 else "minutes"
        return f"{minutes} {plural} ago"
    else:
        if seconds > 0:
            return "a moment ago"
        else:
            return "just now"


finalPostsData = []
usersArr = []
seenUsers = {}
POSTS_PER_SUBREDDIT = int(config.get("POSTS_PER_SUBREDDIT"))

subredditJSON = []
with open("./subreddits.json", "r") as f:
    subredditJSON = json.load(f)


async def getPostData_subreddit(topic, currSubreddit, rate_limit):
    async with rate_limit:
        subredditName = currSubreddit["title"].replace("r/", "")
        async with asyncpraw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=getUserAgent(),
            username=config.get("username"),
            password=config.get("password"),
            ratelimit_seconds=300,
        ) as reddit:
            subreddit = await reddit.subreddit(subredditName)

            async for posts in subreddit.hot(limit=POSTS_PER_SUBREDDIT):
                obj = posts.__dict__
                submission = await reddit.submission(id=obj["id"])
                print(submission.title, obj["permalink"])
                data = vars(submission)

                postBody = data["selftext"]
                postHTML = data["selftext_html"]

                dat = post_content(data, submission)

                post_data = {}

                if dat == "Invalid":
                    continue

                # Link type post
                if not postBody and not postHTML:
                    author = data.get("author", "")
                    if author:
                        author = author.name

                    post_data = {
                        "id": data.get("id", ""),
                        "subreddit": data.get("subreddit", "").display_name,
                        "subreddit_id": data.get("subreddit_id", "").replace("t5_", ""),
                        "author": author,
                        "author_id": data.get("author_fullname", "").replace("t2_", ""),
                        "title": data.get("title", ""),
                        "postflair": data.get("link_flair_text", ""),
                        "postflaircolor": data.get("link_flair_background_color", ""),
                        "num_comments": data.get("num_comments", ""),
                        "ups": data.get("ups", ""),
                        "awards": random.choices(
                            await getAwards(), k=random.randint(0, 4)
                        ),
                        "comments": await getComments(
                            f"https://reddit.com{obj.get('permalink','')}.json",
                            topic,
                            rate_limit,
                        ),
                        "media_metadata": dat,
                        "createdat": data["created_utc"],
                        "createdatHuman": unix_to_relative_time(data["created_utc"]),
                        "text": data["url"],
                        "text_html": "",
                        "over_18": data.get("over_18", ""),
                        "spoiler": data.get("spoiler", ""),
                        "link_type": True,
                    }

                elif dat["type"] in (
                    "video",
                    "gif",
                    "image",
                    "multi",
                    "gallery",
                    "text",
                ):
                    author = data.get("author", "")
                    if author:
                        author = author.name
                    post_data = {
                        "id": data.get("id", ""),
                        "subreddit": data.get("subreddit", "").display_name,
                        "subreddit_id": data.get("subreddit_id", "").replace("t5_", ""),
                        "author": author,
                        "author_id": data.get("author_fullname", "").replace("t2_", ""),
                        "title": data.get("title", ""),
                        "postflair": data.get("link_flair_text", ""),
                        "postflaircolor": data.get("link_flair_background_color", ""),
                        "num_comments": data.get("num_comments", ""),
                        "ups": data.get("ups", ""),
                        "awards": random.choices(
                            await getAwards(), k=random.randint(0, 4)
                        ),
                        "comments": await getComments(
                            f"https://reddit.com{obj.get('permalink','')}.json",
                            topic,
                            rate_limit,
                        ),
                        "media_content": dat,
                        "createdat": data["created_utc"],
                        "createdatHuman": unix_to_relative_time(data["created_utc"]),
                        "text": postBody,
                        "text_html": postHTML,
                        "over_18": data.get("over_18", ""),
                        "spoiler": data.get("spoiler", ""),
                        "link_type": False,
                    }

                if post_data:
                    finalPostsData.append(dict(sorted(post_data.items())))


async def main():
    tasks = []
    rate_limit = AsyncLimiter(
        int(config.get("HITS_POSTS")), int(config.get("TIME_POSTS"))
    )
    for topic in subredditJSON:
        for currSubreddit in subredditJSON[topic]:
            tasks.append(getPostData_subreddit(topic, currSubreddit, rate_limit))

    await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())

    # Create Posts
    with open("posts.json", "w") as f:
        json.dump(finalPostsData, f, indent=4)
