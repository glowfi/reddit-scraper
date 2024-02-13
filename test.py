import json


with open("./subreddits.json") as f:
    data = json.load(f)
    c = 0

    final = []

    for i in data:
        if not data[i]:
            final.append(i.replace("and", " and "))
        else:
            final.append(i)

final.sort()


for i in final:
    print(f"'{i}',")
