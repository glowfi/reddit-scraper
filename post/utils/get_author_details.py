# Get current post_author_name and id
from post.utils.comments.addcommenteduser import add_commented_user_to_user_list


def get_author_details(resData, allUsers, seenUsers, trophies):
    res_data = resData[1].get("data", {}).get("children", [])
    currPostAuthor = (
        resData[0]
        .get("data", {})
        .get("children", [0])[0]
        .get("data", [])
        .get("author", "")
    )
    currPostAuthorID = (
        resData[0]
        .get("data", {})
        .get("children", [0])[0]
        .get("data", [])
        .get("author_fullname", "")
        .replace("t2_", "")
    )
    print("ALERT .....", currPostAuthor, currPostAuthorID)
    if currPostAuthor and currPostAuthorID:
        add_commented_user_to_user_list(
            currPostAuthor,
            currPostAuthorID,
            allUsers,
            resData[0]
            .get("data", {})
            .get("children", [0])[0]
            .get("data", [])
            .get("subreddit", ""),
            resData[0]
            .get("data", {})
            .get("children", [0])[0]
            .get("data", [])
            .get("subreddit_id", "")
            .replace("t5_", ""),
            seenUsers,
            trophies,
        )

    return res_data
