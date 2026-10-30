# 相棒イラスト（画像生成AIの緑背景 #00FF00）を透過・サイズ統一して pomo/pets/<種類>/<品種>/<名前>.webp に書き出す
#   python3 tools/pets_process.py <元画像フォルダ（dog_shiba/0.png, 3_happy.png …）> pomo/pets
# 足元を下から8%の位置にそろえ、成長段階ごとの大きさを揃える。機嫌の絵（3_happy など）は同じ段階の基本の絵と同じ縮尺。
import sys, os, re
import numpy as np
from PIL import Image

OUT = 512
HEIGHT = {'0': 0.40, '1': 0.56, '2': 0.66, '3': 0.76, '4': 0.78}   # character height / canvas, per stage
BASE = 0.92                                                         # baseline (feet) from the top

def key(path):
    a = np.asarray(Image.open(path).convert('RGB')).astype(np.float32)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    gx = g - np.maximum(r, b)                                        # greenness
    alpha = np.clip(1 - (gx - 40) / 100, 0, 1)
    g = np.minimum(g, np.maximum(r, b) + 8)                          # remove green spill on the outline
    im = Image.fromarray(np.dstack([r, g, b, alpha * 255]).clip(0, 255).astype(np.uint8), 'RGBA')
    bb = im.getchannel('A').point(lambda v: 255 if v > 24 else 0).getbbox()
    return im.crop(bb)

def place(im, scale):
    w, h = max(1, round(im.width * scale)), max(1, round(im.height * scale))
    im = im.resize((w, h), Image.LANCZOS)
    c = Image.new('RGBA', (OUT, OUT), (0, 0, 0, 0))
    c.alpha_composite(im, ((OUT - w) // 2, round(OUT * BASE) - h))
    return c

src, dst = sys.argv[1], sys.argv[2]
for d in sorted(os.listdir(src)):
    kind, breed = d.split('_', 1)
    files = {os.path.splitext(f)[0]: os.path.join(src, d, f) for f in os.listdir(os.path.join(src, d))}
    cut = {k: key(p) for k, p in files.items()}
    scales = {}
    for k in sorted(cut):
        stage = k.split('_')[0]
        if '_' not in k: scales[stage] = OUT * HEIGHT[stage] / cut[k].height
    os.makedirs(os.path.join(dst, kind, breed), exist_ok=True)
    for k, im in cut.items():
        stage = k.split('_')[0]
        s = scales.get(stage) or OUT * HEIGHT[stage] / im.height
        out = os.path.join(dst, kind, breed, k + '.webp')
        place(im, s).save(out, 'WEBP', quality=88, method=6)
        print(out, os.path.getsize(out) // 1024, 'KB')
