# -*- coding: utf-8 -*-
"""把 05-英文学习 的 index.html + words.json + images/ 同步到 xuanyunz.com/english/

用法：python sync.py
加完词之后跑一次即可。中文字符路径的 scp 在 Windows 上不稳定，先拷到临时 ASCII 目录再传。
images/ 只传 .jpg（页面用的），源 .png 留在本地不传。
"""
import io, os, shutil, subprocess, sys, tempfile

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

SRC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KEY = r'C:/Users/ROG/.ssh/id_ed25519_caa_oa'
HOST = 'root@121.41.116.103'
DST = '/var/www/xuanyunz.com/english/'
FILES = ['index.html', 'words.json']

stage = os.path.join(tempfile.gettempdir(), 'en_sync_stage')
os.makedirs(os.path.join(stage, 'images'), exist_ok=True)

for f in FILES:
    src = os.path.join(SRC, f)
    if not os.path.exists(src):
        sys.exit(f'缺少文件：{src}')
    shutil.copy2(src, os.path.join(stage, f))

# 页面用的图：只取 jpg
img_src = os.path.join(SRC, 'images')
imgs = []
if os.path.isdir(img_src):
    for f in sorted(os.listdir(img_src)):
        if f.lower().endswith(('.jpg', '.jpeg', '.webp', '.svg')):
            shutil.copy2(os.path.join(img_src, f), os.path.join(stage, 'images', f))
            imgs.append(f)

paths = [os.path.join(stage, f) for f in FILES]
r = subprocess.run(['scp', '-o', 'ConnectTimeout=15', '-i', KEY, *paths, f'{HOST}:{DST}'],
                   capture_output=True, text=True)
if r.returncode != 0:
    sys.exit('scp 失败：' + (r.stderr or ''))

if imgs:
    # 远端先建 images 目录再传图
    subprocess.run(['ssh', '-o', 'ConnectTimeout=15', '-i', KEY, HOST, f'mkdir -p {DST}images'],
                   capture_output=True, text=True)
    ipaths = [os.path.join(SRC, 'images', f) for f in imgs]
    r2 = subprocess.run(['scp', '-o', 'ConnectTimeout=15', '-i', KEY, *ipaths,
                         f'{HOST}:{DST}images/'], capture_output=True, text=True)
    if r2.returncode != 0:
        sys.exit('图片 scp 失败：' + (r2.stderr or ''))

# 校验线上
import urllib.request
for f in FILES:
    url = f'https://xuanyunz.com/english/{f}'
    try:
        code = urllib.request.urlopen(url, timeout=15).getcode()
    except Exception as e:
        code = f'ERR {e}'
    print(f'{url}  {code}')

print('[done] 已同步到', DST)
