#!/bin/bash

### Import data into mongodb
# mongosh --eval "use socialmedia" --eval "db.dropDatabase()"
# mongosh --eval "use socialmedia"

# Cluster URI
# CLUSTER_URI=$(echo -e '')
# mongoimport -d socialmedia -c subreddits --file ./subreddits.json --jsonArray --uri "${CLUSTER_URI}"
# mongoimport -d socialmedia -c posts --file ./posts.json --jsonArray --uri "${CLUSTER_URI}"
# mongoimport -d socialmedia -c users --file ./users.json --jsonArray --uri "${CLUSTER_URI}"

# Local import
# mongoimport -d socialmedia -c subreddits --file ./subreddits_p1.json --jsonArray
# mongoimport -d socialmedia -c posts --file ./posts_p1.json --jsonArray
# mongoimport -d socialmedia -c users --file ./user_p1.json --jsonArray
# mongoimport -d socialmedia -c users --file ./user_p2.json --jsonArray

# mongoimport -d socialmedia -c subreddits --file ./subreddits.json --jsonArray
# mongoimport -d socialmedia -c users --file ./users.json --jsonArray
# mongoimport -d socialmedia -c posts --file ./posts.json --jsonArray
# mongoimport -d socialmedia -c awards --file ./awards.json --jsonArray
# mongoimport -d socialmedia -c trophies --file ./trophies.json --jsonArray
# mongoimport -d socialmedia -c topics --file ./topic.json --jsonArray
