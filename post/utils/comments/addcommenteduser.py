import random


# Add the comment author to global users list
def add_commented_user_to_user_list(
    author, author_id, allUsers, subreddit, subredditID, seenUsers, trophies
):
    if author_id and author_id not in seenUsers:
        tmp = {
            "id": author_id,
            "username": author,
            "password": "pass",
            "subreddits_member": (
                [[subredditID, subreddit]] if subreddit and subredditID else []
            ),
            "trophies": random.choices(trophies, k=random.randint(1, 5)),
        }

        allUsers[author_id] = dict(sorted(tmp.copy().items()))
        seenUsers.add(author_id)

    else:
        subreddit_lists = allUsers.get(author_id).get("subreddits_member", [])
        if subredditID and subreddit and subreddit_lists:
            data = [subredditID, subreddit]
            if data not in subreddit_lists:
                subreddit_lists.append(data)
