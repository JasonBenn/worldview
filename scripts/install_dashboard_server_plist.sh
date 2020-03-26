#!/usr/bin/env bash

# launchctl stop worldview_dashboard
# launchctl unload ~/Library/LaunchAgents/worldview_dashboard.plist
cp ~/code/worldview/dashboard/worldview_dashboard.plist ~/Library/LaunchAgents/
# launchctl load ~/Library/LaunchAgents/worldview_dashboard.plist
# launchctl start worldview_dashboard
# launchctl list | grep dashboard

# 15,45 7-22 * * * bash /Users/jasonbenn/code/worldview/scripts/build_dashboard.sh