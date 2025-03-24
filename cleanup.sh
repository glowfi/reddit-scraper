#!/usr/bin/env bash

find . | grep *__pycache__/ | xargs -I "{}" rm -rf "{}"
rm -rf __pycache__
rm -rf scraper.log
rm -rf subreddits.json
rm -rf subreddits_p1.json
rm -rf posts.json
rm -rf posts_p1.json
rm -rf users.json
rm -rf users_p1.json
rm -rf users_p2.json
rm -rf awards.json
rm -rf trophies.json
