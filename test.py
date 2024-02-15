import json


with open("./posts.json") as f:
    data = json.load(f)
    print(len(data))

    # for topic in data:
    #     for sreddits in data[topic]:
    #         print(topic, sreddits["title"])
