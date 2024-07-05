#!/usr/bin/env python3

import asyncio
import os
import time

from helper.utils import danger
from subreddit.subreddits import run as subreddit_run
from post.posts import run as post_run
from user.users import run as user_run
from split import split_files


async def run_script(script_name):
    retries = 100
    curr_retry_count = retries

    while curr_retry_count:
        try:
            if script_name == "subreddit":
                await subreddit_run()
                break
            elif script_name == "post":
                await post_run()
                break
            elif script_name == "user":
                await user_run()
                break
            else:
                danger("Wrong script_name entered!")
                raise SystemExit

        except Exception as e:
            danger(
                f"Retrying script {script_name} {abs(retries-curr_retry_count)} times(s) ..."
            )
            danger(f"Error occured {script_name} {str(e)}")
            curr_retry_count -= 1
            time.sleep(6)

    if curr_retry_count == 0:
        raise SystemExit


if __name__ == "__main__":

    # Start measuring time
    start_time = time.time()

    # Clean
    os.system("rm errs.txt")
    os.system("touch errs.txt")
    os.system("rm ./noposts.txt")
    os.system(
        "rm ./comments-got.txt ./comments-errs.txt ./comments-retry.txt ./comments-status.txt"
    )

    # Run scripts one by one
    asyncio.run(run_script("subreddit"))
    asyncio.run(run_script("post"))
    asyncio.run(run_script("user"))

    # Split Files into chunks for easy importing
    split_files()
    os.system("mkdir json")
    os.system(
        "mv posts.json posts_p1.json subreddits.json subreddits_p1.json user_p1.json user_p2.json users.json json/"
    )

    # End measuring time
    end_time = time.time()

    # Calculate the difference in seconds
    execution_time = end_time - start_time

    # Convert the execution time to days, hours, minutes, and seconds
    days = execution_time // (24 * 60 * 60)
    hours = (execution_time % (24 * 60 * 60)) // (60 * 60)
    minutes = (execution_time % (60 * 60)) // 60
    seconds = execution_time % 60

    print(
        f"Execution Time: {int(days)} day(s), {int(hours)} hour(s), {int(minutes)} minute(s), {int(seconds)} second(s)"
    )
