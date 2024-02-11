#!/bin/bash

if [[ "$1" = "s" ]]; then
	./subreddits_sync.py
	./posts_sync.py
else
	./subreddits.py
	./posts.py
fi
