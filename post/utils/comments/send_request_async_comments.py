import aiohttp
import copy
from helper.utils import headers, getUserAgent


# Get comments for this post asynchronously
async def send_request_comments_async(url, rate_limit):
    async with rate_limit:
        async with aiohttp.ClientSession() as session:
            my_headers = copy.deepcopy(headers)
            my_headers["User-Agent"] = f"{getUserAgent()}"
            async with session.get(
                url=url,
                headers=my_headers,
            ) as response:
                return await response.text()
