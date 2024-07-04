import json
import time

from helper.utils import log_message
from post.utils.comments.send_request_sync_comments import sync_send_request_comments


# Keep retrying until we get the comments details
def keep_retrying(resData, url):
    MAX_RETRIES = 30
    NO_TRIES = MAX_RETRIES

    while NO_TRIES:
        if "kind" in resData:
            resData = json.loads(resData)
            if isinstance(resData, list) and len(resData) > 0 and "kind" in resData[0]:
                print(
                    "\x1b[6;30;42m"
                    + f"Got Back data in {abs(MAX_RETRIES-NO_TRIES)+1} tries !"
                    + "\x1b[0m"
                )
                log_message(f"Got {url}", "comments-got.txt")
                break
        else:
            print(
                "\033[41m" + f"Retrying {abs(MAX_RETRIES-NO_TRIES)+1} ...." + "\033[0m"
            )
            log_message(f"Retrying {url}", "comments-retry.txt")

            time.sleep(5)
            resData = sync_send_request_comments(url)

        NO_TRIES -= 1

    return NO_TRIES, resData
