#!/usr/bin/env bash

cd $( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )/.. || exit


VERSION=$(ls -v /Users/ck/Library/Preferences/Ableton | grep 'Live 11.2.11' |  sed -e 's/Live 11\.2 \.//'  |sort -n | tail -n1)
echo "using Version: $VERSION"
tail -f "/Users/ck/Library/Preferences/Ableton/$VERSION/Log.txt" | grep -v "Python: INFO:_Framework.ControlSurface"