from collections import defaultdict
import json

OLD_JSON_DATA_LOCATION = ""
NEW_JSON_DATA_LOCATION = ""

if not OLD_JSON_DATA_LOCATION or not NEW_JSON_DATA_LOCATION:
    print("Provide a valid File Location!")

files = ["awards.json", "trophies.json", "posts.json", "subreddits.json", "users.json"]


print("Started!")

# Read Old,new post Data
readDataOld = []
for file in files:
    with open(f"{OLD_JSON_DATA_LOCATION}/{file}", "r") as fp:
        readDataOld.append(json.load(fp))

readDataNew = []
for file in files:
    with open(f"{NEW_JSON_DATA_LOCATION}/{file}", "r") as fp:
        readDataNew.append(json.load(fp))


# Handle Subreddits
print("Handling Subreddits ...")
old_sreddits = []
for topic in readDataOld[3]:
    for sreddit in readDataOld[3][topic]:
        old_sreddits.append(sreddit)

new_sreddits = []
for topic in readDataNew[3]:
    for sreddit in readDataNew[3][topic]:
        new_sreddits.append(sreddit)


final_sreddits = defaultdict(list)

for sreddit in new_sreddits:
    found = False
    for old_sreddit in old_sreddits:
        if sreddit["id"] == old_sreddit["id"]:
            found = True
            break
    if not found:
        final_sreddits[sreddit["category"]].append(sreddit)


with open("subreddits.json", "w") as fp:
    json.dump(final_sreddits, fp)


# Handle Posts
print("Handling Posts ...")
idx = 0
for post_new in readDataNew[2]:
    for post_old in readDataOld[2]:
        if post_old["id"] == post_new["id"]:
            del readDataNew[2][idx]
    idx += 1

with open("posts.json", "w") as fp:
    json.dump(readDataNew[2], fp)


# Handle Users
print("Handling Users ...")
st = set()
for user in readDataNew[-1]:
    if user in readDataOld[-1]:
        st.add(user)
for key in st:
    del readDataNew[-1][key]

with open("users.json", "w") as fp:
    json.dump(readDataNew[-1], fp)

print("Done!")
