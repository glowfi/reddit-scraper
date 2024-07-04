import random
import uuid

from bs4 import BeautifulSoup
import requests
from helper.utils import getUserAgent
from user.constants import descriptions


# Generate user profile description
def generate_description():
    return random.choice(descriptions)


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


# Generate user profile pic
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


# Generate user profile pics alternate
def getProfilePics_alternate():
    return [f"https://robohash.org/{uuid.uuid4()}.png" for _ in range(1000)]
