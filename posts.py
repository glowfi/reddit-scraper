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
import logging
import urllib.parse
from urllib.parse import parse_qs
from urllib.parse import urlparse, urlunparse
import copy
import random
import string
import requests


# Logging
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
for logger_name in ("asyncpraw", "asyncprawcore"):
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)


# Load DOTENV
config = dotenv_values(".env")


# Custom User agent string
def getUserAgent():
    letters = string.ascii_lowercase
    length = 10
    return f"User agent by {str(uuid.uuid4())}-" + "".join(
        random.choice(letters) for _ in range(length)
    )


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


def sanitize_url(url):
    parsed_url = urlparse(url)
    new_url = urlunparse(
        (
            parsed_url.scheme,
            parsed_url.netloc,
            parsed_url.path.rstrip("/"),
            parsed_url.params,
            parsed_url.query,
            parsed_url.fragment,
        )
    )
    return str(new_url)


# Add user
def add(author, author_id, allUsers, subreddit, subredditID):
    if author_id and author_id not in seenUsers:
        tmp = {
            "id": author_id,
            "username": author,
            "password": "pass",
            "subreddits_member": (
                [[subredditID, subreddit]] if subreddit and subredditID else []
            ),
            "trophies": random.choices(trophies, k=random.randint(1, 5)),
        }

        allUsers[author_id] = dict(sorted(tmp.copy().items()))
        seenUsers.add(author_id)

    else:
        subreddit_lists = allUsers.get(author_id).get("subreddits_member", [])
        if subredditID and subreddit and subreddit_lists:
            data = [subredditID, subreddit]
            if data not in subreddit_lists:
                subreddit_lists.append(data)


# Get comments for this post
async def send_request_comments(url, rate_limit):
    async with rate_limit:
        async with aiohttp.ClientSession() as session:
            my_headers = copy.deepcopy(headers)
            my_headers["User-Agent"] = f"{getUserAgent()}"
            async with session.get(
                url=url,
                headers=my_headers,
            ) as response:
                return await response.text()


# Log comments to a file
def log_error(msg, filename):
    with open(filename, "a") as fp:
        fp.write(msg + "\n")


# Get all user comment
async def getComments(url, topic, rate_limit):
    RESP_FROM_REQ = None
    async with rate_limit:
        print("url:", url)
        res_data = []
        try:
            resData = await send_request_comments(url, rate_limit)
            RESP_FROM_REQ = resData

            MAX_RETRIES = 30
            NO_TRIES = MAX_RETRIES

            while NO_TRIES:
                if "kind" in resData:
                    resData = json.loads(resData)
                    if (
                        isinstance(resData, list)
                        and len(resData) > 0
                        and "kind" in resData[0]
                    ):
                        print(
                            "\x1b[6;30;42m"
                            + f"Got Back data in {abs(MAX_RETRIES-NO_TRIES)+1} tries !"
                            + "\x1b[0m"
                        )
                        log_error(f"Got {url}", "comments-got.txt")
                        break
                else:
                    print(
                        "\033[41m"
                        + f"Retrying {abs(MAX_RETRIES-NO_TRIES)+1} ...."
                        + "\033[0m"
                    )
                    log_error(f"Retrying {url}", "comments-retry.txt")

                    resData = requests.get(url).text
                    # resData = await send_request_comments(url, rate_limit)
                    RESP_FROM_REQ = resData

                NO_TRIES -= 1

            if NO_TRIES == 0:
                return []

            res_data = resData[1].get("data", {}).get("children", [])
            currPostAuthor = (
                resData[0]
                .get("data", {})
                .get("children", [0])[0]
                .get("data", [])
                .get("author", "")
            )
            currPostAuthorID = (
                resData[0]
                .get("data", {})
                .get("children", [0])[0]
                .get("data", [])
                .get("author_fullname", "")
                .replace("t2_", "")
            )
            print("ALERT .....", currPostAuthor, currPostAuthorID)
            if currPostAuthor and currPostAuthorID:
                add(
                    currPostAuthor,
                    currPostAuthorID,
                    allUsers,
                    resData[0]
                    .get("data", {})
                    .get("children", [0])[0]
                    .get("data", [])
                    .get("subreddit", ""),
                    resData[0]
                    .get("data", {})
                    .get("children", [0])[0]
                    .get("data", [])
                    .get("subreddit_id", "")
                    .replace("t5_", ""),
                )

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
                    if tmp["comment_html"]:
                        tmp["comment_html"] = (
                            tmp["comment_html"]
                            .replace("&lt;", "<")
                            .replace("&gt;", ">")
                        )

                    tmp["comment_ups"] = comm.get("data", {}).get("ups", "")
                    tmp["category"] = topic

                    for i in tmp:
                        if tmp[i] == "":
                            notGotValues += 1

                    if notGotValues >= 4:
                        continue

                    author, authorID = tmp["author"], tmp["author_id"]

                    if author and authorID:
                        add(
                            author,
                            authorID,
                            allUsers,
                            tmp["subreddit_name"],
                            tmp["subreddit_id"],
                        )
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
            print("HERE: ...", len(res_data), url)
            print(RESP_FROM_REQ)
            print("\033[41m" + f"Error Occured:  {e} " + "\033[0m")


def handleURL(encodedURL: str):
    if encodedURL.find("https://www.reddit.com/media") != -1:
        data = parse_qs(encodedURL)
        return [data[item] for item in data][0][0]

    else:
        return urllib.parse.unquote(encodedURL)


def post_content(data, subm):
    if hasattr(subm, "poll_data"):
        return {"type": "Invalid", "data": []}
    else:
        # Multi [video+img] [media_metadata.id.e (check Image or RedditVideo)] [1anj4fi]
        hasMulti = data.get("media_metadata", "")
        isGallery = data.get("is_gallery", False)
        st = set()
        if hasMulti and not isGallery:
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
                            hasMulti.get(imageID, {})
                            .get("variants", {})
                            .get("gif", {})
                            .get("resolutions", [])
                        )
                        if hasGif:
                            for objs in hasGif:
                                if objs.get("u", ""):
                                    objs["u"] = handleURL(objs["u"])

                            final_data.append(
                                {
                                    "type": "gif",
                                    "id": imageID,
                                    "data": sorted(hasGif, key=lambda x: x["y"]),
                                }
                            )
                        # image
                        else:
                            dat = hasMulti.get(imageID, {}).get("p", [])
                            for objs in dat:
                                if objs.get("u", ""):
                                    objs["u"] = handleURL(objs["u"])
                            sourceImage = hasMulti.get(imageID, {}).get("s", {})
                            if sourceImage:
                                dat.append(sourceImage)
                            if dat:
                                final_data.append(
                                    {
                                        "type": "image",
                                        "id": imageID,
                                        "data": sorted(dat, key=lambda x: x["y"]),
                                    }
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
                                        "dash_url": handleURL(dat.get("dashUrl", "")),
                                        "hls_url": handleURL(dat.get("hlsUrl", "")),
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
                for objs in hasGif:
                    if objs.get("url", ""):
                        objs["url"] = handleURL(objs["url"])

                return {
                    "data": sorted(hasGif, key=lambda x: x["height"]),
                    "id": str(uuid.uuid4()),
                    "type": "gif",
                }

        # Video [secure_media.reddit_video.dash_url.hls_url.fallback_url.scrubber_media_url] [1alyf9i]
        val = data.get("secure_media", {})
        if val:
            hasVideo = data.get("secure_media", {}).get("reddit_video", {})
            # print(hasVideo, "hasVideo")
            if hasVideo:
                vid_data = {
                    "dash_url": handleURL(hasVideo.get("dash_url", "")),
                    "hls_url": handleURL(hasVideo.get("hls_url", "")),
                    "fallback_url": handleURL(hasVideo.get("fallback_url", "")),
                    "scrubber_media_url": handleURL(
                        hasVideo.get("scrubber_media_url", "")
                    ),
                }
                return {"data": vid_data, "type": "video", "id": str(uuid.uuid4())}

        # Image [preview.resolutions] [1amno06]
        if data.get("preview", {}):
            hasImage = data.get("preview", {}).get("images")[0].get("resolutions", [])
            if data:
                sourceImage = data.get("preview", {}).get("images")[0].get("source", {})
                for objs in hasImage:
                    if objs.get("url", ""):
                        objs["url"] = handleURL(objs["url"])
                if sourceImage:
                    hasImage.append(sourceImage)
                return {
                    "data": sorted(hasImage, key=lambda x: x["height"]),
                    "id": str(uuid.uuid4()),
                    "type": "image",
                }

        # Gallery [media_metadata.id.p] [1anhgwz]
        hasGallery = data.get("media_metadata", "")
        imageGallery = []
        if hasGallery:
            for imageID in hasGallery:
                imgs = hasGallery.get(imageID, {}).get("p", [])
                if imgs:
                    for objs in imgs:
                        if objs.get("u", ""):
                            objs["u"] = handleURL(objs["u"])
                    sourceImage = hasGallery.get(imageID, {}).get("s", {})
                    if sourceImage:
                        imgs.append(sourceImage)
                    imageGallery.append({"id": imageID, "pics": imgs})

            if imageGallery:
                for objs in imageGallery:
                    getPics = objs.get("pics", [])
                    if getPics:
                        objs.get("pics", []).sort(key=lambda x: x["y"])

            return {
                "data": imageGallery,
                "type": "gallery",
                "id": str(uuid.uuid4()),
            }

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


# Trophies
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


# Awards
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
            timeout=32,
        ) as reddit:
            subreddit = await reddit.subreddit(subredditName)

            postCounter = 0
            async for posts in subreddit.hot(limit=None):
                obj = posts.__dict__

                try:
                    submission = await reddit.submission(id=obj["id"])
                    print(submission.title)
                    data = vars(submission)

                    author = data.get("author", "")
                    if not author:
                        continue

                    postBody = data["selftext"]
                    postHTML = data["selftext_html"]
                    if postHTML:
                        postHTML = postHTML.replace("&lt;", "<").replace("&gt;", ">")

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
                            "subreddit_id": data.get("subreddit_id", "").replace(
                                "t5_", ""
                            ),
                            "author": author,
                            "author_id": data.get("author_fullname", "").replace(
                                "t2_", ""
                            ),
                            "title": data.get("title", ""),
                            "postflair": data.get("link_flair_text", ""),
                            "postflaircolor": data.get(
                                "link_flair_background_color", ""
                            ),
                            "num_comments": data.get("num_comments", ""),
                            "ups": data.get("ups", ""),
                            "awards": random.choices(awards, k=random.randint(0, 4)),
                            "comments": await getComments(
                                sanitize_url(
                                    f"https://reddit.com{obj.get('permalink','')}"
                                )
                                + ".json",
                                topic,
                                rate_limit,
                            ),
                            "media_metadata": dat,
                            "createdat": data["created_utc"],
                            "createdatHuman": unix_to_relative_time(
                                data["created_utc"]
                            ),
                            "text": data["url"],
                            "text_html": "",
                            "over_18": data.get("over_18", ""),
                            "spoiler": data.get("spoiler", ""),
                            "link_type": True,
                            "category": topic,
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
                            "subreddit_id": data.get("subreddit_id", "").replace(
                                "t5_", ""
                            ),
                            "author": author,
                            "author_id": data.get("author_fullname", "").replace(
                                "t2_", ""
                            ),
                            "title": data.get("title", ""),
                            "postflair": data.get("link_flair_text", ""),
                            "postflaircolor": data.get(
                                "link_flair_background_color", ""
                            ),
                            "num_comments": data.get("num_comments", ""),
                            "ups": data.get("ups", ""),
                            "awards": random.choices(awards, k=random.randint(0, 4)),
                            "comments": await getComments(
                                sanitize_url(
                                    f"https://reddit.com{obj.get('permalink','')}"
                                )
                                + ".json",
                                topic,
                                rate_limit,
                            ),
                            "media_content": dat,
                            "createdat": data["created_utc"],
                            "createdatHuman": unix_to_relative_time(
                                data["created_utc"]
                            ),
                            "text": postBody,
                            "text_html": postHTML,
                            "over_18": data.get("over_18", ""),
                            "spoiler": data.get("spoiler", ""),
                            "link_type": False,
                            "category": topic,
                        }

                    if post_data:
                        finalPostsData.append(dict(sorted(post_data.items())))

                        postCounter += 1
                        print(
                            "\x1b[6;30;42m"
                            + f"POST COUNTER .................... {topic} {postCounter}"
                            + "\x1b[0m"
                        )

                        DONE[0] += 1
                        print(
                            "\x1b[6;30;42m"
                            + f"TOTAL POSTS FETCHED ............  {DONE[0]}"
                            + "\x1b[0m"
                        )

                        if (
                            postCounter == POSTS_PER_SUBREDDIT
                            or DONE[0] >= TOTAL_REQUIRED_POSTS
                        ):
                            break

                except Exception as e:
                    with open("noposts.txt", "a+") as f:
                        _url = f'https://reddit.com/r/{str(data.get("subreddit", "").display_name)}/{str(data.get("id", ""))}/{str(submission.title)}'
                        f.write(f"{str(e)}  {str(id)} {_url} \n")


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
            tasks.append(getPostData_subreddit(topic, currSubreddit, rate_limit))

    await asyncio.gather(*tasks)


if __name__ == "__main__":
    finalPostsData = []
    allUsers = {}
    seenUsers = set()
    awards, trophies = [], []
    POSTS_PER_SUBREDDIT = int(config.get("POSTS_PER_SUBREDDIT"))
    TOTAL_SUBREDDITS_PER_TOPICS = int(config.get("TOTAL_SUBREDDITS_PER_TOPICS"))
    topicsize = int(config.get("TOPIC_SIZE"))
    TOTAL_REQUIRED_POSTS = TOTAL_SUBREDDITS_PER_TOPICS * topicsize * POSTS_PER_SUBREDDIT

    DONE = [0]

    subredditJSON = []
    with open("./subreddits.json", "r") as f:
        subredditJSON = json.load(f)

    # Get Trophies and awards
    asyncio.run(waiter(awards, trophies))
    awards = awards[0]
    trophies = trophies[0]

    # Get Posts
    asyncio.run(main())

    # Create Posts
    with open("posts.json", "w") as f:
        json.dump(finalPostsData, f, indent=4)

    # Create Users
    with open("users.json", "w") as f:
        json.dump(allUsers, f, indent=4)

    # Log allcomments done
    with open("comments-got.txt", "r") as fp:
        data1 = fp.readlines()

    with open("comments-retry.txt", "r") as fp:
        data2 = fp.readlines()

    data1 = set([i.split(" ")[-1].strip("\n") for i in data1])
    data2 = set([i.split(" ")[-1].strip("\n") for i in data2])

    with open("comments-confirm.txt", "w") as fp:
        status = data1 == data2
        fp.write(f"{status}")
