#!/bin/bash
for PROC in $(pgrep sumo)
do
    USE="$(echo ps -p PROC -pcpu | awk 'FNR == 2 {print}')"
    if [ "$USE" != "0" ]
    then
      renice -20 "$PROC"
    fi
done

