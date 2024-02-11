#!/bin/python3

import json
import praw
import requests
from numerize import numerize
import datetime
from dotenv import dotenv_values
import string
import random


# Custom User agent string
def getUserAgent():
    letters = string.ascii_lowercase
    length = 10
    return "".join(random.choice(letters) for _ in range(length))


# Load DOTENV
config = dotenv_values(".env")


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


# Praw object
reddit = praw.Reddit(
    client_id=client_id,
    client_secret=client_secret,
    user_agent=getUserAgent(),
    username=config.get("username"),
    password=config.get("password"),
)


# Topics
topics = [
    "Activism",
    "AddictionSupport",
    "AnimalsandPets",
    "Art",
    "BeautyandMakeup",
    "Business,Economics,andFinance",
    "Careers",
    "CarsandMotorVehicles",
    "Celebrity",
    "CraftsandDIY",
    "Crypto",
    "Culture,Race,andEthnicity",
    "EthicsandPhilosophy",
    "FamilyandRelationships",
    "Fashion",
    "FitnessandNutrition",
    "FoodandDrink",
    "Funny/Humor",
    "Gaming",
    "Gender",
    "History",
    "Hobbies",
    "HomeandGarden",
    "InternetCultureandMemes",
    "Law",
    "LearningandEducation",
    "MarketplaceandDeals",
    "MatureThemesandAdultContent",
    "MedicalandMentalHealth",
    "Men'sHealth",
    "Meta/Reddit",
    "Military",
    "Movies",
    "Music",
    "OutdoorsandNature",
    "Place",
    "PodcastsandStreamers",
    "Politics",
    "Programming",
    "Reading,Writing,andLiterature",
    "ReligionandSpirituality",
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
def getRules(redditName):
    data = reddit.subreddit(redditName).rules
    allRules = []
    for rule in data:
        tmp = rule.__dict__
        obj = {}
        obj["rule_title"] = tmp.get("short_name", "")
        obj["rule_desc"] = tmp.get("description", "")
        allRules.append(obj)

    return allRules


# Get Flairs
def getFlairs(redditName):
    # Credentials

    # Get Token
    auth = requests.auth.HTTPBasicAuth(
        client_id,
        client_secret,
    )
    data = {
        "grant_type": "password",
        "username": config.get("username"),
        "password": config.get("password"),
    }
    headers = {"User-Agent": "MyAPI"}
    res = requests.post(
        "https://www.reddit.com/api/v1/access_token",
        auth=auth,
        headers=headers,
        data=data,
    )
    token = res.json()["access_token"]
    headers["Authorization"] = f"bearer {token}"

    # Get Flair
    allFlairs = []
    try:
        res = requests.get(
            f"https://oauth.reddit.com/r/{redditName}/api/link_flair_v2",
            headers=headers,
        ).json()
        for flairs in res:
            allFlairs.append(
                {"text": flairs["text"], "color": flairs["background_color"]}
            )
    except Exception as e:
        print("Exception Handled!", e)

    return allFlairs


# Get Anchors
def getAnchors(subredditName):
    topbar = reddit.subreddit(subredditName).widgets.topbar
    anchorTags = {}
    if len(topbar) > 0:
        probably_menu = topbar[0]
        assert isinstance(probably_menu, praw.models.Menu)
        for item in probably_menu:
            if isinstance(item, praw.models.Submenu):
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
def getModeratorsNames(redditName):
    moderators = []
    for moderator in reddit.subreddit(redditName).moderator():
        moderators.append([moderator.name, str(moderator.id).replace("t2_", "")])
    return moderators


# Subreddit schema
"""Subreddit
id id
title title
about public_description
logoUrl community_icon
bannerUrl banner_background_image
category category
rules
flairs
anchors
buttonColor key_color
headerColor primary_color
bannerbackgroundColor banner_background_color
moderators
creationDate created_utc
members subscribers
spoilers_enabled spoilers_enabled
over18 over18
online
bySize
"""


# Get all subreddit names based on the topics above
master = {}
topicsize = int(config.get("TOPIC_SIZE"))

for topic in list(set(topics[:topicsize])):
    subreddit = reddit.subreddits.search(topic)
    finalData = []
    TOTAl_SUBREDDITS_PER_TOPICS = int(config.get("TOTAl_SUBREDDITS_PER_TOPICS"))
    for sreddit in subreddit:
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
        tmp["rules"] = getRules(obj.get("display_name", ""))
        tmp["flairs"] = getFlairs(f"{obj.get('display_name','')}")
        tmp["anchors"] = getAnchors(obj.get("display_name", ""))

        # Colors
        tmp["buttonColor"] = obj.get("key_color", "")
        tmp["headerColor"] = obj.get("primary_color", "")
        tmp["banner_background_color"] = obj.get("banner_background_color", "#33a8ff")

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

        tmp["moderators"] = getModeratorsNames(obj.get("display_name", ""))

        # Spolier , NSFW
        tmp["over18"] = obj.get("over18", "")
        tmp["spoilers_enabled"] = obj.get("spoilers_enabled", "")

        finalData.append(tmp)
        TOTAl_SUBREDDITS_PER_TOPICS -= 1
        print(tmp)
        print(f"Done {obj.get('display_name','NA')}")
    master[topic] = finalData

with open("subreddits_sync.json", "w") as fp:
    json.dump(master, fp, indent=4)
