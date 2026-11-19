# -*- coding: utf-8 -*-
"""按词批量出画面图：本地 ComfyUI 生成 → 压缩成网页 jpg → 写回 words.json 的 image 字段。

用法：python batch_images.py [词1 词2 ...]（不给参数则处理全部缺图的词）
已有 images/<word>.jpg 的词会跳过。
"""
import io, json, os, subprocess, sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOL = 'D:/Claude/配置/.claude/tools/local_image_gen.py'
WORDS = os.path.join(ROOT, 'words.json')
IMGDIR = os.path.join(ROOT, 'images')

STYLE = '，夸张的动作和表情，明快饱和的色彩，粗描边线条，浅色简洁背景，卡通插画，画面中没有任何文字字母和水印'

SCENES = {
    'memory': '穿红黄衣服的快餐店小丑被一只大白鹅追着啄手，他抄起一个大蘑菇挡在身前，蘑菇被啄得飞出去掉进翻滚的红色熔岩池，熔岩池上方飘着许多空白小纸条',
    'ODS': '一轮巨大的卡通太阳停在传送带上方，传送带上滚出一个冒热气的饺子，一条粗蛇缠住饺子往后面的仓库里拖，仓库门口挂着空白牌子',
    'DWD': '一条长长的流水线上放着饺子，一只大乌鸦俯冲下来叼住饺子，乌鸦噎得直翻白眼，嘴里又吐出一个饺子砸在桌上，桌上摊着一叠空白小票',
    'DWS': '一个大饺子从流水线上滚下来，一只乌鸦张嘴接住，饺子顺着乌鸦的嘴滑进一条蛇的大嘴里，蛇把饺子嚼成一团',
    'ADS': '一个穿短裤的小男孩端着满满一盘食物，盘子里有苹果和饺子，他把盘子里的东西全倒进一条张着大嘴的蛇口里，蛇旁边堆着好几个空盘子',
    'DIM': '一个小弟弟抱着一盒外卖冲进快餐店门口，把立着的一排空白名牌全撞倒了，名牌散了一地',
    'builder': '一块湿布从天上盖下来压在半成品的房梁上，布底下躺着一个裹毯子的人，他伸手一推，把一个金发外国人推得栽进墙角的草丛里',
    'seller': '一个满脸横肉的大汉，从摊位上泼开的一大摊鲜红颜料里拔出两根锄头扛在肩上，身后是堆满杂货的摊位',
    'workspace': '一只乌鸦骑在一个猿人的肩膀上，猿人坐在跷跷板上被弹得飞起来，天上掉下一块手帕和一个苹果，砸进旁边一间小厕所的屋顶，远处是一间空荡荡的屋子',
    'loop': '一把锄头插在地面上的圆圈中央，锄头柄上挂着一副大眼镜，一把斧头正劈下来把眼镜劈成两半，劈出的裂缝在地上连成一个圆圈',
    'looping': '一把锄头插在地面圆圈中央，柄上挂着一副大眼镜，斧头劈开眼镜，一只鹰从眼镜的缺口里扑出来，绕着地上的圆圈飞',
    'harness': '扎双丸子头的小男孩哪吒，正把两条粗蛇套进一副带铁扣的皮质马挽具里当马骑，墙角一丛小草被吹得东倒西歪，身后的土墙上又挂着一副挽具',
}


def gen(word):
    png = os.path.join(IMGDIR, f'{word}.png')
    jpg = os.path.join(IMGDIR, f'{word}.jpg')
    scene = SCENES.get(word)
    if not scene:
        print(f'⚠️ {word}: 没有场景描述，跳过')
        return False
    print(f'→ {word} 出图…', flush=True)
    r = subprocess.run([sys.executable, '-I', TOOL, scene + STYLE,
                        '-o', png, '--size', '4:3', '--steps', '8'],
                       capture_output=True, text=True, encoding='utf-8', errors='replace')
    if r.returncode != 0 or not os.path.exists(png):
        print(f'❌ {word} 生成失败：{(r.stdout or "")[-300:]}{(r.stderr or "")[-300:]}')
        return False
    c = subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', png,
                        '-vf', 'scale=1000:-2:flags=lanczos', '-q:v', '3', jpg],
                       capture_output=True, text=True)
    if c.returncode != 0 or not os.path.exists(jpg):
        print(f'❌ {word} 压缩失败：{(c.stderr or "")[-300:]}')
        return False
    print(f'✅ {word}: {os.path.getsize(jpg)//1024} KB', flush=True)
    return True


targets = sys.argv[1:]
if not targets:
    targets = [w['word'] for w in json.load(open(WORDS, encoding='utf-8'))['words']
               if not os.path.exists(os.path.join(IMGDIR, f"{w['word']}.jpg"))]

os.makedirs(IMGDIR, exist_ok=True)
done, failed = [], []
for w in targets:
    (done if gen(w) else failed).append(w)

d = json.load(open(WORDS, encoding='utf-8'))
for x in d['words']:
    if os.path.exists(os.path.join(IMGDIR, f"{x['word']}.jpg")):
        x['image'] = f"images/{x['word']}.jpg"
json.dump(d, open(WORDS, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

print(f'\n完成 {len(done)} 张：{"、".join(done) or "无"}')
if failed:
    print(f'失败 {len(failed)} 张：{"、".join(failed)}')
print('words.json 已更新 image 字段')
