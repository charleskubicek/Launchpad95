#!/usr/bin/env bash

cd $( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )/.. || exit

if grep -v 'complete' ./StepSequencerComponent.py | grep 'print' > /dev/null ; then
    echo "Error: print() is not allowed, use self.log_message instead"
    exit 1
fi

#export PYTHONPATH=./app:./css:./clicker:./tests:.
export SCRIPTS_HOME="/Applications/Ableton Live 11 Suite.app/Contents/App-Resources/MIDI Remote Scripts/CK_Launchpad95"
echo "copying to ${SCRIPTS_HOME}"

#cp StepSequencerComponent.py "$SCRIPTS_HOME" && \
cp *.py "$SCRIPTS_HOME" && \
cp Settings.py "$SCRIPTS_HOME" && \
echo "Launchpad95 Deployed." || echo "Failed"
