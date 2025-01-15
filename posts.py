import logging
import string
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

from colorama import Fore, Style
from bs4 import BeautifulSoup
from dotenv import dotenv_values

from subreddits import Subreddit, writeResult
from users import User, generate_user_info


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


class ResultState(TypedDict):
    status_code: int
    success: bool
    error: str


class PostResult(TypedDict):
    subreddit: str
    posts: Any | None
    result_state: ResultState


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


class PostArticleResult(TypedDict):
    subreddit: str
    post: Any | None
    result_state: ResultState


class UserDetail(TypedDict):
    id: str
    name: str
    subreddit: str
    subreddit_id: str


# Set up logging
logging.basicConfig(
    filename="api_requests.log", level=logging.INFO, format="%(message)s"
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


def unix_to_relative_time(unix_time):
    now = datetime.datetime.now()
    diff = now - datetime.datetime.fromtimestamp(unix_time)

    years = int(diff.days / 365)
    days = abs(diff.days) % 365
    hours = abs(diff.seconds) // 3600
    minutes = abs(diff.seconds) // 60 % 60
    seconds = abs(diff.seconds) % 60

    if years > 0:
        return f"{years} year{'' if years == 1 else 's'} ago"
    elif days > 0:
        plural = "day" if days == 1 else "days"
        return f"{days} {plural} ago"
    elif hours > 0:
        plural = "hour" if hours == 1 else "hours"
        return f"{hours} {plural} ago"
    elif minutes > 0:
        plural = "minute" if minutes == 1 else "minutes"
        return f"{minutes} {plural} ago"
    else:
        if seconds > 0:
            return "a moment ago"
        else:
            return "just now"


# Get Custom User agent string
def getUserAgent() -> str:
    letters = string.ascii_lowercase
    length = 10
    return f"User agent by {str(uuid.uuid4())}-" + "".join(
        random.choice(letters) for _ in range(length)
    )


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
def getToken(params: dict[str, str], headers: dict[str, str], timeout: int) -> str:
    if not client_id or not client_secret or not username or not password:
        return ""
    session = getSession()
    session.auth = (client_id, client_secret)
    resp: AccessTokenResponse = session.post(
        "https://www.reddit.com/api/v1/access_token",
        data=params,
        headers=headers,
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
                headers={
                    "User-Agent": getUserAgent(),
                    "Authorization": f"bearer {token}",
                },
                params={"limit": limit, "show": "all", "sr_detail": True},
            )
        else:
            response = session.get(
                f"https://www.reddit.com/{subreddit}/{filter}.json",
                headers={
                    "User-Agent": getUserAgent(),
                    "Authorization": f"bearer {token}",
                },
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
                headers={
                    "User-Agent": getUserAgent(),
                    "Authorization": f"bearer {token}",
                },
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
                headers={
                    "User-Agent": getUserAgent(),
                    "Authorization": f"bearer {token}",
                },
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
    if encodedURL.find("https://www.reddit.com/media") != -1:
        data = parse_qs(encodedURL)
        return [data[item] for item in data][0][0]

    else:
        return urllib.parse.unquote(html.unescape(encodedURL))


def extract_comments(
    comments_raw_json: Any,
    users: dict[str, list[UserDetail]],
    subreddit_id: str,
    subreddit: str,
) -> tuple[list[Comment], int]:
    logging.info("Extracting comments")
    extracted_comments: list[Comment] = []
    num_comments = 0
    for comment in comments_raw_json:
        if isinstance(comment, dict) and comment.get("kind", "") == "t1":
            comment_data = comment.get("data", {})
            author = comment_data.get("author", "")
            author_fullname = comment_data.get("author_fullname", "").replace("t2_", "")
            extracted_comment: Comment = {
                "author": author,
                "author_fullname": author_fullname,
                "author_flair_text": comment_data.get("author_flair_text", ""),
                "body": comment_data.get("body", ""),
                "body_html": comment_data.get("body_html", ""),
                "ups": comment_data.get("ups", 0),
                "score": comment_data.get("score", 0),
                "replies": [],
            }
            if author and author_fullname:
                users[subreddit_id].append(
                    {
                        "id": author_fullname,
                        "name": author,
                        "subreddit_id": subreddit_id,
                        "subreddit": subreddit,
                    }
                )

            replies = comment_data.get("replies", {})
            num_comments += 1
            if isinstance(replies, dict):
                replies, _num_comments = extract_comments(
                    replies.get("data", {}).get("children", []),
                    users,
                    subreddit_id,
                    subreddit,
                )
                extracted_comment["replies"] = replies
                num_comments += _num_comments
            extracted_comments.append(extracted_comment)
    logging.info("Successfully extracted comments")
    return (extracted_comments, num_comments)


def getMedia(post_detail: Any) -> Media_Content:
    # Link
    postBody = post_detail.get("selftext", "")
    postHTML = post_detail.get("selftext_html", "")
    if (
        not postBody
        and not postHTML
        and "https://i.redd.it" not in post_detail.get("url", "")
        and "secure_media" not in post_detail
    ):
        new_link: Link = {
            "id": str(uuid.uuid4()),
            "link": post_detail.get("url", ""),
            "_type": "link",
        }
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
                            "url": gif.get("url", ""),
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


def getPosts(raw_json: Any, awards: list[Awards]) -> list[Post]:
    posts: list[Post] = []
    unprocessed_posts = raw_json.get("data", {}).get("children", [])

    for unprocessed_post in unprocessed_posts:
        post_detail = unprocessed_post.get("data", {})

        txt, txtHTML = "", ""
        if "crosspost_parent_list" in post_detail:
            txt = post_detail.get("crosspost_parent_list", [])[0].get("selftext", "")
            txtHTML = post_detail.get("crosspost_parent_list", [])[0].get(
                "selftext_html", ""
            )

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
                unix_to_relative_time(post_detail.get("created_utc", 0))
                if post_detail.get("created_utc", 0)
                else ""
            ),
            "num_comments": post_detail.get("num_comments", 0),
            "awards": random.choices(awards, k=random.randint(0, 4)),
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

    return posts


def run():
    params = {
        "grant_type": "password",
        "username": username,
        "password": password,
    }
    headers = {"User-Agent": getUserAgent()}
    acc_token = getToken(params, headers, 10)

    # Get all awards
    awards: list[Awards] = fetchAwards()

    data: dict[str, list[Subreddit]] = {}
    with open("./subreddits.json", "r") as fp:
        data = json.load(fp)

    if data:
        # Final Users
        subreddit_users: dict[str, list[UserDetail]] = defaultdict(list[UserDetail])

        # Final Posts
        posts: list[Post] = []

        # Get new posts of subreddit
        post_results_per_subreddit: list[PostResult] = []
        for topic in data:
            for _, subreddit in enumerate(data[topic]):
                title = subreddit.get("title", "")
                posts_result: PostResult = fetchPostsBySubreddt(
                    POSTS_SORT_FILTER, POSTS_PER_SUBREDDIT, title, acc_token
                )
                post_results_per_subreddit.append(posts_result)

        with open("request_status.txt", "a") as f:
            for result in post_results_per_subreddit:
                writeResult(
                    result["subreddit"] + " posts-per-subreddit", result["result_state"]
                )
            f.write("\n")

        for post_result in post_results_per_subreddit:
            raw_post_json = post_result.get("posts", {})
            posts = [*posts, *getPosts(raw_post_json, awards)]

        # Fetch comments from the subreddit_posts
        for post in posts:
            subreddit = post.get("subreddit", "")
            subreddit_id = post.get("subreddit_id", "")
            post_id = post.get("id", "")
            raw_json_post = fetchPostArticleByPostID(subreddit, post_id, acc_token)
            with open("request_status.txt", "a") as f:
                for result in post_results_per_subreddit:
                    writeResult(
                        result["subreddit"] + f" post-by-id {post_id}",
                        result["result_state"],
                    )
                f.write("\n")
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
                post["media_content"] = getMedia(post_detail_media)

                # Comment
                post_detail_comment = (
                    raw_json_post.get("post", [])[1].get("data", {}).get("children", [])
                )
                if post["author"] and post["author_fullname"]:
                    subreddit_users[subreddit_id].append(
                        {
                            "subreddit_id": "",
                            "subreddit": "",
                            "id": post["author_fullname"],
                            "name": post["author"],
                        }
                    )
                comments, num_comments = extract_comments(
                    post_detail_comment, subreddit_users, subreddit_id, subreddit
                )
                post["comments"] = comments
                post["num_comments"] = num_comments

        # Make posts
        with open("posts.json", "w") as fp:
            json.dump(posts, fp)

        seen_users: dict[str, User] = {}

        # Add moderators to subreddit_members
        for topic in data:
            for idx, subreddit in enumerate(data[topic]):
                subreddit_moderators: list[User] = []
                for moderator in subreddit.get("moderators", []):
                    moderator_id = moderator.get("id", "")
                    seen_users[moderator_id] = moderator
                    subreddit_moderators.append(moderator)
                data[topic][idx]["members"] = subreddit_moderators

        # Add normal subreddit_members
        for subreddit_id, users in subreddit_users.items():
            for topic in data:
                for idx, subreddit in enumerate(data[topic]):
                    sub_id = subreddit.get("id", "")
                    if subreddit_id == sub_id:
                        subreddit_members: list[User] = []
                        for user in users:
                            user_id = user.get("id", "")
                            user_name = user.get("name", "")
                            if user_id in seen_users:
                                subreddit_members.append(seen_users[user_id])
                            else:
                                curr_user = generate_user_info(user_id, user_name)
                                subreddit_members.append(curr_user)
                                seen_users[user_id] = curr_user
                        oldMembers = data[topic][idx].get("members", [])
                        data[topic][idx]["members"] = [*oldMembers, *subreddit_members]
                        if (
                            "members" in data[topic][idx]
                            and data[topic][idx]["members"]
                        ):
                            data[topic][idx]["members"] = [
                                json.loads(i)
                                for i in list(
                                    set(
                                        [
                                            json.dumps(j)
                                            for j in data[topic][idx]["members"]
                                        ]
                                    )
                                )
                            ]
        # Make subreddit members update
        with open("subreddits.json", "w") as fp:
            json.dump(data, fp)

        # Make users
        tmp_users: list[User] = []
        with open("users.json", "w") as fp:
            for user in seen_users.values():
                tmp_users.append(user)
            json.dump(tmp_users, fp)
