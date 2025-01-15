import json


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
            arr2.append(i)
        else:
            arr1.append(i)
        c += 1

    with open("./user_p1.json", "w") as f:
        json.dump(arr1, f)

    with open("./user_p2.json", "w") as f:
        json.dump(arr2, f)
