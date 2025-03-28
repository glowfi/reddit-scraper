import json
import glob
import sys

import re
from typing import DefaultDict


def replace_all_occurences_in_a_string(text, replacements):
    if text is None:
        return ""
    for to_replace, replace_with in replacements.items():
        pattern = re.compile(re.escape(to_replace), re.IGNORECASE)
        text = pattern.sub(replace_with, text)
    return text


file_names = [
    "topics.json",
    "awards.json",
    "trophies.json",
    "subreddits.json",
    "posts.json",
    "users.json",
]


def handleOthers(data, file_name):
    st = set()
    seen_id = set()
    for row in data:
        if (
            file_name != "awards.json"
            and file_name != "trophies.json"
            and file_name != "topics.json"
        ):
            id = row.get("id", "")
            if id and id not in seen_id:
                st.add(json.dumps(row))
                seen_id.add(id)
        else:
            st.add(json.dumps(row))
    return [json.loads(i) for i in list(st)]


multi_dataset_location = ""

if not multi_dataset_location:
    print("no dataser folder location entered")
    sys.exit(1)

files = []
for directory in glob.glob(f"{multi_dataset_location}/*"):
    for file in glob.glob(f"{directory}/*"):
        files.append(file)

for file_name in file_names:
    final = []
    for file in files:
        if file.lower().find(file_name.lower()) != -1:
            with open(file) as fp:
                data = json.load(fp)
                if file_name == "subreddits.json":
                    for topic in data:
                        for subreddit in data[topic]:
                            final.append(subreddit)
                elif file_name == "topics.json":
                    for topic in data:
                        for t in data[topic]:
                            final.append({"topic": t})
                else:
                    final = [*final, *data]
        res = handleOthers(final, file_name)
        with open(f"{file_name}", "w") as fp:
            json.dump(res, fp)


### Voxify


def save_json(file_path, content):
    with open(file_path, "w") as fp:
        json.dump(content, fp)


for file_name in file_names:
    if file_name == "awards.json":
        with open(file_name) as fp:
            awards = json.load(fp)
            for idx, _ in enumerate(awards):
                awards[idx]["title"] = replace_all_occurences_in_a_string(
                    awards[idx]["title"],
                    {"subreddit": "voxsphere", "reddit": "voxpopuli", "r/": "v/"},
                )
            save_json("awards.json", awards)

    if file_name == "trophies.json":
        with open(file_name) as fp:
            trophies = json.load(fp)
            for idx, _ in enumerate(trophies):
                trophies[idx]["title"] = replace_all_occurences_in_a_string(
                    trophies[idx]["title"],
                    {"subreddit": "voxsphere", "reddit": "voxpopuli", "r/": "v/"},
                )
                trophies[idx]["description"] = replace_all_occurences_in_a_string(
                    trophies[idx]["description"],
                    {"subreddit": "voxsphere", "reddit": "voxpopuli", "r/": "v/"},
                )
            save_json("trophies.json", trophies)

    if file_name == "subreddits.json":
        with open(file_name) as fp:
            subs = json.load(fp)
            topicWiseSubreddit = DefaultDict(list)
            for idx, _ in enumerate(subs):
                subs[idx]["title"] = replace_all_occurences_in_a_string(
                    subs[idx]["title"],
                    {
                        "subreddit": "voxsphere",
                        "reddit": "voxpopuli",
                        "r/": "v/",
                    },
                )
                subs[idx]["public_description"] = replace_all_occurences_in_a_string(
                    subs[idx]["public_description"],
                    {
                        "subreddit": "voxsphere",
                        "reddit": "voxpopuli",
                        "r/": "v/",
                    },
                )

                for idx2, _ in enumerate(subs[idx]["rules"]):
                    subs[idx]["rules"][idx2]["description"] = (
                        replace_all_occurences_in_a_string(
                            subs[idx]["rules"][idx2]["description"],
                            {
                                "subreddit": "voxsphere",
                                "reddit": "voxpopuli",
                                "r/": "v/",
                            },
                        )
                    )

                for idx3, _ in enumerate(subs[idx]["members"]):
                    subs[idx]["members"][idx3]["public_description"] = (
                        replace_all_occurences_in_a_string(
                            subs[idx]["members"][idx3]["public_description"],
                            {
                                "subreddit": "voxsphere",
                                "reddit": "voxpopuli",
                                "r/": "v/",
                            },
                        )
                    )
                    subs[idx]["members"][idx3]["name"] = (
                        replace_all_occurences_in_a_string(
                            subs[idx]["members"][idx3]["name"],
                            {
                                "subreddit": "voxsphere",
                                "reddit": "voxpopuli",
                                "r/": "v/",
                            },
                        )
                    )
                    for idx6, _ in enumerate(subs[idx]["members"][idx3]["trophies"]):
                        subs[idx]["members"][idx3]["trophies"][idx6]["description"] = (
                            replace_all_occurences_in_a_string(
                                subs[idx]["members"][idx3]["trophies"][idx6][
                                    "description"
                                ],
                                {
                                    "subreddit": "voxsphere",
                                    "reddit": "voxpopuli",
                                    "r/": "v/",
                                },
                            )
                        )
                        subs[idx]["members"][idx3]["trophies"][idx6]["title"] = (
                            replace_all_occurences_in_a_string(
                                subs[idx]["members"][idx3]["trophies"][idx6]["title"],
                                {
                                    "subreddit": "voxsphere",
                                    "reddit": "voxpopuli",
                                    "r/": "v/",
                                },
                            )
                        )

                for idx4, _ in enumerate(subs[idx]["moderators"]):
                    subs[idx]["moderators"][idx4]["public_description"] = (
                        replace_all_occurences_in_a_string(
                            subs[idx]["moderators"][idx4]["public_description"],
                            {
                                "subreddit": "voxsphere",
                                "reddit": "voxpopuli",
                                "r/": "v/",
                            },
                        )
                    )
                    subs[idx]["moderators"][idx4]["name"] = (
                        replace_all_occurences_in_a_string(
                            subs[idx]["moderators"][idx4]["name"],
                            {
                                "subreddit": "voxsphere",
                                "reddit": "voxpopuli",
                                "r/": "v/",
                            },
                        )
                    )
                    for idx6, _ in enumerate(subs[idx]["moderators"][idx4]["trophies"]):
                        subs[idx]["moderators"][idx4]["trophies"][idx6][
                            "description"
                        ] = replace_all_occurences_in_a_string(
                            subs[idx]["moderators"][idx4]["trophies"][idx6][
                                "description"
                            ],
                            {
                                "subreddit": "voxsphere",
                                "reddit": "voxpopuli",
                                "r/": "v/",
                            },
                        )
                        subs[idx]["moderators"][idx4]["trophies"][idx6]["title"] = (
                            replace_all_occurences_in_a_string(
                                subs[idx]["moderators"][idx4]["trophies"][idx6][
                                    "title"
                                ],
                                {
                                    "subreddit": "voxsphere",
                                    "reddit": "voxpopuli",
                                    "r/": "v/",
                                },
                            )
                        )
                topic = subs[idx]["topic"]
                topicWiseSubreddit[topic].append(subs[idx])
        save_json("subreddits.json", topicWiseSubreddit)

    if file_name == "posts.json":
        with open(file_name) as fp:
            posts = json.load(fp)
            for idx, post in enumerate(posts):
                posts[idx]["subreddit"] = replace_all_occurences_in_a_string(
                    posts[idx]["subreddit"],
                    {"subreddit": "voxsphere", "reddit": "voxpopuli", "r/": "v/"},
                )
                posts[idx]["title"] = replace_all_occurences_in_a_string(
                    posts[idx]["title"],
                    {"subreddit": "voxsphere", "reddit": "voxpopuli", "r/": "v/"},
                )
                posts[idx]["author"] = replace_all_occurences_in_a_string(
                    posts[idx]["author"],
                    {"subreddit": "voxsphere", "reddit": "voxpopuli", "r/": "v/"},
                )
                posts[idx]["text"] = replace_all_occurences_in_a_string(
                    posts[idx]["text"],
                    {"subreddit": "voxsphere", "reddit": "voxpopuli", "r/": "v/"},
                )
                posts[idx]["text_html"] = replace_all_occurences_in_a_string(
                    posts[idx]["text_html"],
                    {"subreddit": "voxsphere", "reddit": "voxpopuli", "r/": "v/"},
                )

                for idx2, _ in enumerate(posts[idx]["awards"]):
                    posts[idx]["awards"][idx2]["title"] = (
                        replace_all_occurences_in_a_string(
                            posts[idx]["awards"][idx2]["title"],
                            {
                                "subreddit": "voxsphere",
                                "reddit": "voxpopuli",
                                "r/": "v/",
                            },
                        )
                    )

                def fix_comments(parent_comment_list):
                    new_comments = []

                    for comment in parent_comment_list:
                        comment["author"] = replace_all_occurences_in_a_string(
                            comment["author"],
                            {
                                "subreddit": "voxsphere",
                                "reddit": "voxpopuli",
                                "r/": "v/",
                            },
                        )
                        comment["body"] = replace_all_occurences_in_a_string(
                            comment["body"],
                            {
                                "subreddit": "voxsphere",
                                "reddit": "voxpopuli",
                                "r/": "v/",
                            },
                        )
                        comment["body_html"] = replace_all_occurences_in_a_string(
                            comment["body_html"],
                            {
                                "subreddit": "voxsphere",
                                "reddit": "voxpopuli",
                                "r/": "v/",
                            },
                        )
                        comment["replies"] = fix_comments(comment["replies"])
                        new_comments.append(comment)

                    return new_comments

                posts[idx]["comments"] = fix_comments(posts[idx]["comments"])
            save_json("posts.json", posts)

    if file_name == "users.json":
        with open(file_name) as fp:
            users = json.load(fp)
            for idx, _ in enumerate(users):
                users[idx]["name"] = replace_all_occurences_in_a_string(
                    users[idx]["name"],
                    {"subreddit": "voxsphere", "reddit": "voxpopuli", "r/": "v/"},
                )
                users[idx]["public_description"] = replace_all_occurences_in_a_string(
                    users[idx]["public_description"],
                    {"subreddit": "voxsphere", "reddit": "voxpopuli", "r/": "v/"},
                )
                for idx2, _ in enumerate(users[idx]["trophies"]):
                    users[idx]["trophies"][idx2]["title"] = (
                        replace_all_occurences_in_a_string(
                            users[idx]["trophies"][idx2]["title"],
                            {
                                "subreddit": "voxsphere",
                                "reddit": "voxpopuli",
                                "r/": "v/",
                            },
                        )
                    )
                    users[idx]["trophies"][idx2]["description"] = (
                        replace_all_occurences_in_a_string(
                            users[idx]["trophies"][idx2]["description"],
                            {
                                "subreddit": "voxsphere",
                                "reddit": "voxpopuli",
                                "r/": "v/",
                            },
                        )
                    )

            save_json("users.json", users)
