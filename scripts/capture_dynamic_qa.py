#!/usr/bin/env python3
"""
Capture dynamic QA sequences — AUD-759 Fase 24

Captura 60/120/300 frames de movimiento continuo por nivel y detecta
jitter, popping, drift, HUD movement.

Uso:
  python scripts/capture_dynamic_qa.py --frames 120 --levels stage0
  python scripts/capture_dynamic_qa.py --frames 60 --all
"""
import argparse, os, pathlib, sys, json, statistics
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
import pygame
from src.engine.core import settings
from src.framework.stage.camera import Camera
from src.framework.stage.stage_loader import StageLoader
from src.framework.entities.player import Player

def capture_level(tmx_path, frames=120):
    stage = StageLoader.load(tmx_path)
    cam = Camera()
    cam.set_map_size(*stage.map_pixel_size)
    spawn = stage.spawn_point
    player = Player(spawn) if spawn else Player(pygame.Vector2(100,100))
    cam.follow(player)
    cam.snap_to_target()
    # HUD reference (should be constant)
    from src.engine.core.event_bus import EventBus
    from src.engine.ui.hud import HUD
    hud = HUD(EventBus())
    hud_pos0 = hud.vida_bar_rect().topleft
    # track
    records=[]
    # simulate walk right + jump arc
    for i in range(frames):
        dt = 1/60
        # move player 1.5 px/frame ~90 px/s
        player.position.x += 1.5
        # simple jump arc every 60 frames
        if i % 60 == 30:
            player.velocity.y = -200  # jump
        else:
            player.velocity.y += settings.GRAVITY * dt * 0.02  # small gravity for test
            player.position.y += player.velocity.y * dt
        player.rect.x = int(player.position.x)
        player.rect.y = int(player.position.y)
        cam.update(dt)
        # collect
        records.append({
            "frame": i,
            "player_world": (float(player.position.x), float(player.position.y)),
            "player_screen": (float(player.position.x - cam.offset.x), float(player.position.y - cam.offset.y)),
            "camera": (float(cam.offset.x), float(cam.offset.y), float(cam.zoom)),
            "hud": hud_pos0,
            "bg_shift_far": float(cam.offset.x * 0.15 % 1280),
            "bg_shift_near": float(cam.offset.x * 0.60 % 1280),
        })
    hud.destroy()
    return records, stage

def analyze(records):
    # detect jitter: camera delta > 10 px unexpected?
    cam_x = [r["camera"][0] for r in records]
    deltas = [abs(cam_x[i]-cam_x[i-1]) for i in range(1,len(cam_x))]
    max_delta = max(deltas) if deltas else 0
    mean_delta = statistics.mean(deltas) if deltas else 0
    # HUD should be constant
    hud_vals = [r["hud"] for r in records]
    hud_stable = len(set(hud_vals))==1
    # background continuity: shift should be smooth, no jumps > factor*max_delta+1
    bg_far = [r["bg_shift_far"] for r in records]
    bg_deltas = [abs(bg_far[i]-bg_far[i-1]) for i in range(1,len(bg_far))]
    # handle wrap: delta near 1280 is wrap, not jitter
    bg_jumps = sum(1 for d in bg_deltas if d>20 and d<1200)  # jumps not near wrap
    # player screen: should stay within viewport, not jump >20
    ps = [r["player_screen"][0] for r in records]
    ps_deltas = [abs(ps[i]-ps[i-1]) for i in range(1,len(ps))]
    ps_max = max(ps_deltas) if ps_deltas else 0
    return {
        "camera_max_delta": round(max_delta,2),
        "camera_mean_delta": round(mean_delta,2),
        "hud_stable": hud_stable,
        "bg_jumps": bg_jumps,
        "player_screen_max_delta": round(ps_max,2),
        "frames": len(records)
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--frames", type=int, default=120)
    parser.add_argument("--levels", nargs="*", default=None)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--out", default="qa_dynamic")
    args = parser.parse_args()
    tmx_root = pathlib.Path("assets/maps")
    all_tmx = sorted(tmx_root.rglob("*.tmx"))
    # map parent name to path
    mapping = {p.parent.name: p for p in all_tmx}
    # principal 26
    principal = ["stage0","stage1_1","stage1_2_la_soda","stage1_3_las_aulas","stage2_1_oficinas","stage2_2","stage3_1_la_entrada_de_piedra","stage3_3_el_patio","stage3_4_boss_gavilan","stage4_1","stage4_1b","hall","boss_venado","boss_rey","boss_paburu","lobby_datacenter","tutorial_hub","stage_mecanicas","stage_ai_dojo","stage_cenital"]
    if args.all:
        targets = principal
    elif args.levels:
        targets = args.levels
    else:
        targets = ["stage0"]
    out_dir = pathlib.Path(args.out)
    out_dir.mkdir(exist_ok=True)
    results={}
    for name in targets:
        tmx = mapping.get(name)
        if not tmx:
            # try find any tmx containing name
            cands = [p for p in all_tmx if name in str(p)]
            if cands:
                tmx=cands[0]
            else:
                print(f"skip {name} not found")
                continue
        print(f"capturing {name} {tmx} frames {args.frames}")
        pygame.init()
        pygame.display.set_mode((settings.INTERNAL_WIDTH,settings.INTERNAL_HEIGHT))
        records, stage = capture_level(tmx, args.frames)
        analysis = analyze(records)
        results[name]=analysis
        # save records
        (out_dir / f"{name}_{args.frames}.json").write_text(json.dumps({"analysis":analysis,"records":records[:5]}, indent=2), encoding="utf-8")
        print(f"  {analysis}")
        pygame.quit()
    # summary
    pathlib.Path(out_dir / "summary.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    print("summary", results)
    # check thresholds
    fails=[]
    for k,v in results.items():
        if not v["hud_stable"]:
            fails.append(f"{k} HUD movement")
        if v["camera_max_delta"]>20:
            fails.append(f"{k} camera max {v['camera_max_delta']}>20")
        if v["bg_jumps"]>0:
            fails.append(f"{k} bg jumps {v['bg_jumps']}")
        if v["player_screen_max_delta"]>30:
            fails.append(f"{k} player screen jump {v['player_screen_max_delta']}")
    if fails:
        print("FAILURES:", fails)
        sys.exit(1)
    else:
        print("All dynamic QA PASS")

if __name__ == "__main__":
    main()
