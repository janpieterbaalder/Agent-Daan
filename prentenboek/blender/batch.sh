#!/bin/bash
# gebruik: blender/batch.sh <kwaliteit> <uitvoermap> scène...
cd "$(dirname "$0")/.."
q=$1; outdir=$2; shift 2
mkdir -p "$outdir"
for s in "$@"; do
  start=$(date +%s)
  "/c/Program Files/Blender Foundation/Blender 5.1/blender.exe" -b --factory-startup -P blender/run.py -- $s "$outdir/$s.png" --q $q > "$outdir/$s.log" 2>&1
  if grep -q "KLAAR" "$outdir/$s.log"; then echo "OK $s $(( $(date +%s) - start ))s"; else echo "FOUT $s"; grep -E "Error|Traceback|File \"|line [0-9]+" "$outdir/$s.log" | grep -v HIPEW | tail -6; fi
done
