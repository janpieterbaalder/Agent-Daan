"""Start een scène in Blender (achtergrond).

    blender -b --factory-startup -P blender/run.py -- <scène> <uitvoer.png> [--q preview|final] [--w 1200]
"""
import sys, os, importlib, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
scene, out = argv[0], os.path.abspath(argv[1])
opts = {'q': 'preview', 'w': None, 'samples': None}
i = 2
while i < len(argv):
    if argv[i].startswith('--'):
        opts[argv[i][2:]] = argv[i + 1]
        i += 2
    else:
        i += 1

mod = importlib.import_module('scenes.' + scene)
t0 = time.time()
mod.main(out, opts)
print(f'KLAAR {scene} in {time.time() - t0:.0f}s -> {out}')
