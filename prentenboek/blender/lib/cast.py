"""Gedeelde materialen voor de personages (één keer per scène aanmaken)."""
from . import mats as M

_CACHE = {}


def char_mats():
    if 'daan' in _CACHE:
        return _CACHE['daan']
    m = {
        'face': M.skin('Huid gezicht', '#f3c2a3', painted=True),
        'skin': M.skin('Huid', '#f3c2a3', painted=False),
        'lid': M.skin('Huid ooglid', '#efb99c', painted=False),
        'ear': M.skin('Huid oor', '#f4bea6', painted=False, sss=0.5),
        'eye': M.eye('Oog Daan', '#6f90b4', '#304c6c', pupil_r=0.27, iris_r=0.6),
        'lash': M.simple('Wimperlijn', '#7d5d4f', rough=0.6),
        'tongue': M.simple('Tong', '#d9706f', rough=0.35, sss=0.3),
        'cornea': M.cornea(),
        'lashes': M.hair_mat('Wimpers', melanin=0.82, redness=0.25, rough=0.35, random_color=0.1),
        'mouth_in': M.simple('Mondholte', '#5a1a1e', rough=0.5, sss=0.2),
        'teeth': M.simple('Tanden', '#f7f3ea', rough=0.25, coat=0.4),
        'hair': M.hair_mat('Haar Daan', melanin=0.035, redness=0.24, rough=0.24, radial=0.3, random_color=0.1, tint=(1.0, 0.97, 0.9), root_dark=0.022),
        'brow': M.hair_mat('Wenkbrauw Daan', melanin=0.13, redness=0.42, rough=0.4),
        'navy': M.fabric('Politieblauw', '#0d1330', rough=0.8, sheen=0.18, weave=1100, strength=0.25,
                         sheen_tint=(0.6, 0.7, 1.0)),
        'navy_dark': M.fabric('Politieblauw donker', '#0a0f26', rough=0.8, sheen=0.15, weave=1100),
        'stitch': M.simple('Stiksel', '#3a4a7e', rough=0.6),
        'gold': M.gold(),
        'silver': M.silver(),
        'gloss': M.gloss_black(),
        'belt': M.leather('Riem', '#121214', 0.42),
        'shoe': M.gloss_black('Schoen', 0.22),
        'sole': M.simple('Zool', '#2a2a2c', rough=0.7),
        'lace': M.simple('Veter', '#1b1b1d', rough=0.55),
        'radio': M.simple('Portofoon', '#151618', rough=0.4, coat=0.2, bump=0.05, bump_scale=300),
        'radio_led': M.emission('Ledje', '#3fb5ff', 20),
        'pj': M.fabric('Pyjama', '#9cc7ef', rough=0.85, sheen=0.9, weave=700, strength=0.15,
                       dots=('#f6f1df', 38.0)),
        'pj_cuff': M.fabric('Pyjama boord', '#f2c84b', rough=0.85, sheen=0.8, weave=700),
    }
    _CACHE['daan'] = m
    return m
