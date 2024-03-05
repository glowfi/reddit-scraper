#!/bin/bash

# Start time
start=$(date +%s)

rm errs.txt
touch errs.txt
rm ./noposts.txt

for ((i = 0; i < 100; i++)); do
	python subreddits.py && break
	echo "Retrying.."
	notify-send "Retrying subreddits..."
	echo "Retrying subreddits ${i+1} ..." >>errs.txt
	sleep 10
done

for ((i = 0; i < 100; i++)); do
	python posts.py && break
	echo "Retrying.."
	notify-send "Retrying posts..."
	echo "Retrying posts ${i+1} ..." >>errs.txt
	rm ./noposts.txt
	sleep 10
done

for ((i = 0; i < 100; i++)); do
	python users.py && break
	echo "Retrying.."
	notify-send "Retrying users..."
	echo "Retrying users ${i+1} ..." >>errs.txt
	sleep 10
done

### Split Files into chunks for easy importing
python split.py
mkdir json
mv *.json json/

### Import data into mongodb
mongosh --eval "use reddit" --eval "db.dropDatabase()"
mongosh --eval "use reddit"
mongoimport -d reddit -c subreddits --file ./subreddits_p1.json --jsonArray
mongoimport -d reddit -c posts --file ./posts_p1.json --jsonArray
mongoimport -d reddit -c users --file ./user_p1.json --jsonArray
mongoimport -d reddit -c users --file ./user_p2.json --jsonArray

# End time
end=$(date +%s)

# Calculate the duration in seconds
duration=$((end - start))

# Convert seconds to days, hours, minutes, and seconds
days=$((duration / 86400))
hours=$(((duration % 86400) / 3600))
minutes=$(((duration % 3600) / 60))
seconds=$((duration % 60))

# Display the duration
echo "####### TIME TAKEN #######"
echo ""
echo "Execution time: $days days, $hours hours, $minutes minutes, $seconds seconds"
echo ""
echo "####### TIME TAKEN #######"
