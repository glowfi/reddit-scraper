import json
import copy


def split_files():

    # Subreddits split array
    with open("./subreddits.json") as f:
        data = json.load(f)

    arr1 = []

    for topic in data:
        for reddits in data[topic]:
            arr1.append(reddits)

    with open("./subreddits_p1.json", "w") as f:
        json.dump(arr1, f)

    # Posts split array
    with open("./posts.json") as f:
        data = json.load(f)

    # change media_metadata to media_content
    c = 0
    for post in data:
        if "media_metadata" in post:
            copied_dict = copy.deepcopy(post)
            data[c]["media_content"] = copied_dict["media_metadata"]
            del data[c]["media_metadata"]
        c += 1

    # Make link_type false if this "https://i.reddit" is found
    idx = 0
    for post in data:
        if post["link_type"]:
            if "https://i.redd.it" in post["text"]:
                data[idx]["link_type"] = False
            if "media_content" in post and post["media_content"]["type"] == "video":
                data[idx]["link_type"] = False
            if "media_content" in post and post["media_content"]["type"] == "gallery":
                data[idx]["link_type"] = False

        idx += 1

    with open("./posts.json", "w") as f:
        json.dump(data, f)

    arr2 = []

    for post in data:
        arr2.append(post)

    with open("./posts_p1.json", "w") as f:
        json.dump(arr2, f)

    # User split array
    with open("./users.json") as f:
        data = json.load(f)

    c = 0
    arr1, arr2 = [], []

    for i in data:
        if c > len(data) // 2:
            arr2.append(data[i])
        else:
            arr1.append(data[i])
        c += 1

    with open("./user_p1.json", "w") as f:
        json.dump(arr1, f)

    with open("./user_p2.json", "w") as f:
        json.dump(arr2, f)


split_files()
