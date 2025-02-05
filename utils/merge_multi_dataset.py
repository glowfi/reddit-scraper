import json
import glob
import sys

file_names = [
    "topic.json",
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
            and file_name != "topic.json"
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

for directory in glob.glob(f"{multi_dataset_location}/*"):
    for file_name in file_names:
        final = []
        for file in glob.glob(f"{directory}/*"):
            if file.lower().find(file_name.lower()) != -1:
                with open(file) as fp:
                    data = json.load(fp)
                    if file_name == "subreddits.json":
                        for topic in data:
                            for subreddit in data[topic]:
                                final.append(subreddit)
                    elif file_name == "topic.json":
                        for topic in data:
                            for t in data[topic]:
                                final.append({"topic": t})
                    else:
                        final = [*final, *data]
        res = handleOthers(final, file_name)
        with open(f"{file_name}", "w") as fp:
            json.dump(res, fp)
