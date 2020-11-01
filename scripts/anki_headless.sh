#!/usr/bin/env bash
/usr/bin/Xvfb :99 -screen 0 1280x1024x24 >& /tmp/anki_headless_xvfb.out &
sleep 3
DISPLAY=:99 /usr/bin/anki >& /tmp/anki_headless_anki.out &
