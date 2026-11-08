#!/bin/bash
# gebruik: blender/r.sh <scène> <uitvoer.png> [--w 1200 --samples 64 --q final]
cd "$(dirname "$0")/.."
"/c/Program Files/Blender Foundation/Blender 5.1/blender.exe" -b --factory-startup -P blender/run.py -- "$@" 2>&1 | grep -E "Error|error|Traceback|File \"|KLAAR|line [0-9]+|^\w+Error" | grep -v "HIPEW\|hiprt" | head -40
