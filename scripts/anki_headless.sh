#!/usr/bin/env bash
/usr/bin/Xvfb :99 -screen 0 1600x1600x24
DISPLAY=:99 /usr/bin/anki
