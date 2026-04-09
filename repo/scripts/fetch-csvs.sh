#!/bin/bash

# Anchor paths to script location so it works from anywhere (nice try, I tested and had a feeling it should work at any directory)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

# Make temp folders and pull data
echo 'Downloading data from lab git...'
TMP_DIR=$(mktemp -d)

# Creating fitered file folder with ze date
TODAY=$(date +%Y-%m-%d)

# Ran native python3 in line since:
# 1. wasn't sure I could add curl/wget etc. to docker file (I figured we need unzip for obvious reasons)
# 2. can somehow make a seperate .py file to run this command/code

python3 -c "import urllib.request; url = 'https://raw.githubusercontent.com/joachimvandekerckhove/cogs205b-s26/9dca64e57fd88213f2422c19a8b10953a8fbfdbe/modules/02-version-control/files/data.zip'; urllib.request.urlretrieve(url,'$TMP_DIR/local_file.zip')"

#Unpack ZIP to temp directory
unzip -q "$TMP_DIR/local_file.zip" -d "$TMP_DIR/unzipped"

# Create date-named data directory
mkdir -p "$REPO_ROOT/data/$TODAY"

# Move only root-level CSVs (no subfolders)
find "$TMP_DIR/unzipped" -maxdepth 1 -name "*.csv" -exec mv -t "$REPO_ROOT/data/$TODAY" {} +

echo "Beep Boop Bop Git Hub stuff"

# Git push
git -C "$REPO_ROOT" add data/ scripts/
git -C "$REPO_ROOT" commit -m "added filtered data"
git -C "$REPO_ROOT" pull --rebase origin main
git -C "$REPO_ROOT" push origin main

echo "File filtered & folder '$TODAY' created."

# Remove temp directory
rm -rf "$TMP_DIR"

echo "We done :3"