import logging
import uuid
import string
import random
import datetime
from datetime import timedelta
import urllib.parse
from urllib.parse import parse_qs
from urllib.parse import urlparse, urlunparse
import time


# Log asyncpraw
def start_logging():
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    for logger_name in ("asyncpraw", "asyncprawcore"):
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.DEBUG)
        logger.addHandler(handler)


# Get Custom User agent string
def getUserAgent():
    letters = string.ascii_lowercase
    length = 10
    return f"User agent by {str(uuid.uuid4())}-" + "".join(
        random.choice(letters) for _ in range(length)
    )


# Headers
headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Encoding": "gzip,deflate,br",
    "Accept-Language": "en-US,en;q=0.5",
    "Connection": "keep-alive",
    "DNT": "1",
    "Host": "www.reddit.com",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "TE": "trailers",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": f"{getUserAgent()}",
}


# Get Human Readable Date [Unix epoch to human readable data]
def unix_epoch_to_human_readable(unixtime):
    dt = datetime.datetime.utcfromtimestamp(unixtime)

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


# Log messages to a file
def log_message(msg, filename):
    with open(filename, "a") as fp:
        fp.write(msg + "\n")


# Given a url it will remove trailing slashes from an url
def sanitize_url(url):
    parsed_url = urlparse(url)
    new_url = urlunparse(
        (
            parsed_url.scheme,
            parsed_url.netloc,
            parsed_url.path.rstrip("/"),
            parsed_url.params,
            parsed_url.query,
            parsed_url.fragment,
        )
    )
    return str(new_url)


# Sanitize and encode reddit media URL
def handleURL(encodedURL: str):
    if encodedURL.find("https://www.reddit.com/media") != -1:
        data = parse_qs(encodedURL)
        return [data[item] for item in data][0][0]

    else:
        return urllib.parse.unquote(encodedURL)


# Unix epoch to age [3yrs 6yrs 9yrs]
def epoch_age(epoch_time):
    # Convert the input to Unix epoch time if it's not already in that format
    if isinstance(epoch_time, str):
        epoch_time = int(float(epoch_time[1:]))

    current_time = int(time.time())
    age_in_seconds = current_time - epoch_time

    years = age_in_seconds // (365 * 24 * 60 * 60)

    return f"{years}yr(s)"


# Timestamp to date format
def getDate(timestamp):
    # Convert Unix epoch time to datetime object
    dt = datetime.datetime.utcfromtimestamp(timestamp)

    # Subtract 8 hours from the original timezone to get the local timezone
    dt = dt - timedelta(hours=8)

    # Format the date and time in desired format
    return dt.strftime("%d %B %Y")


# Helper function to simulate moments.js
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


# Generate random unix epoch
def generate_random_epoch():
    start_date = datetime.datetime(2005, 1, 10)
    end_date = datetime.datetime(2024, 2, 14)

    # Calculate the difference in seconds between the start and end dates
    diff_seconds = (end_date - start_date).total_seconds()

    # Generate a random number of seconds within the range
    random_seconds = random.uniform(0, diff_seconds)

    # Add the random number of seconds to the start date to get the random epoch time
    random_epoch = int((start_date + timedelta(seconds=random_seconds)).timestamp())

    return random_epoch


# Generate random hex color
def generate_random_hex_color():
    # Generate random RGB values
    r = random.randint(0, 255)
    g = random.randint(0, 255)
    b = random.randint(0, 255)

    # Convert to hexadecimal and make sure it's two digits long
    r_hex = hex(r).lstrip("0x").zfill(2)
    g_hex = hex(g).lstrip("0x").zfill(2)
    b_hex = hex(b).lstrip("0x").zfill(2)

    # Combine the RGB values into a single hex color string
    return "#" + r_hex + g_hex + b_hex


# Print messages colored
def success(msg):
    print("\x1b[6;30;42m" + f"{msg}" + "\x1b[0m")


def danger(msg):
    print("\033[41m" + msg + "\033[0m")
