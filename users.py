from typing import TypedDict
import random
import time
import uuid
import json
import datetime
from datetime import timedelta

import requests
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

from bs4 import BeautifulSoup


class Trophies(TypedDict):
    title: str
    description: str
    image_link: str


# Get New Session
def getSession() -> requests.Session:
    session = requests.session()
    retries = Retry(
        total=5,
        backoff_factor=2,  # Exponential backoff
        status_forcelist=[429, 500, 502, 503, 504, 443],
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("https://", adapter)
    return session


# Fetch trophies
def fetchTrophies() -> list[Trophies]:
    session = getSession()
    trophies: list[Trophies] = []

    while not trophies:
        print("Fetching trophies")
        try:
            url = "https://www.reddit.com/wiki/trophies/"
            html_content = session.get(url)
            soup = BeautifulSoup(html_content.text, "html5lib")

            tables = soup.find_all("table")
            for table in tables:
                for row in table.find_all("tr"):
                    # Extract image link
                    image_link = row.find("img")["src"] if row.find("img") else None
                    new_trophy: Trophies = {
                        "description": "",
                        "image_link": "",
                        "title": "",
                    }

                    if image_link:
                        new_trophy["image_link"] = f"https:{image_link}"
                        text = row.get_text().strip("\n")
                        title = text.split("\n")[0]
                        description = (
                            text.split("\n")[1]
                            if len(text.split("\n")) > 1
                            else text.split("\n")[0]
                        )
                        new_trophy["title"] = title
                        new_trophy["description"] = description

                        trophies.append(new_trophy)

        except Exception as e:
            print(e)

    return [json.loads(i) for i in list(set([json.dumps(i) for i in trophies]))]


class User(TypedDict):
    id: str
    name: str
    cake_day_utc: int
    cake_day_human: str
    age: str
    avatar_img: str
    banner_img: str
    public_description: str
    over18: bool
    keycolor: str
    primarycolor: str
    iconcolor: str
    suspended: bool
    trophies: list[Trophies]


# Generate random unix epoch
def generate_random_epoch():
    start_date = datetime.datetime(2005, 1, 10)
    end_date = datetime.datetime(2024, 2, 14)

    # Calculate the difference in seconds between the start and end dates
    diff_seconds = (end_date - start_date).total_seconds()

    # Generate a random number of seconds within the range
    random_seconds = random.uniform(0, diff_seconds)

    # Add the random number of seconds to the start date to get the random epoch time
    random_epoch = int((start_date + timedelta(seconds=random_seconds)).timestamp())

    return random_epoch


# Generate random hex color
def generate_random_hex_color():
    # Generate random RGB values
    r = random.randint(0, 255)
    g = random.randint(0, 255)
    b = random.randint(0, 255)

    # Convert to hexadecimal and make sure it's two digits long
    r_hex = hex(r).lstrip("0x").zfill(2)
    g_hex = hex(g).lstrip("0x").zfill(2)
    b_hex = hex(b).lstrip("0x").zfill(2)

    # Combine the RGB values into a single hex color string
    return "#" + r_hex + g_hex + b_hex


# Generate user primary and key color
def generate_colors():
    def generate_hex():
        return "#{:06x}".format(random.randint(0, 0xFFFFFF))

    primary_color = generate_hex()
    while True:
        key_color = generate_hex()
        if key_color != primary_color:
            break

    return primary_color, key_color


# Unix epoch to age [3yrs 6yrs 9yrs]
def epoch_age(epoch_time):
    # Convert the input to Unix epoch time if it's not already in that format
    if isinstance(epoch_time, str):
        epoch_time = int(float(epoch_time[1:]))

    current_time = int(time.time())
    age_in_seconds = current_time - epoch_time

    years = age_in_seconds // (365 * 24 * 60 * 60)

    return f"{years}yr(s)"


# Timestamp to date format
def getDate(timestamp):
    # Convert Unix epoch time to datetime object
    dt = datetime.datetime.fromtimestamp(timestamp)

    # Subtract 8 hours from the original timezone to get the local timezone
    dt = dt - timedelta(hours=8)

    # Format the date and time in desired format
    return dt.strftime("%d %B %Y")


# Generate user profile description
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


def generate_description():
    return random.choice(descriptions)


# Generate user profile pics alternate
def getProfilePics_alternate():
    return [f"https://robohash.org/{uuid.uuid4()}.png" for _ in range(1000)]


def generate_user_info(id: str, name: str, trophies: list[Trophies]) -> User:
    cake_day_utc = generate_random_epoch()
    primaryColor, keyColor = generate_colors()

    new_user: User = {
        "id": id,
        "name": name,
        "cake_day_utc": cake_day_utc,
        "cake_day_human": getDate(cake_day_utc),
        "age": epoch_age(cake_day_utc),
        "avatar_img": random.sample(getProfilePics_alternate(), 1)[0],
        "banner_img": "",
        "public_description": generate_description(),
        "over18": False,
        "keycolor": keyColor,
        "primarycolor": primaryColor,
        "iconcolor": generate_random_hex_color(),
        "suspended": False,
        "trophies": random.sample(trophies, random.randint(0, 3)),
    }
    return new_user
