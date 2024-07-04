from dotenv import dotenv_values
from helper.utils import getUserAgent, success, unix_epoch_to_human_readable
import asyncpraw

from subreddit.utils.getanchors import getAnchors
from subreddit.utils.getflairs import getFlairs
from subreddit.utils.getmoderatorsname import getModeratorsNames
from subreddit.utils.getrules import getRules

from numerize import numerize

# Load DOTENV
config = dotenv_values(".env")

# Credentials
client_id = config.get("client_id")
client_secret = config.get("client_secret")
user_agent = getUserAgent()


async def getSubredditsByTopics(topic, rate_limit, master, DONE, SUBREDDITS_DONE):
    seen_subreddits = set()

    async with rate_limit:
        print(f"Enterd {topic}")
        async with asyncpraw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent,
            username=config.get("username"),
            password=config.get("password"),
            ratelimit_seconds=300,
        ) as reddit:
            finalData = []

            TOTAL_SUBREDDITS_PER_TOPICS = int(config.get("TOTAL_SUBREDDITS_PER_TOPICS"))
            async for sreddit in reddit.subreddits.search(topic):
                if TOTAL_SUBREDDITS_PER_TOPICS == 0:
                    break
                obj = sreddit.__dict__
                if obj["subreddit_type"] == "private":
                    continue

                # Check for POST with alteast given amout of posts
                subreddit = await reddit.subreddit(obj.get("display_name", ""))
                postCount = int(config.get("POSTS_PER_SUBREDDIT"))

                subreddit_name = str(obj.get("display_name_prefixed", ""))

                if subreddit_name in seen_subreddits:
                    continue
                else:
                    seen_subreddits.add(subreddit_name)

                async for _ in subreddit.top():
                    if postCount == 0:
                        tmp = {}
                        # Basic info
                        tmp["id"] = obj.get("id", "")
                        tmp["title"] = obj.get("display_name_prefixed", "")
                        tmp["about"] = obj.get("public_description", "")
                        tmp["logoUrl"] = obj.get("community_icon", "")
                        tmp["bannerUrl"] = obj.get("banner_background_image", "")
                        tmp["category"] = topic

                        # Rules,Flairs,Anchors
                        tmp["rules"] = await getRules(
                            obj.get("display_name", ""), rate_limit
                        )
                        tmp["flairs"] = await getFlairs(
                            f"{obj.get('display_name','')}", rate_limit
                        )
                        tmp["anchors"] = await getAnchors(
                            obj.get("display_name", ""), rate_limit
                        )

                        # Colors
                        tmp["buttonColor"] = obj.get("key_color", "")
                        tmp["headerColor"] = obj.get("primary_color", "")
                        tmp["banner_background_color"] = obj.get(
                            "banner_background_color", "#33a8ff"
                        )

                        # Members,CreatedDate
                        tmp["creationDate"] = obj.get("created_utc", "")
                        if tmp["creationDate"]:
                            tmp["creationDateHuman"] = unix_epoch_to_human_readable(
                                int(tmp["creationDate"])
                            )
                        else:
                            tmp["creationDateHuman"] = 0

                        tmp["members"] = obj.get("subscribers", "")
                        if tmp["members"]:
                            tmp["membersHuman"] = numerize.numerize(int(tmp["members"]))
                        else:
                            tmp["membersHuman"] = 0

                        tmp["moderators"] = await getModeratorsNames(
                            obj.get("display_name", ""), rate_limit
                        )

                        # Spolier , NSFW
                        tmp["over18"] = obj.get("over18", "")
                        tmp["spoilers_enabled"] = obj.get("spoilers_enabled", "")

                        finalData.append(tmp)
                        TOTAL_SUBREDDITS_PER_TOPICS -= 1
                        print(tmp)
                        print(f"Done {obj.get('display_name','NA')}")
                        SUBREDDITS_DONE[0] += 1

                        success(f"TOTAL SUBREDDITS DONE :{SUBREDDITS_DONE} ........")

                        break
                    postCount -= 1

            master[topic] = finalData
            DONE[0] -= 1
            success(f"TOTAL TOPICS left {DONE[0]} ......")

    return "Done!"
