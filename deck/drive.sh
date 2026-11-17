#!/bin/bash
# Launcher for Steam ("Add a Non-Steam Game" -> this file). Setup: docs/remote-control.md.
cd "$(dirname "$0")" && exec ~/eyes-drive/bin/python drive.py "$@"
