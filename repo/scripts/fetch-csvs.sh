#!/bin/bash

pwd -L

# Make temp folders and pull data
echo 'Downloading data from lab git...'
TMP_DIR=$(mktemp -d)

# Creating fitered file folder
data=$(date +%Y-%m-%d)

# Ran native python3 in line since 
# 1. wasn't sure I could add curl/wget etc. to docker file
# 2. can somehow make a seperate .py file to run this command/code

python3 -c "import urllib.request; url = 'https://raw.githubusercontent.com/joachimvandekerckhove/cogs205b-s26/9dca64e57fd88213f2422c19a8b10953a8fbfdbe/modules/02-version-control/files/data.zip'; urllib.request.urlretrieve(url,'$TMP_DIR/local_file.zip')"

unzip -q "$TMP_DIR/local_file" -d "$TMP_DIR/unzipped"

# Create filtered file directory

mkdir -p ../data/$data 
#cd ../data

find "$TMP_DIR/unzipped" -name "*.csv" -exec mv -t ../data/$data {} +

echo "File filtered & folder '$data' created."


git -C .. add data/ scripts/
git -C .. commit -m "added filtered data"
git -C .. pull --rebase origin main 
git -C .. push origin main