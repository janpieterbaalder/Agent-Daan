"""Bouwt het prentenboek Agent Daan & Joep uit de Blender-renders.

Formaat zoals De Stip: dicht 21 x 21 cm, open 42 x 21 cm. 32 pagina's: voorkant, p. 1-30, achterkant.

    python boek/build.py                 # alles (pagina's, PDF's, website, artifact)
    python boek/build.py --bron work/pv  # met de previews (snelle storyboard-versie)
    python boek/build.py --storyboard    # alleen het storyboardblad

Uit:
- web/pages/ (1600 px) en web/pages-hd/ (2400 px), web/index.html, iconen, og.jpg
- artifact/index.html (alleen de inhoud) met artifact/pages/
- agent-daan-en-joep.pdf          bladen van 42 x 21 cm (omslag + 15 dubbele pagina's), zoals De Stip
- agent-daan-en-joep-druk.pdf     losse pagina's 21 x 21 cm met 3 mm afloop, voor de drukker
- storyboard.jpg                  alle pagina's op een rij met de tekstplaatsing
"""
import os, sys, json, hashlib, io, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)                       # prentenboek/
WEB = os.path.join(ROOT, 'web')
ART = os.path.join(ROOT, 'artifact')
FONTS = os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Microsoft', 'Windows', 'Fonts')
TITLE = 'Agent Daan & Joep'
DESC = 'Bladerboek van het papieren prentenboek Agent Daan & Joep: De koekjesboeven.'
SITE_URL = ''
PX = 2480                                         # 21 cm op 300 dpi
BLEED = 35                                        # 3 mm
N_PAGES = 32

NAVY = (24, 35, 77)
CREAM = (255, 253, 247)
GOLD = (255, 201, 60)
WHITE = (255, 255, 255)


def font(weight, size):
    f = {'body': 'MuseoSansRounded700.otf', 'bold': 'MuseoSansRounded900.otf', 'black': 'MuseoSansRounded1000.otf',
         'light': 'MuseoSansRounded500.otf'}[weight]
    return ImageFont.truetype(os.path.join(FONTS, f), size)


# ------------------------------------------------------------------ indeling
# Elk blad: links + rechts. 'spread' = één render over beide pagina's; anders per pagina een bron.
# Tekst: (tekst, x, y, grootte, stijl, opties) met x/y genormaliseerd over het hele blad (0-1).
#   stijl 'body' = leestekst, 'klank' = groot klankwoord, 'titel', 'klein'
SHEETS = [
    dict(name='omslag', spread='omslag', left=31, right=0, texts=[
        ('Agent Daan', 0.755, 0.075, 250, 'titel', dict(anchor='mm')),
        ('& Joep', 0.755, 0.17, 210, 'titel', dict(anchor='mm', fill=GOLD)),
        ('De koekjesboeven', 0.755, 0.25, 96, 'sub', dict(anchor='mm')),
        ('Wie heeft alle koekjes\nvan de bakker gepakt?\nAgent Daan en zijn aapje Joep\ngaan op zoek...', 0.06, 0.1, 82, 'body',
         dict(anchor='la', spacing=1.25)),
        ('Een prentenboek voor Daan', 0.06, 0.9, 58, 'klein', dict(anchor='ls')),
    ]),
    dict(name='titelblad', left=('patroon', 'schutblad'), right=('vignet', 'titel'), texts=[
        ('Agent Daan', 0.75, 0.14, 200, 'titel_d', dict(anchor='mm')),
        ('& Joep', 0.75, 0.235, 170, 'titel_d', dict(anchor='mm', fill=(214, 150, 20))),
        ('De koekjesboeven', 0.75, 0.83, 96, 'sub_d', dict(anchor='mm')),
    ]),
    dict(name='dit is daan', spread='sp03_dit_is_daan', texts=[
        ('Dit is Daan.', 0.06, 0.085, 118, 'body', dict(anchor='la')),
        ('En dit is Joep,\nhet aapje van Daan.', 0.94, 0.085, 118, 'body', dict(anchor='ra', align='right')),
    ]),
    dict(name='pet op', left=('render', 'p05_pet_op'), right=('render', 'p06_agent'), texts=[
        ('Daan zet zijn\npolitiepet op.', 0.04, 0.88, 112, 'body', dict(anchor='ls')),
        ('Joep krijgt ook een pet.', 0.96, 0.08, 108, 'body', dict(anchor='ra', align='right')),
        ('Nu zijn ze agent!', 0.96, 0.9, 150, 'klank', dict(anchor='rs', rot=4)),
    ]),
    dict(name='auto', spread='sp07_auto', texts=[
        ('Nie-nu,\nnie-nu!', 0.2, 0.2, 250, 'klank', dict(anchor='mm', rot=8, fill=(110, 170, 255))),
        ('Daar gaat de politieauto.', 0.05, 0.9, 112, 'body', dict(anchor='ls')),
    ]),
    dict(name='bakker', spread='sp09_bakker', texts=[
        ('Oh nee!', 0.08, 0.14, 240, 'klank', dict(anchor='lm', rot=-5)),
        ('Bij de bakker zijn\nalle koekjes weg.', 0.95, 0.89, 112, 'body', dict(anchor='rs', align='right')),
    ]),
    dict(name='kruimels', spread='sp11_kruimels', texts=[
        ('Kijk eens, kruimels!', 0.05, 0.1, 150, 'klank', dict(anchor='lm', rot=-3, fill=GOLD)),
        ('Wie heeft dat gedaan?', 0.95, 0.1, 118, 'body', dict(anchor='rm')),
    ]),
    dict(name='boom', spread='sp13_boom', texts=[
        ('Joep klimt in de boom.', 0.06, 0.9, 118, 'body', dict(anchor='ls')),
        ('Hup,', 0.66, 0.78, 170, 'klank', dict(anchor='mm', rot=6)),
        ('hup,', 0.76, 0.55, 170, 'klank', dict(anchor='mm', rot=6)),
        ('hup!', 0.86, 0.32, 190, 'klank', dict(anchor='mm', rot=6)),
    ]),
    dict(name='struik', spread='sp15_struik', texts=[
        ('Joep ziet iets.', 0.05, 0.09, 118, 'body', dict(anchor='la')),
        ('Daar, achter de struik!', 0.95, 0.9, 140, 'klank', dict(anchor='rs', rot=-3, fill=GOLD)),
    ]),
    dict(name='smul', spread='sp17_smul', texts=[
        ('Twee boeven met\neen zak vol koekjes.', 0.04, 0.09, 112, 'body', dict(anchor='la')),
        ('Smik, smak, smul!', 0.96, 0.92, 190, 'klank', dict(anchor='rs', rot=-4, fill=(255, 150, 190))),
    ]),
    dict(name='stop', spread='sp19_stop', texts=[
        ('Stop! Politie!', 0.04, 0.12, 210, 'klank', dict(anchor='lm', rot=-4, fill=(110, 170, 255))),
        ('roept Daan.', 0.05, 0.24, 108, 'body', dict(anchor='lm')),
        ('Oe-oe-aa-aa!', 0.96, 0.12, 200, 'klank', dict(anchor='rm', rot=5, fill=GOLD)),
        ('roept Joep.', 0.95, 0.24, 108, 'body', dict(anchor='rm')),
    ]),
    dict(name='sorry', left=('render', 'p21_schrik'), right=('render', 'p22_sorry'), texts=[
        ('De boeven schrikken.', 0.25, 0.92, 112, 'body', dict(anchor='ms')),
        ('‘Sorry,’ zeggen ze.\n‘We hadden zo’n honger.’', 0.75, 0.085, 108, 'body', dict(anchor='ma', align='center')),
    ]),
    dict(name='tafel', spread='sp23_tafel', texts=[
        ('Samen brengen ze\nde koekjes terug.', 0.04, 0.08, 112, 'body', dict(anchor='la')),
        ('Iedereen krijgt er één.', 0.96, 0.08, 112, 'body', dict(anchor='ra')),
        ('Joep krijgt er twee!', 0.96, 0.92, 160, 'klank', dict(anchor='rs', rot=-3, fill=GOLD)),
    ]),
    dict(name='feest', spread='sp25_feest', texts=[
        ('Goed gedaan, agent Daan!', 0.05, 0.1, 140, 'klank', dict(anchor='lm', rot=-3, fill=GOLD)),
        ('Goed gedaan, agent Joep!', 0.95, 0.1, 140, 'klank', dict(anchor='rm', rot=3, fill=GOLD)),
    ]),
    dict(name='bedtijd', spread='sp27_bedtijd', texts=[
        ('Nu is het bedtijd.', 0.665, 0.4, 112, 'body', dict(anchor='la', fill=(255, 240, 205), stroke=0, shadow=True)),
        ('Welterusten, agent Daan.\nWelterusten, Joep.', 0.665, 0.52, 104, 'body', dict(anchor='la', fill=(255, 240, 205), stroke=0, shadow=True)),
    ]),
    dict(name='einde', left=('vignet', 'colofon'), right=('patroon', 'schutblad'), texts=[
        ('Einde', 0.25, 0.2, 190, 'titel_d', dict(anchor='mm')),
    ]),
]

CHAPTERS = [['Omslag', None, 0]] + [[s['name'].capitalize(), 2 * k - 1] for k, s in enumerate(SHEETS) if k >= 1]
CHAPTER_TITLES = ['Omslag', 'Titelpagina', 'Dit is Daan', 'De politiepet', 'Nie-nu, nie-nu!', 'Bij de bakker',
                  'Kijk eens, kruimels!', 'Joep klimt in de boom', 'Achter de struik', 'Smik, smak, smul!',
                  'Stop! Politie!', 'Sorry', 'Iedereen een koekje', 'Goed gedaan!', 'Bedtijd', 'Einde']

TEXTS = [''] * N_PAGES


# ------------------------------------------------------------------ nabewerking
def post(im, bloom=0.28, vign=0.12):
    """Zachte gloed rond heldere lichten en een lichte vignettering."""
    a = np.asarray(im.convert('RGB')).astype(np.float32) / 255.0
    lum = a.max(2)
    bright = np.clip((lum - 0.82) / 0.18, 0, 1)[..., None] * a
    b = Image.fromarray((bright * 255).astype(np.uint8))
    r = max(4, im.width // 140)
    glow = np.asarray(b.filter(ImageFilter.GaussianBlur(r))).astype(np.float32) / 255.0
    glow2 = np.asarray(b.filter(ImageFilter.GaussianBlur(r * 4))).astype(np.float32) / 255.0
    a = 1 - (1 - a) * (1 - np.clip(glow * bloom + glow2 * bloom * 0.8, 0, 1))
    H, W = lum.shape
    yy, xx = np.mgrid[0:H, 0:W]
    d = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2) / math.sqrt(2)
    a *= (1 - vign * np.clip(d - 0.35, 0, 1) ** 1.6 / 0.65 ** 1.6)[..., None]
    return Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))


# ------------------------------------------------------------------ tekst
STYLES = {
    'body': dict(font='body', fill=NAVY, stroke=0.085, stroke_fill=(255, 251, 242), shadow=False),
    'klank': dict(font='black', fill=GOLD, stroke=0.11, stroke_fill=NAVY, shadow=True),
    'titel': dict(font='black', fill=WHITE, stroke=0.1, stroke_fill=NAVY, shadow=True),
    'sub': dict(font='bold', fill=WHITE, stroke=0.085, stroke_fill=NAVY, shadow=True),
    'klein': dict(font='light', fill=NAVY, stroke=0.08, stroke_fill=(255, 251, 242), shadow=False),
    'titel_d': dict(font='black', fill=NAVY, stroke=0, shadow=False),
    'sub_d': dict(font='bold', fill=(70, 80, 120), stroke=0, shadow=False),
}


def draw_text(img, text, x, y, size, style, opt):
    st = dict(STYLES[style])
    st.update({k: v for k, v in opt.items() if k in ('fill', 'stroke', 'stroke_fill', 'shadow')})
    f = font(st['font'], size)
    anchor = opt.get('anchor', 'la')
    align = opt.get('align', 'left' if anchor[0] == 'l' else 'right' if anchor[0] == 'r' else 'center')
    spacing = int(size * (opt.get('spacing', 1.18) - 1)) + 4
    sw = int(round(size * st.get('stroke', 0)))
    # tekst op een eigen laag (voor schaduw en draaiing)
    tmp = ImageDraw.Draw(Image.new('L', (8, 8)))
    bb = tmp.multiline_textbbox((0, 0), text, font=f, spacing=spacing, align=align, stroke_width=sw)
    pad = int(size * 0.6)
    bb = [int(math.floor(bb[0])), int(math.floor(bb[1])), int(math.ceil(bb[2])), int(math.ceil(bb[3]))]
    w, h = bb[2] - bb[0] + 2 * pad, bb[3] - bb[1] + 2 * pad
    layer = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.multiline_text((pad - bb[0], pad - bb[1]), text, font=f, fill=st['fill'] + (255,), spacing=spacing,
                     align=align, stroke_width=sw, stroke_fill=(st.get('stroke_fill') or NAVY) + (255,))
    if st.get('shadow'):
        alpha = layer.split()[3]
        sh = Image.new('RGBA', layer.size, (10, 14, 34, 0))
        sh.putalpha(alpha.filter(ImageFilter.GaussianBlur(size * 0.09)).point(lambda v: int(v * 0.75)))
        sh2 = Image.new('RGBA', layer.size, (10, 14, 34, 0))
        sh2.putalpha(alpha.filter(ImageFilter.GaussianBlur(size * 0.35)).point(lambda v: int(v * 0.45)))
        base = Image.new('RGBA', layer.size, (0, 0, 0, 0))
        base.alpha_composite(sh2)
        off = Image.new('RGBA', layer.size, (0, 0, 0, 0))
        off.paste(sh, (int(size * 0.03), int(size * 0.05)))
        base.alpha_composite(off)
        base.alpha_composite(layer)
        layer = base
    rot = opt.get('rot', 0)
    if rot:
        layer = layer.rotate(rot, resample=Image.BICUBIC, expand=True)
    W, H = img.size
    px, py = x * W, y * H
    lw, lh = layer.size
    ax = {'l': pad, 'm': lw / 2, 'r': lw - pad}[anchor[0]]
    ay = {'a': pad, 't': pad, 'm': lh / 2, 's': lh - pad, 'b': lh - pad, 'd': lh - pad}[anchor[1]]
    img.alpha_composite(layer, (int(px - ax), int(py - ay)))


# ------------------------------------------------------------------ pagina's maken
def load(src, name):
    p = os.path.join(src, name + '.png')
    if not os.path.exists(p):
        p = os.path.join(src, name + '.jpg')
    return Image.open(p)


def fit(im, w, h):
    """Schaal en snijd het midden uit naar w x h."""
    s = max(w / im.width, h / im.height)
    im = im.resize((max(w, round(im.width * s)), max(h, round(im.height * s))), Image.LANCZOS)
    x0, y0 = (im.width - w) // 2, (im.height - h) // 2
    return im.crop((x0, y0, x0 + w, y0 + h))


def paper(w, h, tone=CREAM):
    a = np.full((h, w, 3), tone, np.float32)
    rng = np.random.default_rng(1)
    n = rng.normal(0, 2.2, (h // 4 + 1, w // 4 + 1))
    n = np.asarray(Image.fromarray(n.astype(np.float32)).resize((w, h), Image.BILINEAR))
    a += n[..., None]
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def page_source(src, kind, name, w, h):
    if kind == 'render':
        return post(fit(load(src, name).convert('RGB'), w, h))
    if kind == 'patroon':
        return fit(load(src, name).convert('RGB'), w, h)
    if kind == 'vignet':
        base = paper(w, h).convert('RGBA')
        v = load(src, name).convert('RGBA')
        v = fit(v, int(w * 0.78), int(w * 0.78))
        base.alpha_composite(v, ((w - v.width) // 2, int(h * 0.18)))
        return base.convert('RGB')
    raise ValueError(kind)


def build_sheet(src, sh, scale=1.0, bleed=BLEED):
    """Geeft het blad als (2*PX + 2*bleed) x (PX + 2*bleed) RGBA, tekst erop."""
    W, H = int((2 * PX + 2 * bleed) * scale), int((PX + 2 * bleed) * scale)
    if 'spread' in sh:
        im = post(fit(load(src, sh['spread']).convert('RGB'), W, H))
    else:
        im = Image.new('RGB', (W, H), CREAM)
        half = W // 2
        for side, key in ((0, 'left'), (1, 'right')):
            kind, name = sh[key]
            pg = page_source(src, kind, name, half, H)
            im.paste(pg, (side * half, 0))
    im = im.convert('RGBA')
    # tekst wordt gemeten binnen het snijformaat
    inner = im.crop((int(bleed * scale), int(bleed * scale), W - int(bleed * scale), H - int(bleed * scale)))
    ts = PX / 2480
    for (t, x, y, size, style, opt) in sh['texts']:
        draw_text(inner, t, x, y, int(size * scale * ts), style, opt)
    im.paste(inner, (int(bleed * scale), int(bleed * scale)))
    return im.convert('RGB')


def page_number(img, n, side):
    if n in (0, 1, 2, 29, 30, 31):
        return
    d = ImageDraw.Draw(img)
    f = font('light', int(img.width * 0.016))
    x = img.width * (0.05 if side == 0 else 0.95)
    d.text((x, img.height * 0.965), str(n), font=f, fill=(255, 255, 255), anchor='ms' if False else ('ls' if side == 0 else 'rs'),
           stroke_width=max(1, img.width // 900), stroke_fill=(30, 34, 60))


def all_pages(src):
    """Alle 32 pagina's op 2480 px (snijformaat) en de bladen met afloop."""
    pages = [None] * N_PAGES
    sheets = []
    for k, sh in enumerate(SHEETS):
        im = build_sheet(src, sh)
        sheets.append(im)
        trim = im.crop((BLEED, BLEED, BLEED + 2 * PX, BLEED + PX))
        L, R = trim.crop((0, 0, PX, PX)), trim.crop((PX, 0, 2 * PX, PX))
        if k == 0:
            pages[31], pages[0] = L, R
        else:
            pages[2 * k - 1], pages[2 * k] = L, R
            page_number(L, 2 * k - 1, 0)
            page_number(R, 2 * k, 1)
        print('blad', k, sh['name'])
    return pages, sheets


# ------------------------------------------------------------------ PDF's
def jpeg_bytes(im, q=90):
    b = io.BytesIO()
    im.save(b, 'JPEG', quality=q, optimize=True, subsampling=0)
    return b.getvalue()


def make_pdfs(pages, sheets):
    import pymupdf
    pt = 72 / 300
    # 1. bladen van 42 x 21 cm (zonder afloop), zoals De Stip
    doc = pymupdf.open()
    for k, sh in enumerate(sheets):
        trim = sh.crop((BLEED, BLEED, BLEED + 2 * PX, BLEED + PX))
        pg = doc.new_page(width=2 * PX * pt, height=PX * pt)
        pg.insert_image(pg.rect, stream=jpeg_bytes(trim, 88))
    doc.set_metadata({'title': TITLE + ' - De koekjesboeven', 'author': 'Voor Daan', 'subject': 'Prentenboek',
                      'creator': 'Blender (Cycles) + build.py'})
    doc.save(os.path.join(ROOT, 'agent-daan-en-joep.pdf'), deflate=True, garbage=3)
    # 2. losse pagina's 21 x 21 cm met 3 mm afloop (drukklaar)
    doc = pymupdf.open()
    S = PX + 2 * BLEED
    order = list(range(N_PAGES))
    for n in order:
        if n == 0:
            src = sheets[0].crop((PX + BLEED, 0, 2 * PX + 2 * BLEED, S))
        elif n == 31:
            src = sheets[0].crop((0, 0, PX + BLEED, S))
        else:
            k = (n + 1) // 2
            sh = sheets[k]
            src = sh.crop((0, 0, PX + BLEED, S)) if n % 2 == 1 else sh.crop((PX + BLEED, 0, 2 * PX + 2 * BLEED, S))
        # de rugkant heeft geen afloop in het blad: spiegel een strook van 3 mm aan
        canvas = Image.new('RGB', (S, S))
        if (n % 2 == 1) or n == 31:     # linkerpagina: rug rechts
            canvas.paste(src, (0, 0))
            strip = src.crop((src.width - BLEED, 0, src.width, S)).transpose(Image.FLIP_LEFT_RIGHT)
            canvas.paste(strip, (src.width, 0))
        else:                           # rechterpagina: rug links
            strip = src.crop((0, 0, BLEED, S)).transpose(Image.FLIP_LEFT_RIGHT)
            canvas.paste(strip, (0, 0))
            canvas.paste(src, (BLEED, 0))
        if n not in (0, 31):
            page_number_on = pages[n]
            canvas.paste(page_number_on, (BLEED, BLEED))
        pg = doc.new_page(width=S * pt, height=S * pt)
        pg.insert_image(pg.rect, stream=jpeg_bytes(canvas, 90))
        try:
            pg.set_trimbox(pymupdf.Rect(BLEED * pt, BLEED * pt, (S - BLEED) * pt, (S - BLEED) * pt))
        except Exception:
            pass
    doc.set_metadata({'title': TITLE + ' - drukbestand (21 x 21 cm, 3 mm afloop)', 'author': 'Voor Daan'})
    doc.save(os.path.join(ROOT, 'agent-daan-en-joep-druk.pdf'), deflate=True, garbage=3)


# ------------------------------------------------------------------ website en artifact
def version(folder):
    h = hashlib.sha1()
    for n in sorted(os.listdir(folder)):
        st = os.stat(os.path.join(folder, n))
        h.update(f'{n}{st.st_size}'.encode())
    return h.hexdigest()[:8]


def make_web(pages):
    names = [f'p{i:02d}.jpg' for i in range(N_PAGES)]
    for folder, size, q in (('pages', 1600, 84), ('pages-hd', 2400, 88)):
        os.makedirs(os.path.join(WEB, folder), exist_ok=True)
        for i, im in enumerate(pages):
            im.resize((size, size), Image.LANCZOS).save(os.path.join(WEB, folder, names[i]), 'JPEG', quality=q,
                                                         optimize=True, progressive=True)
    texts = list(TEXTS)
    v = version(os.path.join(WEB, 'pages'))
    body = open(os.path.join(HERE, 'book.template.html'), encoding='utf8').read()
    chapters = [[CHAPTER_TITLES[0], None, 0]] + [[CHAPTER_TITLES[k], 2 * k - 1] for k in range(1, len(SHEETS))] + \
               [['Achterkant', None, N_PAGES - 1]]

    def fill(pages_, hd):
        return (body.replace('/*PAGES*/[]', json.dumps(pages_))
                    .replace('/*HD*/[]', json.dumps(hd))
                    .replace('/*TEXTS*/[]', json.dumps(texts, ensure_ascii=False))
                    .replace('/*CHAPTERS*/[]', json.dumps(chapters, ensure_ascii=False)))

    pp = [f'pages/{n}?v={v}' for n in names]
    hd = [f'pages-hd/{n}?v={v}' for n in names]
    content = fill(pp, hd)
    head = f'''<!doctype html>
<html lang="nl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="robots" content="noindex, nofollow">
<meta name="description" content="{DESC}">
<meta name="theme-color" content="#ece8e0" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#11152a" media="(prefers-color-scheme: dark)">
<meta property="og:type" content="book">
<meta property="og:title" content="{TITLE}">
<meta property="og:description" content="{DESC}">
<meta property="og:image" content="og.jpg">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" type="image/png" href="favicon.png">
<link rel="apple-touch-icon" href="apple-touch-icon.png">
<link rel="manifest" href="manifest.webmanifest">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="{TITLE}">
<link rel="preload" as="image" href="{pp[0]}">
<style>html{{box-sizing:border-box;padding-top:env(safe-area-inset-top,0px)}}body{{margin:0;font:14px system-ui,sans-serif}}img{{max-width:100%}}[hidden]{{display:none!important}}</style>
'''
    title_end = content.index('</title>') + len('</title>')
    title, rest = content[:title_end], content[title_end:]
    rest = rest.replace('<meta name="claude:viewport-fit-sides" content="cover">\n', '')
    style_end = rest.index('</style>') + len('</style>')
    html = head + title + rest[:style_end] + '\n</head>\n<body>\n' + rest[style_end:].lstrip() + '\n</body>\n</html>\n'
    open(os.path.join(WEB, 'index.html'), 'w', encoding='utf8').write(html)
    manifest = {'name': TITLE, 'short_name': 'Agent Daan', 'start_url': './', 'scope': './', 'display': 'standalone',
                'orientation': 'any', 'background_color': '#ece8e0', 'theme_color': '#18234d', 'lang': 'nl',
                'icons': [{'src': 'icon-192.png', 'sizes': '192x192', 'type': 'image/png'},
                          {'src': 'icon-512.png', 'sizes': '512x512', 'type': 'image/png'}]}
    json.dump(manifest, open(os.path.join(WEB, 'manifest.webmanifest'), 'w', encoding='utf8'), indent=1, ensure_ascii=False)
    json.dump({'cleanUrls': True, 'headers': [
        {'source': '/(.*)', 'headers': [{'key': 'X-Robots-Tag', 'value': 'noindex, nofollow'}]},
        {'source': '/pages/(.*)', 'headers': [{'key': 'Cache-Control', 'value': 'public, max-age=31536000, immutable'}]},
        {'source': '/pages-hd/(.*)', 'headers': [{'key': 'Cache-Control', 'value': 'public, max-age=31536000, immutable'}]}]},
        open(os.path.join(WEB, 'vercel.json'), 'w'), indent=1)
    open(os.path.join(WEB, 'robots.txt'), 'w').write('User-agent: *\nDisallow: /\n')
    # pictogrammen: Joep van de titelpagina; deelafbeelding: de opengeslagen omslag
    cover = pages[2]
    W = cover.width
    sq = cover.crop((int(W * 0.25), int(W * 0.22), int(W * 0.75), int(W * 0.72)))
    for s_, fn in ((180, 'apple-touch-icon.png'), (192, 'icon-192.png'), (512, 'icon-512.png'), (48, 'favicon.png')):
        sq.resize((s_, s_), Image.LANCZOS).save(os.path.join(WEB, fn), optimize=True)
    spread = Image.new('RGB', (2 * PX, PX))
    spread.paste(pages[31], (0, 0))
    spread.paste(pages[0], (PX, 0))
    og = Image.new('RGB', (1200, 630), (236, 232, 224))
    s2 = spread.resize((1130, 565), Image.LANCZOS)
    og.paste(s2, (35, 32))
    og.save(os.path.join(WEB, 'og.jpg'), 'JPEG', quality=86, optimize=True)
    # artifact: alleen de inhoud, pagina's als losse bestanden ernaast
    os.makedirs(os.path.join(ART, 'pages'), exist_ok=True)
    for n in names:
        Image.open(os.path.join(WEB, 'pages', n)).save(os.path.join(ART, 'pages', n), 'JPEG', quality=82, optimize=True,
                                                        progressive=True)
    open(os.path.join(ART, 'index.html'), 'w', encoding='utf8').write(fill([f'pages/{n}' for n in names], []))
    print('website klaar, versie', v)


def storyboard(pages, out):
    """Alle bladen klein op een rij (met tekst), als overzicht."""
    th = 330
    rows = []
    f = font('bold', 26)
    for k in range(len(SHEETS)):
        if k == 0:
            L, R = pages[31], pages[0]
        else:
            L, R = pages[2 * k - 1], pages[2 * k]
        im = Image.new('RGB', (2 * th + 8, th + 44), (236, 232, 224))
        im.paste(L.resize((th, th), Image.LANCZOS), (4, 40))
        im.paste(R.resize((th, th), Image.LANCZOS), (th + 4, 40))
        lbl = 'omslag (achter | voor)' if k == 0 else f'p. {2 * k - 1}-{2 * k}  {CHAPTER_TITLES[k]}'
        ImageDraw.Draw(im).text((8, 8), lbl, font=f, fill=(24, 35, 77))
        rows.append(im)
    cols = 3
    W = cols * rows[0].width + (cols + 1) * 16
    H = math.ceil(len(rows) / cols) * (rows[0].height + 16) + 16 + 90
    sheet = Image.new('RGB', (W, H), (250, 248, 243))
    d = ImageDraw.Draw(sheet)
    d.text((16, 22), 'Agent Daan & Joep - storyboard (beeld, uitsnede en plek van de tekst)', font=font('black', 44),
           fill=(24, 35, 77))
    for i, im in enumerate(rows):
        sheet.paste(im, (16 + (i % cols) * (im.width + 16), 90 + (i // cols) * (im.height + 16)))
    sheet.save(out, 'JPEG', quality=88)
    print('storyboard', out)


def main():
    src = os.path.join(ROOT, 'renders')
    if '--bron' in sys.argv:
        src = os.path.abspath(sys.argv[sys.argv.index('--bron') + 1])
    global PX, BLEED
    if '--klein' in sys.argv:
        PX, BLEED = 620, 9
    pages, sheets = all_pages(src)
    storyboard(pages, os.path.join(ROOT, 'storyboard.jpg' if '--storyboard' in sys.argv or '--klein' not in sys.argv else 'storyboard.jpg'))
    if '--storyboard' in sys.argv:
        return
    make_pdfs(pages, sheets)
    make_web(pages)


if __name__ == '__main__':
    main()
