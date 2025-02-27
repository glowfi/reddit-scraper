#!/usr/bin/env python

import subreddits as sub
import posts as post
from utils.split import split_files

sub.run()
post.run()
split_files()
