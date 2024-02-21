## DataScrapper for VoxPopuli

> Scrapes data from reddit

<p align="center">
    <img src="./logo.webp" />
</p>

## Data scraped

Scrapes for following data :

-   subreddits
-   posts
-   users

## Running the Script

> Installing dependencies and activating a virtual environment

```sh
pip install virtualenv
git clone https://github.com/glowfi/vox_populi_data_scrapper
cd vox_populi_data_scrapper
python -m venv env
source ./env/bin/<Choose activation script Based on your OS>
pip install -r ./requirements
```

> Edit the envTemplate and rename it into .env

**Try not to change the values everything after `POSTS_PER_SUBREDDIT` , as it is
optimized to deal with reddits rate-limiting with many api calls.
Ignore this if you are a paying customer**

```sh
username=<RedditUsername>
password=<RedditPassword>
client_id=<Get_it_from_reddit_api>
client_secret=<Get_it_from_reddit_api>
TOTAL_SUBREDDITS_PER_TOPICS=<Choose_your_desired_value>
POSTS_PER_SUBREDDIT=<Choose_your_desired_value>
TOPIC_SIZE=51
HITS_SUB=20
TIME_SUB=60
HITS_POSTS=15
TIME_POSTS=60
HITS_USERS=25
TIME_USERS=60
```

> Execute the script

```sh
./scrape.sh
```
