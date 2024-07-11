import aiohttp
from bs4 import BeautifulSoup
from helper.utils import getUserAgent
import json, asyncio


# get awards
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


async def get_res():
    with open("./awards.json", "w") as fp:
        json.dump(await getAwards(), fp)


asyncio.run(get_res())
