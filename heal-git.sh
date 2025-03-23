#! /bin/bash

rm -rf .git
git init
git remote add origin git@bitbucket.org:tsdaemon/pathfinder-eyes.git
git fetch
git reset --mixed origin/main
git branch --set-upstream-to=origin/main main