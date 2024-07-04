from post.utils.comments.addcommenteduser import add_commented_user_to_user_list


# Extract deep nested comments
async def extractDeepnestedComments(
    _res_data, parent_id, topic, allUsers, seenUsers, trophies
):
    finalData = []
    for comm in _res_data:
        # Comment txt : data->(author,author_fullname(t2),created_utc,body,id,ups)
        # Replies : replies->data->children[]

        tmp = {}
        notGotValues = 0

        tmp["subreddit_id"] = (
            comm.get("data", {}).get("subreddit_id", "").replace("t5_", "")
        )
        tmp["subreddit_name"] = comm.get("data", {}).get("subreddit", "")
        tmp["author"] = comm.get("data", {}).get("author", "")
        tmp["author_id"] = (
            comm.get("data", {}).get("author_fullname", "").replace("t2_", "")
        )
        tmp["created_utc"] = comm.get("data", {}).get("created_utc", "")
        tmp["parent_comment_id"] = parent_id
        tmp["comment_id"] = comm.get("data", {}).get("id", "")
        tmp["comment"] = comm.get("data", {}).get("body", "")
        tmp["comment_html"] = comm.get("data", {}).get("body_html", "")
        if tmp["comment_html"]:
            tmp["comment_html"] = (
                tmp["comment_html"].replace("&lt;", "<").replace("&gt;", ">")
            )

        tmp["comment_ups"] = comm.get("data", {}).get("ups", "")
        tmp["category"] = topic

        for i in tmp:
            if tmp[i] == "":
                notGotValues += 1

        if notGotValues >= 4:
            continue

        author, authorID = tmp["author"], tmp["author_id"]

        if author == "[deleted]" or author == "[removed]" or not author:
            continue

        if author and authorID:
            add_commented_user_to_user_list(
                author,
                authorID,
                allUsers,
                tmp["subreddit_name"],
                tmp["subreddit_id"],
                seenUsers,
                trophies,
            )
        try:
            tmp["replies"] = await extractDeepnestedComments(
                comm.get("data", {})
                .get("replies", {})
                .get("data", {})
                .get("children", []),
                comm.get("data", {}).get("id", ""),
                topic,
                allUsers,
                seenUsers,
                trophies,
            )
        except Exception as e:
            # print(str(e))
            tmp["replies"] = []

        finalData.append(dict(sorted(tmp.copy().items())))

    return finalData
