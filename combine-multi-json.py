import json
import os

num = 2
username = os.getenv("USER")

posts = []
users = {}
sub = {}

# posts
res = []
for i in range(1, num + 1):
    loc = f"/home/{username}/cdx/dataset/vox-populi/{i}/json/posts.json"
    with open(loc, "r") as fp:
        data = json.load(fp)
        posts = [*posts, *data]
with open("posts.json", "w") as fp:
    json.dump(posts, fp)


# subreddit
res = {}
for i in range(1, num + 1):
    loc = f"/home/{username}/cdx/dataset/vox-populi/{i}/json/subreddits.json"
    with open(loc, "r") as fp:
        data = json.load(fp)
        if i == 1:
            res = {**res, **data}
        else:
            for topic in data:
                for sreddit in data[topic]:
                    res[topic].append(sreddit)

with open("subreddits.json", "w") as fp:
    json.dump(res, fp)


# users
res = {}
for i in range(1, num + 1):
    loc = f"/home/{username}/cdx/dataset/vox-populi/{i}/json/users.json"
    with open(loc, "r") as fp:
        data = json.load(fp)
        res = {**res, **data}

with open("users.json", "w") as fp:
    json.dump(res, fp)
