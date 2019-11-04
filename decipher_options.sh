#!/bin/bash
#
# dump https://tesla-api.timdorr.com/vehicle/optioncodes into a txt file, then
# awk 'NR % 3 ==1 {printf $0 ","} NR%3==2 {printf $0 " "} NR % 3 == 0 { if (length($0)>0) {printf "[" $0 "]\n"} else { printf "\n"} }' options.txt > options.csv
#
cat 201*.json | grep opt | cut -d \" -f 4 | tr ',' '\n' | while read word; 
do 
	cat options.csv | grep ^$word 
done
