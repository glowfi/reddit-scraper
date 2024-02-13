#!/bin/python3

import json
import asyncpraw
import asyncio
from numerize import numerize
import datetime
from dotenv import dotenv_values
import aiohttp
import random
import string
from aiolimiter import AsyncLimiter


# Load DOTENV
config = dotenv_values(".env")


# User agent
def getUserAgent():
    letters = string.ascii_lowercase
    length = 10
    return "".join(random.choice(letters) for _ in range(length))


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


# Topics
topics = [
    "Activism",
    "AddictionSupport",
    "Animals and Pets",
    "Art",
    "BeautyandMakeup",
    "Business,Economics,andFinance",
    "Careers",
    "Cars and MotorVehicles",
    "Celebrity",
    "CraftsandDIY",
    "Crypto",
    "Culture,Race,and Ethnicity",
    "Ethics and Philosophy",
    "Family and Relationships",
    "Fashion",
    "Fitness and Nutrition",
    "Food and Drink",
    "Funny/Humor",
    "Gaming",
    "Gender",
    "History",
    "Hobbies",
    "Home and Garden",
    "InternetCulture and Memes",
    "Law",
    "Learning and Education",
    "Marketplace and Deals",
    "MatureThemes and AdultContent",
    "Medical and MentalHealth",
    "Mens Health",
    "Meta/Reddit",
    "Military",
    "Movies",
    "Music",
    "Outdoors and Nature",
    "Place",
    "Podcasts and Streamers",
    "Politics",
    "Programming",
    "Reading,Writing,andLiterature",
    "Religion and Spirituality",
    "Science",
    "SexualOrientation",
    "Sports",
    "TabletopGames",
    "Technology",
    "Television",
    "TraumaSupport",
    "Travel",
    "Womens Health",
    "World News",
]


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
        ) as reddit:
            data = await reddit.subreddit(redditName)
            allRules = []
            async for rule in data.rules:
                tmp = rule.__dict__
                obj = {}
                obj["rule_title"] = tmp.get("short_name", "")
                obj["rule_desc"] = tmp.get("description", "")
                allRules.append(obj)

    return allRules


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


# Get Human Readable Date
def getDateHuman(unixtime):
    # Convert Unix timestamp to a datetime object
    dt = datetime.datetime.utcfromtimestamp(unixtime)

    # Get month as words using list indexing
    month_words = [
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December",
    ]
    month_num = dt.month - 1
    month = month_words[month_num]

    # Get day and year as words
    day = str(dt.day).capitalize()
    year = str(dt.year)

    # Print the result
    return f"{day} {month} {year}"


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
        ) as reddit:
            sredditMode = await reddit.subreddit(redditName)
            async for moderator in sredditMode.moderator:
                moderators.append(
                    [moderator.name, str(moderator.id).replace("t2_", "")]
                )
    return moderators


# Get all subreddit names based on the topics above
master = {}


async def getSubredditsByTopics(topic, rate_limit):
    async with rate_limit:
        print(f"Enterd {topic}")
        async with asyncpraw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent,
            username=config.get("username"),
            password=config.get("password"),
            ratelimit_seconds=300,
        ) as reddit:
            finalData = []
            TOTAl_SUBREDDITS_PER_TOPICS = int(config.get("TOTAl_SUBREDDITS_PER_TOPICS"))
            async for sreddit in reddit.subreddits.search(topic):
                if TOTAl_SUBREDDITS_PER_TOPICS == 0:
                    break
                obj = sreddit.__dict__
                if obj["subreddit_type"] == "private":
                    continue
                tmp = {}

                # Basic info
                tmp["id"] = obj.get("id", "")
                tmp["title"] = obj.get("display_name_prefixed", "")
                tmp["about"] = obj.get("public_description", "")
                tmp["logoUrl"] = obj.get("community_icon", "")
                tmp["bannerUrl"] = obj.get("banner_background_image", "")
                tmp["category"] = obj.get("category", "")

                # Rules,Flairs,Anchors
                tmp["rules"] = await getRules(obj.get("display_name", ""), rate_limit)
                tmp["flairs"] = await getFlairs(
                    f"{obj.get('display_name','')}", rate_limit
                )
                tmp["anchors"] = await getAnchors(
                    obj.get("display_name", ""), rate_limit
                )

                # Colors
                tmp["buttonColor"] = obj.get("key_color", "")
                tmp["headerColor"] = obj.get("primary_color", "")
                tmp["banner_background_color"] = obj.get(
                    "banner_background_color", "#33a8ff"
                )

                # Members,CreatedDate
                tmp["creationDate"] = obj.get("created_utc", "")
                if tmp["creationDate"]:
                    tmp["creationDateHuman"] = getDateHuman(int(tmp["creationDate"]))
                else:
                    tmp["creationDateHuman"] = 0

                tmp["members"] = obj.get("subscribers", "")
                if tmp["members"]:
                    tmp["membersHuman"] = numerize.numerize(int(tmp["members"]))
                else:
                    tmp["membersHuman"] = 0

                tmp["moderators"] = await getModeratorsNames(
                    obj.get("display_name", ""), rate_limit
                )

                # Spolier , NSFW
                tmp["over18"] = obj.get("over18", "")
                tmp["spoilers_enabled"] = obj.get("spoilers_enabled", "")

                finalData.append(tmp)
                TOTAl_SUBREDDITS_PER_TOPICS -= 1
                print(tmp)
                print(f"Done {obj.get('display_name','NA')}")
            master[topic] = finalData

    return "Done!"


async def main():
    tasks = []
    rate_limit = AsyncLimiter(int(config.get("HITS_SUB")), int(config.get("TIME_SUB")))
    topicsize = int(config.get("TOPIC_SIZE"))

    for topic in list(set(topics[:topicsize])):
        tasks.append(getSubredditsByTopics(topic, rate_limit))

    await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())
    master = dict(sorted(master.items()))
    with open("subreddits.json", "w") as fp:
        json.dump(master, fp, indent=4)
