import json
from dotenv import dotenv_values
import uuid
import time
from datetime import timedelta
from datetime import datetime
import asyncpraw
from aiolimiter import AsyncLimiter
import asyncio
import random
import logging
import requests
from bs4 import BeautifulSoup

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


def generate_description():
    descriptions = [
        "A witty individual with a contagious laugh.",
        "A thoughtful conversationalist who always listens intently.",
        "A creative soul with a passion for innovation.",
        "A natural leader who inspires those around them.",
        "A curious mind who loves to learn new things.",
        "A free spirit who embraces life with open arms.",
        "A kind-hearted person who puts others first.",
        "A fearless adventurer who seeks out new experiences.",
        "A deep thinker who ponders the mysteries of the universe.",
        "A charismatic personality who lights up any room.",
        "A hardworking professional who strives for excellence.",
        "A loyal friend who stands by their loved ones.",
        "A talented artist who sees the world through a unique lens.",
        "A patient listener who offers wise counsel.",
        "A generous giver who goes above and beyond for others.",
        "A humble servant who works tirelessly behind the scenes.",
        "A resilient survivor who overcomes adversity with grace.",
        "A playful jokester who brings laughter to every gathering.",
        "A calm presence who radiates peace and serenity.",
        "A brilliant strategist who thinks several steps ahead.",
        "A compassionate caregiver who nurtures those in need.",
        "A meticulous organizer who keeps everything running smoothly.",
        "A visionary dreamer who imagines a better future.",
        "A quick learner who adapts to new situations with ease.",
        "A gracious host who makes everyone feel welcome.",
        "A persistent problem-solver who never gives up.",
        "A brave warrior who fights for justice and equality.",
        "A gentle soul who cherishes every moment.",
        "A passionate advocate who speaks up for what they believe in.",
        "A lifelong student who is always eage",
        "A creative force, brimming with ideas and inspiration. Loves to experiment with different mediums and styles, pushing boundaries and challenging expectations.",
        "A dedicated problem-solver, with a knack for finding innovative solutions to complex challenges. Prefers to work collaboratively, valuing teamwork and open communication.",
        "A compassionate listener, empathetic and understanding. Strives to create a safe and supportive space for others to share their thoughts and feelings.",
    ]
    return random.choice(descriptions)


def generate_colors():
    def generate_hex():
        return "#{:06x}".format(random.randint(0, 0xFFFFFF))

    primary_color = generate_hex()
    while True:
        key_color = generate_hex()
        if key_color != primary_color:
            break

    return primary_color, key_color


def getProfilePics():
    url = "https://www.reddit.com/user/timawesomeness/comments/813jpq/default_reddit_profile_pictures/"
    headers = {
        "User-Agent": f"{getUserAgent()}",
    }

    response = requests.get(url=url, headers=headers)
    html_content = response.content
    soup = BeautifulSoup(html_content.decode("utf-8"), "html5lib")

    master = []
    tables = soup.find_all("table")
    for table in tables:
        for body in table.find_all("tbody"):
            for tr in body.find_all("tr"):
                image_links = tr.find_all("a")
                if image_links:
                    text = tr.get_text().lstrip().rstrip().split(" ")[0].strip("\n")
                    tmp = []
                    for link in image_links:
                        tmp.append(link["href"])
                    master.append({"hex": text, "data": tmp})
    return master


def generate_random_epoch():
    start_date = datetime(2005, 1, 10)
    end_date = datetime(2024, 2, 14)

    # Calculate the difference in seconds between the start and end dates
    diff_seconds = (end_date - start_date).total_seconds()

    # Generate a random number of seconds within the range
    random_seconds = random.uniform(0, diff_seconds)

    # Add the random number of seconds to the start date to get the random epoch time
    random_epoch = int((start_date + timedelta(seconds=random_seconds)).timestamp())

    return random_epoch


async def getRedditorInfoAlternate(redditor_name, aid, userInfo, profilePics):
    val = generate_random_epoch()
    age = epoch_age(val)
    date = getDate(val)
    primary, key = generate_colors()

    randomize_profile_pic = random.sample(profilePics, 1)[0]
    hexColor = f'#{randomize_profile_pic["hex"]}'
    dat = randomize_profile_pic["data"]
    avatar_img = random.sample(dat, 1)[0]

    print(hexColor)
    print(avatar_img)

    userInfo[aid]["cakeDay"] = val
    userInfo[aid]["cakeDayHuman"] = date
    userInfo[aid]["age"] = age
    userInfo[aid]["avatar_img"] = avatar_img
    userInfo[aid]["banner_img"] = ""
    userInfo[aid]["publicDescription"] = generate_description()
    userInfo[aid]["over18"] = False
    userInfo[aid]["keycolor"] = key
    userInfo[aid]["primarycolor"] = primary
    userInfo[aid]["iconcolor"] = hexColor
    userInfo[aid]["supended"] = False
    total_users[0] -= 1
    print("\x1b[6;30;42m" + f"More {total_users} left ..." + "\x1b[0m")


async def getRedditorInfo(redditor_name, aid, userInfo, rate_limit):
    async with rate_limit:
        async with asyncpraw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=getUserAgent(),
            username=config.get("username"),
            password=config.get("password"),
            ratelimit_seconds=300,
            timeout=32,
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
                        print(
                            "\x1b[6;30;42m" + f"More {total_users} left ..." + "\x1b[0m"
                        )

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


async def main(profilePics):
    tasks = []
    rate_limit = AsyncLimiter(HIT_USERS, TIME_USERS)
    for user in userData:
        redditor_name = userData.get(user, {}).get("username", "")
        id = userData.get(user, {}).get("id", "")
        if redditor_name and id:
            # tasks.append(getRedditorInfo(redditor_name, id, userData, rate_limit))
            tasks.append(
                getRedditorInfoAlternate(redditor_name, id, userData, profilePics)
            )

    await asyncio.gather(*tasks)


if __name__ == "__main__":
    profilePics = getProfilePics()
    asyncio.run(main(profilePics))
    with open("./users.json", "w") as f:
        json.dump(userData, f, indent=4)
