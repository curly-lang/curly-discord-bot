#!/bin/bash

cd curly-lang
git checkout $1 > /dev/null
gitpull=`git pull`
if [[ "$gitpull" == "Already up to date." ]]
then
  echo "Build is up to date."
  if [[ "$2" == "--force" ]]
  then
    echo "Forcing rebuild anyway."
    touch src/main.rs
  else
    exit 1
  fi
fi
echo "Building..."
cargo build
cp target/debug/curlyc "../curly-binaries/curlyc-$1"
