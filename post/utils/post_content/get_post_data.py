import asyncpraw
import random

from dotenv import dotenv_values

from helper.utils import getUserAgent, sanitize_url, success, unix_to_relative_time
from post.utils.comments.get_all_comments_for_a_post import getComments
from post.utils.post_content.get_post_media_content import post_content


# Load DOTENV
config = dotenv_values(".env")

# Credentials
client_id = config.get("client_id")
client_secret = config.get("client_secret")
user_agent = getUserAgent()


# Get post content
async def get_post_data_subreddit(
    topic,
    currSubreddit,
    rate_limit,
    allUsers,
    seenUsers,
    trophies,
    awards,
    finalPostsData,
    DONE,
    POSTS_PER_SUBREDDIT,
    TOTAL_REQUIRED_POSTS,
):
    async with rate_limit:
        subredditName = currSubreddit["title"].replace("r/", "")
        async with asyncpraw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=getUserAgent(),
            username=config.get("username"),
            password=config.get("password"),
            ratelimit_seconds=300,
            timeout=32,
        ) as reddit:
            subreddit = await reddit.subreddit(subredditName)

            postCounter = 0
            async for posts in subreddit.hot(limit=None):
                obj = posts.__dict__

                try:
                    submission = await reddit.submission(id=obj["id"])
                    print(submission.title)
                    data = vars(submission)

                    author = data.get("author", "")
                    if not author:
                        continue

                    postBody = data["selftext"]
                    postHTML = data["selftext_html"]
                    if postHTML:
                        postHTML = postHTML.replace("&lt;", "<").replace("&gt;", ">")

                    dat = post_content(data, submission)

                    post_data = {}

                    if dat == "Invalid":
                        continue

                    # Link type post
                    if not postBody and not postHTML:
                        author = data.get("author", "")
                        if author:
                            author = author.name

                        post_data = {
                            "id": data.get("id", ""),
                            "subreddit": data.get("subreddit", "").display_name,
                            "subreddit_id": data.get("subreddit_id", "").replace(
                                "t5_", ""
                            ),
                            "author": author,
                            "author_id": data.get("author_fullname", "").replace(
                                "t2_", ""
                            ),
                            "title": data.get("title", ""),
                            "postflair": data.get("link_flair_text", ""),
                            "postflaircolor": data.get(
                                "link_flair_background_color", ""
                            ),
                            "num_comments": data.get("num_comments", ""),
                            "ups": data.get("ups", ""),
                            "awards": random.choices(awards, k=random.randint(0, 4)),
                            "comments": await getComments(
                                sanitize_url(
                                    f"https://reddit.com{obj.get('permalink','')}"
                                )
                                + ".json",
                                topic,
                                rate_limit,
                                allUsers,
                                seenUsers,
                                trophies,
                            ),
                            "media_metadata": dat,
                            "createdat": data["created_utc"],
                            "createdatHuman": unix_to_relative_time(
                                data["created_utc"]
                            ),
                            "text": data["url"],
                            "text_html": "",
                            "over_18": data.get("over_18", ""),
                            "spoiler": data.get("spoiler", ""),
                            "link_type": True,
                            "category": topic,
                        }

                    elif dat["type"] in (
                        "video",
                        "gif",
                        "image",
                        "multi",
                        "gallery",
                        "text",
                    ):
                        author = data.get("author", "")
                        if author:
                            author = author.name
                        post_data = {
                            "id": data.get("id", ""),
                            "subreddit": data.get("subreddit", "").display_name,
                            "subreddit_id": data.get("subreddit_id", "").replace(
                                "t5_", ""
                            ),
                            "author": author,
                            "author_id": data.get("author_fullname", "").replace(
                                "t2_", ""
                            ),
                            "title": data.get("title", ""),
                            "postflair": data.get("link_flair_text", ""),
                            "postflaircolor": data.get(
                                "link_flair_background_color", ""
                            ),
                            "num_comments": data.get("num_comments", ""),
                            "ups": data.get("ups", ""),
                            "awards": random.choices(awards, k=random.randint(0, 4)),
                            "comments": await getComments(
                                sanitize_url(
                                    f"https://reddit.com{obj.get('permalink','')}"
                                )
                                + ".json",
                                topic,
                                rate_limit,
                                allUsers,
                                seenUsers,
                                trophies,
                            ),
                            "media_content": dat,
                            "createdat": data["created_utc"],
                            "createdatHuman": unix_to_relative_time(
                                data["created_utc"]
                            ),
                            "text": postBody,
                            "text_html": postHTML,
                            "over_18": data.get("over_18", ""),
                            "spoiler": data.get("spoiler", ""),
                            "link_type": False,
                            "category": topic,
                        }

                    if post_data:
                        finalPostsData.append(dict(sorted(post_data.items())))

                        postCounter += 1
                        success(
                            f"POST COUNTER .................... {topic} {postCounter}"
                        )

                        DONE[0] += 1
                        success(f"TOTAL POSTS FETCHED ............  {DONE[0]}")
                        if (
                            postCounter == POSTS_PER_SUBREDDIT
                            or DONE[0] >= TOTAL_REQUIRED_POSTS
                        ):
                            break

                except Exception as e:
                    with open("noposts.txt", "a+") as f:
                        _url = f'https://reddit.com/r/{str(data.get("subreddit", "").display_name)}/{str(data.get("id", ""))}/{str(submission.title)}'
                        f.write(f"{str(e)}  {str(id)} {_url} \n")
