#!/usr/bin/env python3
"""Generate shared item sprites: coin, key, chest, door, push block."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/"assets"/"sprites"/"shared"
OUT.mkdir(parents=True, exist_ok=True)

def save(img, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path)
    print(f"Generated {path}")

# Coin 16x16 x6 frames - ellipse squish
for i in range(6):
    img=Image.new("RGBA",(16,16),(0,0,0,0))
    d=ImageDraw.Draw(img)
    widths=[12,10,6,2,6,10][i]
    x0=(16-widths)//2
    d.ellipse([x0,2,x0+widths,14], fill=(255,230,80,255), outline=(120,100,20,255))
    if widths > 6:
        d.ellipse([x0+2,4,x0+widths-2,8], fill=(255,255,180,255))
    save(img, OUT/f"coin_{i}.png") if False else None

# Single sheet coin_anim 16x16*6
frames=[]
for i in range(6):
    img=Image.new("RGBA",(16,16),(0,0,0,0))
    d=ImageDraw.Draw(img)
    widths=[12,10,6,2,6,10][i]
    x0=(16-widths)//2
    d.ellipse([x0,2,x0+widths,14], fill=(255,230,80,255), outline=(60,50,20,255))
    if widths > 6:
        d.ellipse([x0+2,4,x0+widths-2,8], fill=(255,255,180,255))
    frames.append(img)
sheet=Image.new("RGBA",(16*6,16),(0,0,0,0))
for i,f in enumerate(frames): sheet.paste(f,(i*16,0))
sheet.save(OUT/"coin_anim.png")
print(f"Generated {OUT/'coin_anim.png'}")

# Also single coin icon for validator (expects coin.png? but use coin_anim)
# key 16x16
img=Image.new("RGBA",(16,16),(0,0,0,0))
d=ImageDraw.Draw(img)
# ring
d.ellipse([2,2,7,7], outline=(200,180,40,255), width=1)
d.ellipse([3,3,6,6], outline=(255,230,80,255))
# stem
d.rectangle([4,7,6,12], fill=(200,180,40,255))
# teeth
d.rectangle([6,9,9,10], fill=(200,180,40,255))
d.rectangle([6,11,8,12], fill=(200,180,40,255))
img.save(OUT/"key.png")
print(f"Generated {OUT/'key.png'}")
# red tint variant for red key
for name, col in [("key_red.png",(220,40,40)), ("key_blue.png",(40,120,220))]:
    im=img.copy()
    # tint: multiply
    datas=im.getdata()
    new=[]
    for r,g,b,a in datas:
        if a==0: new.append((r,g,b,a))
        else:
            # simple tint overlay
            nr = int(r*0.7 + col[0]*0.3)
            ng = int(g*0.7 + col[1]*0.3)
            nb = int(b*0.7 + col[2]*0.3)
            new.append((nr,ng,nb,a))
    im2=Image.new("RGBA", im.size); im2.putdata(new)
    im2.save(OUT/name)
    print(f"Generated {OUT/name}")

# chest closed 24x16
img=Image.new("RGBA",(24,16),(0,0,0,0))
d=ImageDraw.Draw(img)
d.rectangle([2,4,21,13], fill=(140,110,70,255), outline=(60,40,20,255))
d.rectangle([2,4,21,7], fill=(200,170,120,255), outline=(60,40,20,255))
# lock
d.rectangle([11,8,13,11], fill=(60,50,30,255))
d.ellipse([10,6,14,10], fill=(255,230,80,255), outline=(60,50,20,255))
img.save(OUT/"chest_closed.png")
print(f"Generated {OUT/'chest_closed.png'}")
# chest open
img2=Image.new("RGBA",(24,16),(0,0,0,0))
d=ImageDraw.Draw(img2)
d.rectangle([2,8,21,13], fill=(140,110,70,255), outline=(60,40,20,255))
# open lid back
d.rectangle([2,1,21,5], fill=(200,170,120,255), outline=(60,40,20,255))
# interior
d.rectangle([5,9,18,12], fill=(20,20,10,255))
# sparkle for content
d.ellipse([10,9,14,11], fill=(255,255,180,255))
img2.save(OUT/"chest_open.png")
print(f"Generated {OUT/'chest_open.png'}")
# anim 4 frames lerp lid
frames=[]
for f in range(4):
    im=Image.new("RGBA",(24,16),(0,0,0,0))
    d=ImageDraw.Draw(im)
    if f<2:
        lid_y = 4 - f*2
        d.rectangle([2,4+lid_y,21,7+lid_y], fill=(200,170,120,255), outline=(60,40,20,255))
        d.rectangle([2,8,21,13], fill=(140,110,70,255), outline=(60,40,20,255))
    else:
        lid_y = 0
        d.rectangle([2,1,21,5], fill=(200,170,120,255), outline=(60,40,20,255))
        d.rectangle([2,8,21,13], fill=(140,110,70,255), outline=(60,40,20,255))
    frames.append(im)
sheet=Image.new("RGBA",(24*4,16),(0,0,0,0))
for i,f in enumerate(frames): sheet.paste(f,(i*24,0))
sheet.save(OUT/"chest_anim.png")
print(f"Generated {OUT/'chest_anim.png'}")

# door closed 16x48
img=Image.new("RGBA",(16,48),(0,0,0,0))
d=ImageDraw.Draw(img)
d.rectangle([2,2,13,45], fill=(120,80,40,255), outline=(60,40,20,255))
# panels
d.rectangle([4,6,11,14], fill=(100,65,30,255), outline=(60,40,20,255))
d.rectangle([4,18,11,26], fill=(100,65,30,255), outline=(60,40,20,255))
d.rectangle([4,30,11,38], fill=(100,65,30,255), outline=(60,40,20,255))
# handle
d.ellipse([10,20,12,22], fill=(200,180,80,255))
img.save(OUT/"door_closed.png")
print(f"Generated {OUT/'door_closed.png'}")
# door open (frame)
img2=Image.new("RGBA",(16,48),(0,0,0,0))
d=ImageDraw.Draw(img2)
d.rectangle([2,2,13,45], outline=(60,40,20,255), width=2)
# inside dark
d.rectangle([4,4,11,43], fill=(20,20,10,255))
img2.save(OUT/"door_open.png")
print(f"Generated {OUT/'door_open.png'}")
# door cage variant (jaula) 16x48 with bars
img3=Image.new("RGBA",(16,48),(0,0,0,0))
d=ImageDraw.Draw(img3)
d.rectangle([2,2,13,45], outline=(90,90,100,255), width=2)
for x in range(4,12,3):
    d.line([(x,4),(x,43)], fill=(120,120,135,255), width=1)
img3.save(OUT/"door_cage_closed.png")
print(f"Generated {OUT/'door_cage_closed.png'}")
img4=Image.new("RGBA",(16,48),(0,0,0,0))
d=ImageDraw.Draw(img4)
d.rectangle([2,2,13,45], outline=(90,90,100,255), width=1)
img4.save(OUT/"door_cage_open.png")
print(f"Generated {OUT/'door_cage_open.png'}")

# push block 16x16
img=Image.new("RGBA",(16,16),(0,0,0,0))
d=ImageDraw.Draw(img)
d.rectangle([1,1,14,14], fill=(80,80,95,255), outline=(40,30,20,255))
# arrows
d.polygon([(5,8),(9,5),(9,11)], fill=(140,150,170,255))
d.rectangle([9,7,11,9], fill=(140,150,170,255))
img.save(OUT/"push_block.png")
print(f"Generated {OUT/'push_block.png'}")
# timed variant yellow border + clock
img2=img.copy()
d=ImageDraw.Draw(img2)
d.rectangle([1,1,14,14], outline=(255,230,80,255), width=1)
d.ellipse([10,2,14,6], fill=(255,255,255,255), outline=(0,0,0,255))
d.line([(12,4),(12,5)], fill=(0,0,0,255))
img2.save(OUT/"push_block_timed.png")
print(f"Generated {OUT/'push_block_timed.png'}")
# target plate 16x16
img3=Image.new("RGBA",(16,16),(0,0,0,0))
d=ImageDraw.Draw(img3)
d.rectangle([1,1,14,14], fill=(40,40,50,255), outline=(255,230,80,255))
d.rectangle([4,4,11,11], outline=(255,230,80,255))
d.ellipse([6,6,9,9], fill=(255,230,80,255))
img3.save(OUT/"push_target.png")
print(f"Generated {OUT/'push_target.png'}")

# coin single for fallback (first frame)
frames[0].save(OUT/"coin.png")
print(f"Generated {OUT/'coin.png'}")
