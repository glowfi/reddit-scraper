import requests
import copy
from helper.utils import headers, getUserAgent


# Sync request for getting comment details
def sync_send_request_comments(url):
    my_headers = copy.deepcopy(headers)
    my_headers["User-Agent"] = f"{getUserAgent()}"
    resData = requests.get(url, headers=my_headers).text
    return resData
