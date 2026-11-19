# -*- coding: utf-8 -*-
"""把 images/ 里的 png 原图压成网页用的 webp + jpg 兜底。

- webp：800 宽，质量 70（页面首选，体积约为 jpg 的六成）
- jpg ：800 宽，q6（老浏览器兜底）
- 原图 png 不动，留作重出参考

用法：python compress_images.py
"""
import io, json, os, subprocess, sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMGDIR = os.path.join(ROOT, 'images')
WORDS = os.path.join(ROOT, 'words.json')
WIDTH = 800
WEBP_Q = 70
JPG_Q = 6


def size_kb(p):
    return os.path.getsize(p) // 1024


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, errors='replace')


rows = []
for f in sorted(os.listdir(IMGDIR)):
    if not f.lower().endswith('.png'):
        continue
    stem = os.path.splitext(f)[0]
    png = os.path.join(IMGDIR, f)
    webp = os.path.join(IMGDIR, stem + '.webp')
    jpg = os.path.join(IMGDIR, stem + '.jpg')

    r = run(['ffmpeg', '-y', '-loglevel', 'error', '-i', png,
             '-vf', f'scale={WIDTH}:-2:flags=lanczos', '-quality', str(WEBP_Q), webp])
    if r.returncode != 0 or not os.path.exists(webp):
        print(f'❌ {stem} webp 失败：{(r.stderr or "")[-200:]}')
        continue

    old = size_kb(jpg) if os.path.exists(jpg) else 0
    j = run(['ffmpeg', '-y', '-loglevel', 'error', '-i', png,
             '-vf', f'scale={WIDTH}:-2:flags=lanczos', '-q:v', str(JPG_Q), jpg])
    if j.returncode != 0:
        print(f'⚠️ {stem} jpg 兜底失败：{(j.stderr or "")[-200:]}')

    rows.append((stem, size_kb(png), size_kb(webp), size_kb(jpg) if os.path.exists(jpg) else 0, old))

# 页面改指向 webp
d = json.load(open(WORDS, encoding='utf-8'))
for w in d['words']:
    if os.path.exists(os.path.join(IMGDIR, w['word'] + '.webp')):
        w['image'] = f"images/{w['word']}.webp"
json.dump(d, open(WORDS, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

print(f'{"词":<10}{"原图":>8}{"webp":>8}{"jpg兜底":>9}{"旧jpg":>8}')
for s, a, b, c, o in rows:
    print(f'{s:<10}{a:>6}KB{b:>6}KB{c:>7}KB{o:>6}KB')
print(f'\n合计 webp {sum(r[2] for r in rows)} KB，jpg 兜底 {sum(r[3] for r in rows)} KB，'
      f'旧 jpg {sum(r[4] for r in rows)} KB')
print('words.json 已改为指向 .webp')
