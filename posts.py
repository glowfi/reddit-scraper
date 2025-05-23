import sys
import traceback
import logging
import random
import uuid
import json
import datetime
from collections import defaultdict
from typing import Any, TypedDict

import requests
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from requests.models import HTTPError
import urllib.parse
from urllib.parse import parse_qs
import html

import ua_generator
from ua_generator.user_agent import UserAgent
from colorama import Fore, Style
from bs4 import BeautifulSoup
from dotenv import dotenv_values

from subreddits import Subreddit
from users import User, generate_user_info, Trophies, fetchTrophies


class AccessTokenResponse(TypedDict):
    access_token: str
    token_type: str
    expires_in: int
    scope: str


class Awards(TypedDict):
    title: str
    image_link: str


class Comment(TypedDict):
    author: str
    author_fullname: str
    author_flair_text: str
    body: str
    body_html: str
    ups: int
    score: int
    created_utc: int
    replies: list["Comment"]


class ImageMultiResolution(TypedDict):
    x: int
    y: int
    u: str


class ImageResolution(TypedDict):
    height: int
    width: int
    url: str


class Image(TypedDict):
    id: str
    resolutions: list[ImageResolution | ImageMultiResolution]
    _type: str


class Gif(TypedDict):
    id: str
    resolutions: list[ImageResolution | ImageMultiResolution]
    _type: str


class Video(TypedDict):
    id: str
    fallback_url: str
    hls_url: str
    dash_url: str
    scrubber_media_url: str
    height: int
    width: int
    _type: str


class VideoMulti(TypedDict):
    id: str
    hlsUrl: str
    dashUrl: str
    x: int
    y: int
    _type: str


class GalleryImageResolutions(TypedDict):
    id: str
    x: int
    y: int
    u: str


class Gallery(TypedDict):
    id: str
    images: list[list[GalleryImageResolutions]]
    _type: str


class Link(TypedDict):
    id: str
    link: str
    _type: str
    image: Image


class Media_Content(TypedDict, total=False):
    _type: str
    content: (
        Image
        | Gif
        | Video
        | Gallery
        | Link
        | list[Image | Gif | Video | VideoMulti | Gallery | Link]
    )


class Post(TypedDict):
    id: str
    subreddit: str
    subreddit_id: str
    title: str
    author: str
    author_fullname: str
    author_flair_text: str  # maps to full_text in subreddit
    link_flair_text: str  # maps to full_text in subreddit
    num_comments: int
    ups: str
    awards: list[Awards]
    comments: list[Comment]
    media_content: Media_Content
    created_utc: int
    created_human: str
    text: str
    text_html: str
    over_18: bool
    spoiler: bool


class ResultState(TypedDict):
    status_code: int
    success: bool
    error: str


class PostResult(TypedDict):
    subreddit: str
    posts: Any | None
    result_state: ResultState


class PostArticleResult(TypedDict):
    subreddit: str
    post: Any | None
    result_state: ResultState


class UserDetail(TypedDict):
    id: str
    name: str
    subreddit: str
    subreddit_id: str


class OnDemandSubreddit(TypedDict):
    title: str
    topic: str
    posts_count: int


# Set up logging
logging.basicConfig(
    filename="scraper.log",
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

# Load DOTENV
config = dotenv_values(".env")

# Credentials
client_id = config.get("client_id")
client_secret = config.get("client_secret")
username = config.get("username")
password = config.get("password")
POSTS_PER_SUBREDDIT = config.get("POSTS_PER_SUBREDDIT")
POSTS_SORT_FILTER = config.get("POSTS_SORT_FILTER")  # hot,new,top,rising,controversial

if not client_id or not client_secret or not username or not password:
    raise Exception("please give credentials in .env file")

if not POSTS_SORT_FILTER or not POSTS_PER_SUBREDDIT:
    raise Exception(
        "please give posts sort filter and posts per subreddit in .env file"
    )
POSTS_PER_SUBREDDIT = int(POSTS_PER_SUBREDDIT)


# Get Human Readable Date [Unix epoch to human readable data]
def unix_epoch_to_human_readable(unixtime):
    dt = datetime.datetime.fromtimestamp(unixtime)

    # Get month as words using list indexing
    month_words = [
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December",
    ]
    month_num = dt.month - 1
    month = month_words[month_num]

    # Get day and year as words
    day = str(dt.day).capitalize()
    year = str(dt.year)

    # Print the result
    return f"{day} {month} {year}"


# Get random user agent
def getUserAgent() -> UserAgent:
    return ua_generator.generate(
        device=("desktop", "mobile"),
        platform=("windows", "macos", "ios", "linux", "android"),
        browser=("chrome", "edge", "firefox", "safari"),
    )


# Get headers from user agent
def getHeaders(ua: UserAgent, token: str) -> dict[str, str]:
    if not token:
        return ua.headers.get()
    return {
        **ua.headers.get(),
        "Authorization": f"bearer {token}",
    }


# Get New Session
def getSession() -> requests.Session:
    session = requests.session()
    retries = Retry(
        total=5,
        # total=1,
        backoff_factor=2,  # Exponential backoff
        status_forcelist=[429, 500, 502, 503, 504, 443],
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("https://", adapter)
    return session


# Get Oauth token
def getToken(params: dict[str, str], timeout: int) -> str:
    if not client_id or not client_secret or not username or not password:
        return ""
    session = getSession()
    session.auth = (client_id, client_secret)
    resp: AccessTokenResponse = session.post(
        "https://www.reddit.com/api/v1/access_token",
        data=params,
        headers=getHeaders(getUserAgent(), ""),
        timeout=timeout,
    ).json()
    return resp["access_token"]


def fetchAwards() -> list[Awards]:
    session = getSession()

    try:
        url = "https://asyncpraw.readthedocs.io/en/latest/code_overview/models/submission.html#asyncpraw.models.Submission"
        html_content = session.get(url)
        soup = BeautifulSoup(html_content.text, "html5lib")

        result: list[Awards] = []
        tables = soup.find_all("table")
        for table in tables:
            for row in table.find_all("tr"):
                # Extract image link
                image_link = row.find("img")["src"] if row.find("img") else None
                if image_link:
                    new_award: Awards = {
                        "title": f"{row.find('p').text}",
                        "image_link": f"{image_link}",
                    }
                    result.append(new_award)
        return result

    except Exception as e:
        print(e)
        return []


def fetchPostsBySubreddt(
    filter: str, limit: int, subreddit: str, token: str
) -> PostResult:
    # hot,new,top,rising,controversial
    session = getSession()

    try:
        if token:
            response = session.get(
                f"https://oauth.reddit.com/{subreddit}/{filter}.json",
                headers=getHeaders(getUserAgent(), token),
                params={"limit": limit, "show": "all", "sr_detail": True},
            )
        else:
            response = session.get(
                f"https://www.reddit.com/{subreddit}/{filter}.json",
                headers=getHeaders(getUserAgent(), token),
                params={"limit": limit, "show": "all", "sr_detail": True},
            )
        response.raise_for_status()

        response_json = response.json()
        print(
            f"{Fore.GREEN}Success got posts Status Code:{response.status_code} Subreddit Name:{subreddit}{Style.RESET_ALL}"
        )
        logging.info(
            f"Success got posts Status Code:{response.status_code} Subreddit Name:{subreddit}"
        )
        return {
            "subreddit": subreddit,
            "posts": response_json,
            "result_state": {
                "error": "",
                "success": True,
                "status_code": response.status_code,
            },
        }
    except Exception as err:
        code = -1
        if type(err) is HTTPError:
            code = err.response.status_code
        print(
            f"{Fore.RED}Fail to get posts Status Code:{code} Subreddit name:{subreddit}{Style.RESET_ALL} Error :{err}"
        )
        logging.error(
            f"Fail to get posts Status Code:{code} Subreddit name:{subreddit} Error :{err}"
        )
        return {
            "subreddit": subreddit,
            "posts": None,
            "result_state": {
                "error": str(err),
                "success": False,
                "status_code": code,
            },
        }


def fetchPostArticleByPostID(
    subreddit: str, postID: str, token: str
) -> PostArticleResult:
    # hot,new,top,rising,controversial
    session = getSession()

    try:
        if token:
            response = session.get(
                f"https://oauth.reddit.com/{subreddit}/comments/{postID}.json",
                headers=getHeaders(getUserAgent(), token),
                params={
                    "showmore": True,
                    "showmedia": True,
                    "showtitle": True,
                    "sr_detail": True,
                },
            )
        else:
            response = session.get(
                f"https://www.reddit.com/{subreddit}/comments/{postID}.json",
                headers=getHeaders(getUserAgent(), token),
                params={
                    "showmore": True,
                    "showmedia": True,
                    "showtitle": True,
                    "sr_detail": True,
                },
            )
        response.raise_for_status()

        response_json = response.json()
        print(
            f"{Fore.GREEN}Success got post by id Status Code:{response.status_code} Subreddit Name:{subreddit}{Style.RESET_ALL}"
        )
        logging.info(
            f"Success got post by id Status Code:{response.status_code} Subreddit Name:{subreddit}"
        )
        return {
            "subreddit": subreddit,
            "post": response_json,
            "result_state": {
                "error": "",
                "success": True,
                "status_code": response.status_code,
            },
        }
    except Exception as err:
        code = -1
        if type(err) is HTTPError:
            code = err.response.status_code
        print(
            f"{Fore.RED}Fail to get post by id Status Code:{code} Subreddit name:{subreddit}{Style.RESET_ALL} Error :{err}"
        )
        logging.error(
            f"Fail to get post by id Status Code:{code} Subreddit name:{subreddit} Error :{err}"
        )
        return {
            "subreddit": subreddit,
            "post": None,
            "result_state": {
                "error": str(err),
                "success": False,
                "status_code": code,
            },
        }


# Sanitize and encode reddit media URL
def handleURL(encodedURL: str):
    if not encodedURL:
        return ""
    if encodedURL.find("https://www.reddit.com/media") != -1:
        data = parse_qs(encodedURL)
        return [data[item] for item in data][0][0]

    else:
        return urllib.parse.unquote(html.unescape(encodedURL))


def buildComments(
    comments_raw_json: Any,
    users: dict[str, set[str]],
    subreddit_id: str,
    subreddit: str,
) -> tuple[list[Comment], int]:
    extracted_comments: list[Comment] = []
    num_comments = 0
    for comment in comments_raw_json:
        if isinstance(comment, dict) and comment.get("kind", "") == "t1":
            comment_data = comment.get("data", {})
            author = comment_data.get("author", "")
            author_fullname = comment_data.get("author_fullname", "").replace("t2_", "")
            if author == "[deleted]":
                continue
            extracted_comment: Comment = {
                "author": author,
                "author_fullname": author_fullname,
                "author_flair_text": comment_data.get("author_flair_text", ""),
                "body": comment_data.get("body", ""),
                "body_html": comment_data.get("body_html", ""),
                "ups": comment_data.get("ups", 0),
                "score": comment_data.get("score", 0),
                "created_utc": comment_data.get("created_utc", 0),
                "replies": [],
            }
            if author and author_fullname:
                users[subreddit_id].add(
                    json.dumps(
                        {
                            "id": author_fullname,
                            "name": author,
                            "subreddit_id": subreddit_id,
                            "subreddit": subreddit,
                        }
                    )
                )

            replies = comment_data.get("replies", {})
            num_comments += 1
            if isinstance(replies, dict):
                replies, _num_comments = buildComments(
                    replies.get("data", {}).get("children", []),
                    users,
                    subreddit_id,
                    subreddit,
                )
                extracted_comment["replies"] = replies
                num_comments += _num_comments
            extracted_comments.append(extracted_comment)
    return (extracted_comments, num_comments)


def buildMedia(post_detail: Any) -> Media_Content:
    base_url: str = "https://www.reddit.com"
    permalink: str = base_url + post_detail.get("permalink", "").rstrip("/")
    url: str = post_detail.get("url", "").rstrip("/")
    url_overridden_by_dest: str = post_detail.get("url_overridden_by_dest", "").rstrip(
        "/"
    )

    # Link
    if (
        permalink != url
        and url_overridden_by_dest == url
        and "https://i.redd.it" not in post_detail.get("url", "")
        and not post_detail.get("secure_media", {})
        and not post_detail.get("media_metadata", {})
        and not post_detail.get("is_gallery", False)
    ):
        link_image_content: Image = {
            "id": str(uuid.uuid4()),
            "resolutions": [],
            "_type": "image",
        }
        new_link: Link = {
            "id": str(uuid.uuid4()),
            "link": post_detail.get("url", ""),
            "_type": "link",
            "image": link_image_content,
        }
        if (
            post_detail.get("preview", {}).get("images")
            and isinstance(post_detail.get("preview", {}).get("images"), list)
            and len(post_detail.get("preview", {}).get("images", [])) > 0
        ):
            images = (
                post_detail.get("preview", {}).get("images")[0].get("resolutions", [])
            )
            images = sorted(images, key=lambda x: x["height"])
            sourceImage = (
                post_detail.get("preview", {}).get("images")[0].get("source", {})
            )
            for image in images:
                if image.get("url", ""):
                    new_image_resolution: ImageResolution = {
                        "height": image.get("height", 0),
                        "width": image.get("width", 0),
                        "url": handleURL(image["url"]),
                    }
                    link_image_content.get("resolutions", []).append(
                        new_image_resolution
                    )
            if sourceImage and sourceImage.get("url", ""):
                link_image_content.get("resolutions", []).append(
                    {
                        "height": sourceImage.get("height", 0),
                        "width": sourceImage.get("width", 0),
                        "url": handleURL(sourceImage["url"]),
                    }
                )
            if len(link_image_content.get("resolutions", [])) > 0:
                new_link["image"] = link_image_content
        return {
            "_type": "link",
            "content": new_link,
        }

    # Multi
    if post_detail.get("media_metadata", {}) and not post_detail.get(
        "is_gallery", False
    ):
        media_type_count = set()
        for media_content_id in post_detail.get("media_metadata", {}):
            media_type_count.add(
                post_detail.get("media_metadata", {})
                .get(media_content_id, {})
                .get("e", "")
            )
        if len(media_type_count) >= 2:
            media_contents: list[Image | Gif | Video | VideoMulti | Gallery | Link] = []
            for media_content_id in post_detail.get("media_metadata", {}):
                mediaType = (
                    post_detail.get("media_metadata", {})
                    .get(media_content_id, {})
                    .get("e", "")
                )
                # Image
                if mediaType == "Image":
                    new_image: Image = {
                        "id": str(uuid.uuid4()),
                        "resolutions": [],
                        "_type": "image",
                    }
                    for image in (
                        post_detail.get("media_metadata", {})
                        .get(media_content_id, {})
                        .get("p", [])
                    ):
                        new_image.get("resolutions", []).append(
                            {
                                "x": image.get("x", 0),
                                "y": image.get("y", 0),
                                "u": handleURL(image.get("u", "")),
                            }
                        )
                    if (
                        post_detail.get("media_metadata", {})
                        .get(media_content_id, {})
                        .get("s", [])
                    ):
                        new_image.get("resolutions", []).append(
                            {
                                "x": post_detail.get("media_metadata", {})
                                .get(media_content_id, {})
                                .get("s", {})
                                .get("x", 0),
                                "y": post_detail.get("media_metadata", {})
                                .get(media_content_id, {})
                                .get("s", {})
                                .get("y", 0),
                                "u": handleURL(
                                    post_detail.get("media_metadata", {})
                                    .get(media_content_id, {})
                                    .get("s", {})
                                    .get("u", "")
                                ),
                            }
                        )
                    media_contents.append(new_image)

                # Gif
                elif mediaType == "AnimatedImage":
                    new_gif: Gif = {
                        "id": str(uuid.uuid4()),
                        "resolutions": [],
                        "_type": "gif",
                    }
                    for gif in (
                        post_detail.get("media_metadata", {})
                        .get(media_content_id, {})
                        .get("p", [])
                    ):
                        new_gif.get("resolutions", []).append(
                            {
                                "x": gif.get("x", 0),
                                "y": gif.get("y", 0),
                                "u": handleURL(gif.get("u", "")),
                            }
                        )

                    if (
                        post_detail.get("media_metadata", {})
                        .get(media_content_id, {})
                        .get("s", [])
                    ):
                        new_gif.get("resolutions", []).append(
                            {
                                "x": post_detail.get("media_metadata", {})
                                .get(media_content_id, {})
                                .get("s", {})
                                .get("x", 0),
                                "y": post_detail.get("media_metadata", {})
                                .get(media_content_id, {})
                                .get("s", {})
                                .get("y", 0),
                                "u": handleURL(
                                    post_detail.get("media_metadata", {})
                                    .get(media_content_id, {})
                                    .get("s", {})
                                    .get("gif", "")
                                ),
                            }
                        )
                    media_contents.append(new_gif)

                # Video
                elif mediaType == "RedditVideo":
                    video = post_detail.get("media_metadata", {}).get(
                        media_content_id, {}
                    )
                    new_video_multi: VideoMulti = {
                        "id": str(uuid.uuid4()),
                        "x": video.get("x", 0),
                        "y": video.get("y", 0),
                        "hlsUrl": handleURL(video.get("hlsUrl", "")),
                        "dashUrl": handleURL(video.get("dashUrl", "")),
                        "_type": "video",
                    }
                    media_contents.append(new_video_multi)
            return {"_type": "multi", "content": media_contents}

    # Gif
    if post_detail.get("preview", {}):
        gifs = (
            post_detail.get("preview", {})
            .get("images")[0]
            .get("variants", {})
            .get("gif", {})
            .get("resolutions", [])
        )
        if gifs:
            gif_content: Gif = {
                "id": str(uuid.uuid4()),
                "resolutions": [],
                "_type": "gif",
            }
            gifs = sorted(gifs, key=lambda x: x["height"])
            for gif in gifs:
                if gif.get("url", ""):
                    gif_content.get("resolutions", []).append(
                        {
                            "width": gif.get("width", 0),
                            "height": gif.get("height", 0),
                            "url": handleURL(gif.get("url", "")),
                        }
                    )
            return {"_type": "gif", "content": gif_content}

    # Video
    if post_detail.get("secure_media", {}):
        video = post_detail.get("secure_media", {}).get("reddit_video", {})
        if video:
            new_video: Video = {
                "id": str(uuid.uuid4()),
                "hls_url": handleURL(video.get("hls_url", "")),
                "dash_url": handleURL(video.get("dash_url", "")),
                "fallback_url": handleURL(video.get("fallback_url", "")),
                "scrubber_media_url": handleURL(video.get("scrubber_media_url", "")),
                "height": video.get("height", 0),
                "width": video.get("width", 0),
                "_type": "video",
            }
            return {"_type": "video", "content": new_video}

    # Image
    if post_detail.get("preview", {}):
        images = post_detail.get("preview", {}).get("images")[0].get("resolutions", [])
        if images:
            images = sorted(images, key=lambda x: x["height"])
            image_content: Image = {
                "id": str(uuid.uuid4()),
                "resolutions": [],
                "_type": "image",
            }
            sourceImage = (
                post_detail.get("preview", {}).get("images")[0].get("source", {})
            )
            for image in images:
                if image.get("url", ""):
                    new_image_resolution: ImageResolution = {
                        "height": image.get("height", 0),
                        "width": image.get("width", 0),
                        "url": handleURL(image["url"]),
                    }
                    image_content.get("resolutions", []).append(new_image_resolution)
            if sourceImage and sourceImage.get("url", ""):
                image_content.get("resolutions", []).append(
                    {
                        "height": sourceImage.get("height", 0),
                        "width": sourceImage.get("width", 0),
                        "url": handleURL(sourceImage["url"]),
                    }
                )
            return {"_type": "image", "content": image_content}

    # Gallery
    if post_detail.get("media_metadata", {}):
        gallery = post_detail.get("media_metadata", {})
        gallery_content: Gallery = {
            "id": str(uuid.uuid4()),
            "images": [],
            "_type": "gallery",
        }
        for imageID in gallery:
            images = gallery.get(imageID, {}).get("p", [])
            if images:
                images = sorted(images, key=lambda x: x["y"])
                image_resolutions: list[GalleryImageResolutions] = []
                for image in images:
                    if image.get("u"):
                        new_gallery_Image_Resolution: GalleryImageResolutions = {
                            "id": str(uuid.uuid4()),
                            "x": image.get("x", 0),
                            "y": image.get("y", 0),
                            "u": handleURL(image["u"]),
                        }
                        image_resolutions.append(new_gallery_Image_Resolution)
                source_image_gallery = gallery.get(imageID, {}).get("s", {})
                if source_image_gallery and source_image_gallery.get("u", ""):
                    image_resolutions.append(
                        {
                            "id": str(uuid.uuid4()),
                            "x": source_image_gallery.get("x", 0),
                            "y": source_image_gallery.get("y", 0),
                            "u": handleURL(source_image_gallery["u"]),
                        }
                    )
                gallery_content.get("images", []).append(image_resolutions)
        return {"_type": "gallery", "content": gallery_content}

    return {}


def buildPosts(raw_json: Any, awards: list[Awards]) -> list[Post]:
    posts: list[Post] = []
    unprocessed_posts = raw_json.get("data", {}).get("children", [])

    for unprocessed_post in unprocessed_posts:
        post_detail = unprocessed_post.get("data", {})

        if post_detail.get("author", "") == "[deleted]":
            continue

        logging.info(
            f"builidng post with title {post_detail.get("title", "")} and id {post_detail.get("id", "")}"
        )

        txt, txtHTML = "", ""
        if "crosspost_parent_list" in post_detail:
            txt = post_detail.get("crosspost_parent_list", [])
            if len(txt) > 0:
                txt = txt[0].get("selftext", "")
            else:
                txt = ""

            txtHTML = post_detail.get("crosspost_parent_list", [])
            if len(txtHTML) > 0:
                txtHTML = txtHTML[0].get("selftext_html", "")
            else:
                txtHTML = ""

        new_post: Post = {
            "id": post_detail.get("id", ""),
            "subreddit": post_detail.get("subreddit_name_prefixed", ""),
            "subreddit_id": post_detail.get("subreddit_id", "").replace("t5_", ""),
            "author": post_detail.get("author", ""),
            "author_fullname": post_detail.get("author_fullname", "").replace(
                "t2_", ""
            ),
            "title": post_detail.get("title", ""),
            "ups": post_detail.get("ups", 0),
            "over_18": post_detail.get("over_18", False),
            "spoiler": post_detail.get("spoiler", False),
            "link_flair_text": post_detail.get("link_flair_text", ""),
            "author_flair_text": post_detail.get("author_flair_text", ""),
            "created_utc": post_detail.get("created_utc", 0),
            "created_human": (
                unix_epoch_to_human_readable(post_detail.get("created_utc", 0))
                if post_detail.get("created_utc", 0)
                else ""
            ),
            "num_comments": post_detail.get("num_comments", 0),
            "awards": random.sample(awards, random.randint(0, 3)),
            "text": (
                post_detail.get("selftext", "")
                if post_detail.get("selftext", "")
                else txt
            ),
            "text_html": (
                post_detail.get("selftext_html", "")
                .replace("&lt;", "<")
                .replace("&gt;", ">")
                if post_detail.get("selftext_html", "")
                else txtHTML
            ),
            "comments": [],
            "media_content": {},
        }
        posts.append(new_post)
        logging.info(
            f"finished builidng post with title {post_detail.get("title", "")} and id {post_detail.get("id", "")}"
        )

    return posts


def removeDuplicateUser(users: list[User]) -> list[User]:
    seen_users: dict[str, bool] = {}
    final_users: list[User] = []

    for user in users:
        user_name = user.get("name", "")
        if user_name not in seen_users:
            final_users.append(user)
            seen_users[user_name] = True

    return final_users


def run():
    params = {
        "grant_type": "password",
        "username": username,
        "password": password,
    }
    acc_token = getToken(params, 10)

    # Get all awards
    awards: list[Awards] = fetchAwards()
    with open("awards.json", "w") as fp:
        json.dump(awards, fp)

    # Get all trophies
    trophies: list[Trophies] = fetchTrophies()
    with open("trophies.json", "w") as fp:
        json.dump(trophies, fp)

    topic_data = {}
    with open("./topics.json", "r") as fp:
        topic_data: dict[str, list[str]] = json.load(fp)

    subreddit_data: dict[str, list[Subreddit]] = {}
    with open("./subreddits.json", "r") as fp:
        subreddit_data = json.load(fp)

    if subreddit_data:
        # Final Users
        subreddit_users: dict[str, set[str]] = defaultdict(set[str])

        # Final Posts
        posts: list[Post] = []

        # on demand subreddits
        on_demand_subreddits: list[OnDemandSubreddit] = []
        try:
            with open("./ondemand.json", "r") as fp:
                on_demand_subreddits: list[OnDemandSubreddit] = json.load(fp)
        except Exception:
            print(traceback.print_exc())
            sys.exit(1)

        post_results_per_subreddit: list[PostResult] = []
        seen_subreddits: set[str] = set()

        # Get new posts of on-demand subreddit
        for on_demand_subreddit in on_demand_subreddits:
            title = on_demand_subreddit.get("title", "")
            if title.lower() in seen_subreddits:
                continue
            seen_subreddits.add(title.lower())
            posts_count = on_demand_subreddit.get("posts_count", 0)
            if not title or not posts_count:
                continue
            posts_result: PostResult = fetchPostsBySubreddt(
                POSTS_SORT_FILTER, posts_count, title, acc_token
            )
            if posts_result.get("posts", {}):
                post_results_per_subreddit.append(posts_result)

        # Get new posts of topic based subreddit
        if topic_data:
            for topic in subreddit_data:
                for _, subreddit in enumerate(subreddit_data[topic]):
                    title = subreddit.get("title", "")
                    if title.lower() in seen_subreddits:
                        continue
                    seen_subreddits.add(title.lower())
                    posts_result: PostResult = fetchPostsBySubreddt(
                        POSTS_SORT_FILTER, POSTS_PER_SUBREDDIT, title, acc_token
                    )
                    if posts_result.get("posts", {}):
                        post_results_per_subreddit.append(posts_result)

        for post_result in post_results_per_subreddit:
            raw_post_json = post_result.get("posts", {})
            subreddit_title = post_result.get("subreddit")
            logging.info(f"builidng all post for subreddit {subreddit_title}")
            posts = [*posts, *buildPosts(raw_post_json, awards)]
            logging.info(f"finished builidng all post for subreddit {subreddit_title}")

        # Fetch comments from the subreddit_posts
        for post in posts:
            subreddit = post.get("subreddit", "")
            subreddit_id = post.get("subreddit_id", "")
            post_id = post.get("id", "")
            raw_json_post = fetchPostArticleByPostID(subreddit, post_id, acc_token)
            if raw_json_post.get("post", []) and isinstance(
                raw_json_post.get("post", []), list
            ):
                # Media Content
                post_detail_media = (
                    raw_json_post.get("post", [])[0]
                    .get("data", {})
                    .get("children", [])[0]
                    .get("data", {})
                )
                logging.info(
                    f"building media for post with title {post.get("title", "")} and id {post_id}"
                )
                post["media_content"] = buildMedia(post_detail_media)
                logging.info(
                    f"finished building media for post with title {post.get("title", "")} and id {post_id}"
                )

                # Comment
                post_detail_comment = (
                    raw_json_post.get("post", [])[1].get("data", {}).get("children", [])
                )
                if post["author"] and post["author_fullname"]:
                    subreddit_users[subreddit_id].add(
                        json.dumps(
                            {
                                "subreddit_id": "",
                                "subreddit": "",
                                "id": post["author_fullname"],
                                "name": post["author"],
                            }
                        )
                    )
                logging.info(
                    f"building comments for post with title {post.get("title", "")} and id {post_id}"
                )
                comments, num_comments = buildComments(
                    post_detail_comment,
                    subreddit_users,
                    subreddit_id,
                    subreddit,
                )
                post["comments"] = comments
                post["num_comments"] = num_comments
                logging.info(
                    f"finished building comments for post with title {post.get("title", "")} and id {post_id}"
                )

        # Make posts
        with open("posts.json", "w") as fp:
            json.dump(posts, fp)

        seen_users: dict[str, User] = {}

        # Add moderators to subreddit_members
        for topic in subreddit_data:
            for idx, subreddit in enumerate(subreddit_data[topic]):
                subreddit_moderators: list[User] = []
                for moderator in subreddit.get("moderators", []):
                    moderator_id = moderator.get("id", "")
                    seen_users[moderator_id] = moderator
                    subreddit_moderators.append(moderator)
                subreddit_data[topic][idx]["members"] = subreddit_moderators

        # Add normal subreddit_members
        sub_users: dict[str, list[UserDetail]] = defaultdict(list[UserDetail])
        for subreddit_id in subreddit_users:
            users: list[UserDetail] = [
                json.loads(user) for user in subreddit_users[subreddit_id]
            ]
            sub_users[subreddit_id] = users

        for subreddit_id, users in sub_users.items():
            for topic in subreddit_data:
                for idx, subreddit in enumerate(subreddit_data[topic]):
                    sub_id = subreddit.get("id", "")
                    if subreddit_id == sub_id:
                        subreddit_members: list[User] = []
                        for user in users:
                            user_id = user.get("id", "")
                            user_name = user.get("name", "")
                            if user_id in seen_users:
                                subreddit_members.append(seen_users[user_id])
                            else:
                                curr_user = generate_user_info(
                                    user_id, user_name, trophies
                                )
                                subreddit_members.append(curr_user)
                                seen_users[user_id] = curr_user
                        oldMembers = subreddit_data[topic][idx].get("members", [])
                        subreddit_data[topic][idx]["members"] = [
                            *oldMembers,
                            *subreddit_members,
                        ]
                        members: list[User] = subreddit_data[topic][idx].get(
                            "members", []
                        )
                        if members:
                            subreddit_data[topic][idx]["members"] = [
                                json.loads(members)
                                for members in list(
                                    set(
                                        [
                                            json.dumps(j)
                                            for j in removeDuplicateUser(members)
                                        ]
                                    )
                                )
                            ]
        # Make subreddit members update
        with open("subreddits.json", "w") as fp:
            json.dump(subreddit_data, fp)

        # Make users
        tmp_users: list[User] = []
        with open("users.json", "w") as fp:
            for user in seen_users.values():
                tmp_users.append(user)
            json.dump(tmp_users, fp)
