#!/bin/bash

# Anchor paths to script location so it works from anywhere 
# taking this from fetch-csvs script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

# Check and/or install python package dependencies 
echo "Checking dependencies..."

PACKAGES=("numpy" "matplotlib" "scipy" "pandas")
MISSING=()

for pkg in "${PACKAGES[@]}"; do
    if python3 -c "import $pkg" 2>/dev/null; then
        echo "  $pkg is already installed"
    else
        echo "  $pkg is missing"
        MISSING+=("$pkg")
    fi
done

if [ ${#MISSING[@]} -ne 0 ]; then
    echo ""
    echo "Installing missing packages: ${MISSING[*]}"
    pip3 install "${MISSING[@]}" --break-system-packages
else
    echo ""
    echo "All dependencies already satisfied, skipping install."
fi

# cd into the folder so plots save here alongside the scripts 
cd "$SCRIPT_DIR"

# Run the Python script 
echo ""
echo "Running signal_detection.py..."
python3 "$SCRIPT_DIR/signal_detection.py"

# Confirm contents 
echo ""
echo "Contents of 'assignment 3':"
ls -lh "$SCRIPT_DIR/"

# Push to git
echo "Beep Boop Bop Git Hub stuff"
echo ""
echo "Pushing to git..."
echo ""
git -C "$REPO_ROOT" add assignment3/
git -C "$REPO_ROOT" commit -m "Add assignment 3 files"
git -C "$REPO_ROOT" pull --rebase origin main
git -C "$REPO_ROOT" push origin main

echo ""
echo "We're done! :3 Assignment 3 files pushed to git"