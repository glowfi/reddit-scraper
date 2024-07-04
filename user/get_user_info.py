import asyncpraw
from dotenv import dotenv_values
from helper.utils import epoch_age, getDate, getUserAgent, success


# Load DOTENV
config = dotenv_values(".env")

# Credentials
client_id = config.get("client_id")
client_secret = config.get("client_secret")
user_agent = getUserAgent()


async def getRedditorInfo(redditor_name, aid, userInfo, rate_limit, total_users):
    async with rate_limit:
        async with asyncpraw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=getUserAgent(),
            username=config.get("username"),
            password=config.get("password"),
            ratelimit_seconds=300,
            timeout=32,
        ) as reddit:
            try:
                redditor = await reddit.redditor(redditor_name, fetch=True)
            except Exception as e:
                with open("user_errors.txt", "a") as fp:
                    fp.write(
                        str(redditor_name) + " " + str(e) + "\n",
                    )
                print(f"Error with {redditor_name}")
                return

            if not hasattr(redditor, "id"):
                print(f"{redditor_name} Account Suspended")
                userInfo[aid]["cakeDay"] = "NA"
                userInfo[aid]["cakeDayHuman"] = "NA"
                userInfo[aid]["age"] = "NA"
                userInfo[aid]["avatar_img"] = "NA"
                userInfo[aid]["banner_img"] = "NA"
                userInfo[aid]["publicDescription"] = "NA"
                userInfo[aid]["over18"] = "NA"
                userInfo[aid]["keycolor"] = "NA"
                userInfo[aid]["primarycolor"] = "NA"
                userInfo[aid]["iconcolor"] = "NA"
                userInfo[aid]["supended"] = True
            else:
                try:
                    print(f"{redditor_name}")
                    await redditor.load()
                    if hasattr(redditor, "id"):
                        await redditor.subreddit.load()
                        print(f"Got Back {redditor_name}!")
                except Exception as e:
                    print("Handled Exception!", e)

                if redditor:
                    try:
                        userInfo[aid]["cakeDay"] = redditor.created_utc
                        userInfo[aid]["cakeDayHuman"] = getDate(redditor.created_utc)
                        userInfo[aid]["age"] = epoch_age(redditor.created_utc)
                        userInfo[aid]["avatar_img"] = redditor.icon_img
                        userInfo[aid]["banner_img"] = (
                            redditor.subreddit.banner_img if redditor.subreddit else ""
                        )
                        userInfo[aid]["publicDescription"] = (
                            redditor.subreddit.public_description
                            if redditor.subreddit
                            else ""
                        )
                        userInfo[aid]["over18"] = (
                            redditor.subreddit.over18 if redditor.subreddit else ""
                        )
                        userInfo[aid]["keycolor"] = (
                            redditor.subreddit.key_color if redditor.subreddit else ""
                        )
                        userInfo[aid]["primarycolor"] = (
                            redditor.subreddit.primary_color
                            if redditor.subreddit
                            else ""
                        )
                        userInfo[aid]["iconcolor"] = (
                            redditor.subreddit.icon_color if redditor.subreddit else ""
                        )
                        userInfo[aid]["supended"] = False

                        total_users[0] -= 1
                        success(f"More {total_users} left ...")

                    except Exception as e:
                        with open("user_errors.txt", "a") as fp:
                            fp.write(
                                str(redditor_name) + " " + str(e) + "\n",
                            )
                        print(f"Error with {redditor_name}")
