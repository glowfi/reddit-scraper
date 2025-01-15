# cat q | grep -o "data-topic.\+>\|aria-labelledby.\+>"

import re
import html
import json


def extract_info(html_string):
    res: dict[str, list[str]] = {}

    # Regular expression patterns to find aria-labelledby and data-topic
    aria_pattern = r'aria-labelledby="([^"]+)"'
    data_pattern = r'data-topic="([^"]+)"'

    # Find all occurrences of aria-labelledby
    aria_matches = re.finditer(aria_pattern, html_string)

    # Iterate over the aria-labelledby matches
    for aria_match in aria_matches:
        # Get the aria-labelledby value
        aria_value = aria_match.group(1)

        # Find the next aria-labelledby match
        next_aria_match = re.search(aria_pattern, html_string[aria_match.end() :])

        # If there is no next aria-labelledby match, set the end index to the end of the string
        if next_aria_match is None:
            end_index = len(html_string)
        else:
            end_index = aria_match.end() + next_aria_match.start()

        # Find all data-topic matches between the current aria-labelledby and the next one
        data_matches = re.findall(
            data_pattern, html_string[aria_match.end() : end_index]
        )

        # Print the aria-labelledby value and its corresponding data-topic values
        print(f"aria-labelledby: {html.unescape(aria_value).replace('title-','')}")
        res[html.unescape(aria_value).replace("title-", "")] = []
        for data_value in data_matches:
            print(f"data-topic: {html.unescape(data_value)}")
            res[html.unescape(aria_value).replace("title-", "")].append(
                html.unescape(data_value)
            )
        print("------------------------")
    return res


with open("./1", "r") as fp:
    data = fp.read()
    titleString = "aria-labelledby"
    topicString = "data-topic"
    res = extract_info(data)

    with open("./top.json", "w") as fp:
        json.dump(res, fp)
