bash -c 'fd . | grep *__pycache__/ | xargs -I "{}" rm -rf "{}"'
rm -rf posts.json
rm -rf posts_p1.json
rm -rf subreddits.json
rm -rf subreddits_p1.json
rm -rf user_p1.json
rm -rf user_p2.json
rm -rf users.json
rm -rf noposts.txt
rm -rf comments-got.txt
rm -rf comments-errs.txt
rm -rf comments-retry.txt
rm -rf comments-status.txt
rm -rf errs.txt
