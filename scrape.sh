#!/bin/bash

start=$(date +%s.%N)

rm errs.txt
touch errs.txt
rm ./noposts.txt

for ((i = 0; i < 100; i++)); do
	./subreddits.py && break
	echo "Retrying.."
	notify-send "Retrying subreddits..."
	echo "Retrying subreddits ${i+1} ..." >>errs.txt
	sleep 10
done

for ((i = 0; i < 100; i++)); do
	./posts.py && break
	echo "Retrying.."
	notify-send "Retrying posts..."
	echo "Retrying posts ${i+1} ..." >>errs.txt
	rm ./noposts.txt
	sleep 10
done

for ((i = 0; i < 100; i++)); do
	./users.py && break
	echo "Retrying.."
	notify-send "Retrying users..."
	echo "Retrying users ${i+1} ..." >>errs.txt
	sleep 10
done

end=$(date +%s.%N)

runtime=$(echo "$end - $start" | bc -l)

echo " Total Time Taken : ${runtime}"
