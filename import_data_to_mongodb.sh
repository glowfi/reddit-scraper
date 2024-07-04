#!/bin/bash

### Import data into mongodb
# mongosh --eval "use reddit" --eval "db.dropDatabase()"
# mongosh --eval "use reddit"

# Cluster URI
# CLUSTER_URI=$(echo -e '')
# mongoimport -d socialmedia -c subreddits --file ./subreddits.json --jsonArray --uri "${CLUSTER_URI}"
# mongoimport -d socialmedia -c posts --file ./posts.json --jsonArray --uri "${CLUSTER_URI}"
# mongoimport -d socialmedia -c users --file ./users.json --jsonArray --uri "${CLUSTER_URI}"

# Local import
# mongoimport -d reddit -c subreddits --file ./subreddits_p1.json --jsonArray
# mongoimport -d reddit -c posts --file ./posts_p1.json --jsonArray
# mongoimport -d reddit -c users --file ./user_p1.json --jsonArray
# mongoimport -d reddit -c users --file ./user_p2.json --jsonArray
