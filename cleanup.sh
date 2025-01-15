bash -c 'fd . | grep *__pycache__/ | xargs -I "{}" rm -rf "{}"'
rm -rf request_status.txt
rm -rf api_requests.log
rm -rf subreddits.json
rm -rf posts.json
rm -rf users.json
