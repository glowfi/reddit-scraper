import time

from helper.utils import danger, log_message
from post.utils.comments.handle_comments_extraction import handle_comment_extraction
from post.utils.comments.send_request_async_comments import send_request_comments_async
from post.utils.comments.send_request_sync_comments import sync_send_request_comments


# Get all comments for a post
async def getComments(url, topic, rate_limit, allUsers, seenUsers, trophies):
    async with rate_limit:
        print("url:", url)
        res_data = []
        try:

            # Try getting a the comment in one hit
            resData = await send_request_comments_async(url, rate_limit)

            # Handle Comment extraction
            return await handle_comment_extraction(
                resData, url, topic, allUsers, seenUsers, trophies
            )

        except Exception as e:

            # If name resoltion error
            if (
                str(e)
                == "Cannot connect to host reddit.com:443 ssl:default [Temporary failure in name resolution]"
            ):

                danger(f"Caught name resolution error ssl:default 443:  {e} ")

                log_message(
                    f"Url: {url} Message: SSL-Error Error : {str(e)}",
                    "comments-errs.txt",
                )

                # Sleep for a minute
                time.sleep(90)

                # Same logic from above
                resData = sync_send_request_comments(url)

                # Handle Comment extraction
                return await handle_comment_extraction(
                    resData, url, topic, allUsers, seenUsers, trophies
                )

            else:
                print("HERE: ...", len(res_data), url)
                danger(f"Error Occured:  {e} ")
                log_message(f"Url: {url} Error : {e}", "comments-errs.txt")
