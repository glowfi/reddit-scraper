import json


with open("./posts.json") as f:
    data = json.load(f)
    print(len(data))
