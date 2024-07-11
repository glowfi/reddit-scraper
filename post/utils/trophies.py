import aiohttp
from bs4 import BeautifulSoup
from helper.utils import getUserAgent
import json, asyncio


# Get trophies
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
            "image_link": "https://a.thumbs.redditmedia.com/GnIq6cHQCTUioRxU4opnYO0PJibxEBb_K3cyln1tXJ0.png",
            "title": "Bellwether",
            "description": "Hang out on the new queue and flag carefully",
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
                description = (
                    text.split("\n")[1]
                    if len(text.split("\n")) > 1
                    else text.split("\n")[0]
                )
                tmp["title"] = title
                tmp["description"] = description
                master.append(tmp)
    return [json.loads(i) for i in list(set([json.dumps(i) for i in master]))]


async def get_res():
    with open("./trophies.json", "w") as fp:
        json.dump(await getTrophies(), fp)


asyncio.run(get_res())
