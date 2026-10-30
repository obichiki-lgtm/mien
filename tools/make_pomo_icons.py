# Pomo Timer のアプリアイコン（PWA / ホーム画面用）を生成する: python3 tools/make_pomo_icons.py
from PIL import Image, ImageDraw

import json, os

# テーマカラー（アプリの --acc-* ライト版）。tomato は既存のパス（icons/ 直下・manifest.webmanifest）を使う
ACCENTS = {'tomato': '#D9452B', 'ocean': '#2268B8', 'forest': '#2E8656', 'grape': '#7448BF', 'sumi': '#26302C'}
W = (255, 255, 255)
ACC = None

def draw(size, maskable=False, bg_full=False):
    s = 4  # supersample
    n = size * s
    im = Image.new('RGBA', (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    if maskable or bg_full:
        d.rectangle([0, 0, n, n], fill=ACC)
    else:
        d.rounded_rectangle([0, 0, n - 1, n - 1], radius=int(n * 0.22), fill=ACC)
    k = 0.62 if maskable else 0.78        # maskable: keep inside the safe zone
    c, r = n / 2, n * k / 2 * 0.80
    cy = c + n * 0.03
    w = int(n * 0.075 * (k / 0.78))
    d.ellipse([c - r, cy - r, c + r, cy + r], outline=W, width=w)          # dial
    d.pieslice([c - r * 0.62, cy - r * 0.62, c + r * 0.62, cy + r * 0.62], -90, 60, fill=W)  # elapsed
    lw, lh = r * 0.5, r * 0.28                                             # leaf
    d.ellipse([c - lw, cy - r - lh * 1.15, c, cy - r + lh * 0.2], fill=W)
    d.ellipse([c, cy - r - lh * 1.15, c + lw, cy - r + lh * 0.2], fill=W)
    return im.resize((size, size), Image.LANCZOS)

base = json.load(open('pomo/manifest.webmanifest', encoding='utf-8'))
for name, hexc in ACCENTS.items():
    ACC = tuple(int(hexc[i:i + 2], 16) for i in (1, 3, 5))
    d = 'pomo/icons/' if name == 'tomato' else f'pomo/icons/{name}/'
    os.makedirs(d, exist_ok=True)
    draw(192).save(d + 'icon-192.png')
    draw(512).save(d + 'icon-512.png')
    draw(512, maskable=True).save(d + 'maskable-512.png')
    draw(180, bg_full=True).convert('RGB').save(d + 'apple-touch-icon.png')
    if name != 'tomato':
        m = dict(base, theme_color=hexc)
        m['icons'] = [dict(i, src=i['src'].replace('icons/', f'icons/{name}/', 1)) for i in base['icons']]
        with open(f'pomo/manifest-{name}.webmanifest', 'w', encoding='utf-8') as f:
            json.dump(m, f, ensure_ascii=False, indent=2)
            f.write('\n')
print('ok')
