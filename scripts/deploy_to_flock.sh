rsync -r --exclude=".idea" --exclude=".git" /Users/jasonbenn/code/worldview/. flock:/home/flock/worldview
ssh flock cp /home/flock/worldview/scripts/anki_headless.service /etc/systemd/system
