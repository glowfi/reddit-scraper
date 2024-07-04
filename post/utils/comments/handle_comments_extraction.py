import asyncpraw
from dotenv import dotenv_values

from helper.utils import getUserAgent, log_message
from post.utils.comments.alternate_extract_deep_nested_comments import (
    alternateextractDeepnestedComments,
)
from post.utils.comments.extract_deep_nested_comments import extractDeepnestedComments
from post.utils.comments.keepretryingcomments import keep_retrying

from post.utils.get_author_details import get_author_details


# Load DOTENV
config = dotenv_values(".env")

# Credentials
client_id = config.get("client_id")
client_secret = config.get("client_secret")
user_agent = getUserAgent()


async def handle_comment_extraction(resData, url, topic, allUsers, seenUsers, trophies):
    # Check if we can get the comment in only just 1 hit
    ans = keep_retrying(resData, url)
    NO_TRIES = ans[0]
    resData = ans[1]

    # If out of tries return blank comments list
    if NO_TRIES == 0:
        log_message(
            f"Url: {url} Error : Bad Error Using alternate", "comments-errs.txt"
        )
        async with asyncpraw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=getUserAgent(),
            username=config.get("username"),
            password=config.get("password"),
            ratelimit_seconds=300,
        ) as reddit:
            postID = str(url.split("/")[6])
            submission = await reddit.submission(postID)
            comments = await submission.comments()
            await comments.replace_more(limit=None)
            comment_queue = comments[:]
            log_message(f"Got {url}", "comments-got.txt")
            return await alternateextractDeepnestedComments(
                comment_queue, "isParent", topic, allUsers, seenUsers, trophies
            )

    # Extract deeplynested comments
    else:
        res_data = get_author_details(resData, allUsers, seenUsers, trophies)
        allComments = await extractDeepnestedComments(
            res_data, "isParent", topic, allUsers, seenUsers, trophies
        )
        return allComments
