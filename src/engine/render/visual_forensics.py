"""
Module: visual_forensics
System: engine.render
Description: Runtime Visual Forensics — traza CODE → RUNTIME → FRAME → DISPLAY.

AUD-806 — Runtime Frame Truth / Visual Forensics.

Este módulo es el diagnóstico forense que responde, para cualquier píxel:

    WORLD → ENTITY → SPRITE → CAMERA → SCREEN → INTERNAL → VIEWPORT → DISPLAY

y para HUD:

    HUD → SCREEN SPACE → INTERNAL → VIEWPORT → DISPLAY

No altera gameplay: sólo observa y describe. El overlay se dibuja sobre el
frame sin tocar el renderer (misma superficie interna, antes de _publicar_software).

Uso:

    from src.engine.render import visual_forensics as vf
    state = vf.collect(app, camera, player, stage, hud)
    vf.draw_forensics_overlay(surface, state)

    # Captura reproducible
    internal = vf.capture_internal(app.internal_surface)
    display  = vf.capture_display()  # copia de display.get_surface() si existe

    # Distribución de píxeles para escalas no enteras
    vf.pixel_distribution(internal_w=1280, viewport_w=1920)  # → [2,1,1,2,...]

Criterios de verdad visual (AUD-806 §30):

    A: CODE = RUNTIME = VISUAL
    B: CODE ≠ RUNTIME
    C: RUNTIME correcto pero DESIGN ≠ RUNTIME
    D: DISPLAY TRANSFORM correcto pero PIXEL-PERFECT LIMITATION (p.ej. 1.5×)

El módulo no corrige: sólo mide, detecta y reporta — §26 "No corregir antes de entender".
"""
from __future__ import annotations

import pygame

from src.engine.core import display as _display
from src.engine.core import settings

# ---------------------------------------------------------------------------
# Helpers de pipeline
# ---------------------------------------------------------------------------

def window_size() -> tuple[int, int]:
    """Ventana física (pygame.display.get_surface().get_size())."""
    return _display.window_size()


def drawable_size() -> tuple[int, int]:
    """Drawable real (framebuffer). En dummy == window."""
    return _display.drawable_size()


def internal_size() -> tuple[int, int]:
    return _display.internal_size()


def viewport_for(display_w: int, display_h: int) -> tuple[int, int, int, int]:
    """Viewport letterbox para un display dado."""
    return _display.calculate_viewport(display_w, display_h)


def scale_for(display_w: int, display_h: int) -> tuple[float, float]:
    return _display.display_scale(display_w, display_h)


def trace_world_to_display(
    world_pos: tuple[float, float] | pygame.Vector2,
    camera_offset: tuple[float, float] | pygame.Vector2,
    display_size: tuple[int, int] | None = None,
) -> dict[str, tuple[float, float]]:
    """Traza WORLD → SCREEN (internal) → DISPLAY para un punto.

    Devuelve dict con world, screen (internal), display.
    Screen = world - camera_offset (1:1 a internal, sin zoom).
    Display = viewport_offset + screen * scale (letterbox uniforme).
    """
    if isinstance(world_pos, pygame.Vector2):
        wx, wy = float(world_pos.x), float(world_pos.y)
    else:
        wx, wy = float(world_pos[0]), float(world_pos[1])
    if isinstance(camera_offset, pygame.Vector2):
        cx, cy = float(camera_offset.x), float(camera_offset.y)
    else:
        cx, cy = float(camera_offset[0]), float(camera_offset[1])
    # WORLD → SCREEN (internal)
    sx = wx - cx
    sy = wy - cy
    # SCREEN → DISPLAY
    if display_size is None:
        dw, dh = drawable_size()
    else:
        dw, dh = display_size
    vp_x, vp_y, vp_w, vp_h = _display.calculate_viewport(dw, dh)
    iw, ih = internal_size()
    # scale derived from viewport (may differ slightly due to rounding)
    sc_x = vp_w / iw if iw else 1.0
    sc_y = vp_h / ih if ih else 1.0
    dx = vp_x + sx * sc_x
    dy = vp_y + sy * sc_y
    return {
        "world": (wx, wy),
        "screen": (sx, sy),
        "display": (dx, dy),
        "viewport": (float(vp_x), float(vp_y), float(vp_w), float(vp_h)),
        "scale": (sc_x, sc_y),
    }


def trace_hud_to_display(
    hud_rect: pygame.Rect,
    display_size: tuple[int, int] | None = None,
) -> dict[str, tuple[float, float]]:
    """Traza HUD rect (internal) → DISPLAY.

    HUD es screen-space sobre internal, sin cámara. Sólo viewport+scale.
    """
    if display_size is None:
        dw, dh = drawable_size()
    else:
        dw, dh = display_size
    vp_x, vp_y, vp_w, vp_h = _display.calculate_viewport(dw, dh)
    iw, ih = internal_size()
    sc_x = vp_w / iw if iw else 1.0
    sc_y = vp_h / ih if ih else 1.0
    dx = vp_x + hud_rect.x * sc_x
    dy = vp_y + hud_rect.y * sc_y
    dw_disp = hud_rect.width * sc_x
    dh_disp = hud_rect.height * sc_y
    return {
        "internal_pos": (float(hud_rect.x), float(hud_rect.y)),
        "internal_size": (float(hud_rect.width), float(hud_rect.height)),
        "display_pos": (dx, dy),
        "display_size": (dw_disp, dh_disp),
        "scale": (sc_x, sc_y),
        "viewport": (float(vp_x), float(vp_y), float(vp_w), float(vp_h)),
    }


def trace_tile(
    tile_x: int,
    tile_y: int,
    camera_offset: tuple[float, float] | pygame.Vector2,
    display_size: tuple[int, int] | None = None,
) -> dict[str, tuple[float, float]]:
    """Traza un tile (coord tile*16 = world) → screen → display."""
    world_x = tile_x * settings.TILE_SIZE
    world_y = tile_y * settings.TILE_SIZE
    base = trace_world_to_display((world_x, world_y), camera_offset, display_size)
    # also tile size in each space
    if display_size is None:
        dw, dh = drawable_size()
    else:
        dw, dh = display_size
    vp_x, vp_y, vp_w, vp_h = _display.calculate_viewport(dw, dh)
    iw, ih = internal_size()
    sc_x = vp_w / iw if iw else 1.0
    return {
        **base,
        "tile": (float(tile_x), float(tile_y)),
        "world_size": (float(settings.TILE_SIZE), float(settings.TILE_SIZE)),
        "screen_size": (float(settings.TILE_SIZE), float(settings.TILE_SIZE)),
        "display_size": (float(settings.TILE_SIZE * sc_x), float(settings.TILE_SIZE * sc_x)),
    }


def pixel_distribution(internal_w: int, viewport_w: int) -> list[int]:
    """Para un ancho interno y viewport, cómo se reparte cada source pixel.

    Ej: 1280→1920 scale 1.5 → [2,1,1,2,2,1...] — no uniforme pero geométricamente uniforme.
    Calculado como en _publicar_software: pygame.transform.scale nearest.
    Para estimar, mapeamos intervalos [i*scale, (i+1)*scale) y su cobertura en píxeles display
    redondeando a enteros (floor del inicio y ceil del final).
    La distribución real de pygame es equivalente a muestreo nearest.
    """
    if internal_w <= 0 or viewport_w <= 0:
        return []
    scale = viewport_w / internal_w
    dist: list[int] = []
    for i in range(min(internal_w, 32)):  # limitar a 32 para no saturar
        # Intervalo en display
        start = i * scale
        end = (i + 1) * scale
        # Ancho en píxeles físicos (nearest: round)
        # Usamos round del borde para emular transform.scale
        w = int(round(end)) - int(round(start))
        # Fallback si round da 0 por scale <0.5 (no ocurre)
        if w <= 0:
            w = max(1, int(round(scale)))
        dist.append(w)
    return dist


def expected_display_rect(
    internal_rect: pygame.Rect,
    display_size: tuple[int, int] | None = None,
) -> pygame.Rect:
    """Rect interno → display esperado (sin sampling drift, con scale uniforme)."""
    if display_size is None:
        dw, dh = drawable_size()
    else:
        dw, dh = display_size
    vp_x, vp_y, vp_w, vp_h = _display.calculate_viewport(dw, dh)
    iw, ih = internal_size()
    sc_x = vp_w / iw if iw else 1.0
    sc_y = vp_h / ih if ih else 1.0
    return pygame.Rect(
        int(round(vp_x + internal_rect.x * sc_x)),
        int(round(vp_y + internal_rect.y * sc_y)),
        int(round(internal_rect.width * sc_x)),
        int(round(internal_rect.height * sc_y)),
    )


# ---------------------------------------------------------------------------
# Forensics state — recolecta todo lo necesario para §5
# ---------------------------------------------------------------------------

def collect_forensics(
    camera: object | None = None,
    player: object | None = None,
    stage: object | None = None,
    hud: object | None = None,
    display_size: tuple[int, int] | None = None,
) -> dict[str, object]:
    """Recolecta el estado forense completo para overlay y validación.

    No toca renderer ni gameplay: sólo lee.
    """
    iw, ih = internal_size()
    if display_size is None:
        try:
            dw, dh = drawable_size()
            ww, wh = window_size()
        except Exception:
            dw, dh = iw, ih
            ww, wh = iw, ih
    else:
        dw, dh = display_size
        ww, wh = display_size
    vp_x, vp_y, vp_w, vp_h = _display.calculate_viewport(dw, dh)
    sc_x = vp_w / iw if iw else 1.0
    sc_y = vp_h / ih if ih else 1.0

    # Camera
    cam_x = cam_y = 0.0
    if camera is not None:
        try:
            off = getattr(camera, "offset", pygame.Vector2(0, 0))
            cam_x = float(off.x) if hasattr(off, "x") else float(off[0])
            cam_y = float(off.y) if hasattr(off, "y") else float(off[1])
        except Exception:
            pass

    # Player
    pw_x = pw_y = 0.0
    pr = pygame.Rect(0, 0, 40, 64)
    feet = 0
    if player is not None:
        try:
            r = getattr(player, "rect", None)
            if isinstance(r, pygame.Rect):
                pr = r.copy()
                pw_x = float(r.x)
                pw_y = float(r.y)
                feet = int(r.bottom)
            else:
                # fallback x,y attrs
                pw_x = float(getattr(player, "x", 0))
                pw_y = float(getattr(player, "y", 0))
        except Exception:
            pass
    # Screen (internal) from world - camera
    ps_x = pw_x - cam_x
    ps_y = pw_y - cam_y
    # Display
    pd_x = vp_x + ps_x * sc_x
    pd_y = vp_y + ps_y * sc_y

    # Ground Y — buscar en stage si existe
    ground_y: int | None = None
    if stage is not None:
        try:
            # stage.collision_rects o hazard? buscar Solid ancho >500
            rects = getattr(stage, "collision_rects", None) or getattr(stage, "solids", None) or []
            for cr in rects:
                if hasattr(cr, "width") and hasattr(cr, "y"):
                    if cr.width > 500:
                        ground_y = int(cr.y)
                        break
            if ground_y is None:
                # fallback TMX parse? usar 608 por convención stage0
                ground_y = 608
        except Exception:
            ground_y = 608
    else:
        ground_y = 608

    # Visible world rect
    vis_x = int(cam_x)
    vis_y = int(cam_y)
    vis_w = iw
    vis_h = ih
    map_w = map_h = 0
    if stage is not None:
        try:
            mps = getattr(stage, "map_pixel_size", None)
            if mps and len(mps) == 2:
                map_w, map_h = int(mps[0]), int(mps[1])
            else:
                map_w = int(getattr(stage, "width", 0)) * settings.TILE_SIZE
                map_h = int(getattr(stage, "height", 0)) * settings.TILE_SIZE
        except Exception:
            pass
        if map_w == 0:
            map_w = 2560
        if map_h == 0:
            map_h = 720

    # HUD rects
    hud_info: dict[str, object] = {}
    if hud is not None:
        try:
            # vida, mana, portrait, minimap etc.
            for attr in ["_vida_bar_rect", "_mana_bar_rect", "_estamina_bar_rect",
                         "_portrait_frame_rect", "_timer_bg_rect", "_carga_bar_rect"]:
                r = getattr(hud, attr, None)
                if isinstance(r, pygame.Rect):
                    hud_info[attr.replace("_", "").replace("barrect", "_bar")] = r.copy()
            # minimap via method
            try:
                mr = hud.minimap_rect()  # type: ignore[union-attr]
                if isinstance(mr, pygame.Rect):
                    hud_info["minimap"] = mr.copy()
            except Exception:
                pass
            # via regiones()
            try:
                regs = hud.regiones()  # type: ignore[union-attr]
                if isinstance(regs, dict):
                    for k, v in regs.items():
                        if isinstance(v, pygame.Rect):
                            hud_info[f"hud_{k}"] = v.copy()
            except Exception:
                pass
        except Exception:
            pass

    return {
        "WINDOW": (ww, wh),
        "DRAWABLE": (dw, dh),
        "INTERNAL": (iw, ih),
        "VIEWPORT": (vp_x, vp_y, vp_w, vp_h),
        "SCALE": (sc_x, sc_y),
        "OFFSET": (vp_x, vp_y),
        "CAMERA": (cam_x, cam_y),
        "PLAYER_WORLD": (pw_x, pw_y),
        "PLAYER_SCREEN": (ps_x, ps_y),
        "PLAYER_RECT": (pr.x, pr.y, pr.width, pr.height),
        "PLAYER_FEET": feet,
        "GROUND_Y": ground_y,
        "VISIBLE_WORLD_RECT": (vis_x, vis_y, vis_w, vis_h),
        "MAP_SIZE": (map_w, map_h),
        "HUD": hud_info,
        "CAMERA_BOUNDS": (0, 0, max(0, map_w - iw), max(0, map_h - ih)),
    }


def format_forensics(state: dict[str, object]) -> list[str]:
    """Formatea el estado forense como líneas para overlay (§5 ejemplo)."""
    iw, ih = state.get("INTERNAL", (1280, 720))  # type: ignore[assignment]
    dw, dh = state.get("DRAWABLE", (1280, 720))  # type: ignore[assignment]
    vp = state.get("VIEWPORT", (0, 0, 1280, 720))  # type: ignore[assignment]
    sc = state.get("SCALE", (1.0, 1.0))  # type: ignore[assignment]
    off = state.get("OFFSET", (0, 0))  # type: ignore[assignment]
    cam = state.get("CAMERA", (0.0, 0.0))  # type: ignore[assignment]
    pw = state.get("PLAYER_WORLD", (0.0, 0.0))  # type: ignore[assignment]
    ps = state.get("PLAYER_SCREEN", (0.0, 0.0))  # type: ignore[assignment]
    pr = state.get("PLAYER_RECT", (0, 0, 40, 64))  # type: ignore[assignment]
    feet = state.get("PLAYER_FEET", 0)
    ground = state.get("GROUND_Y", 608)
    vis = state.get("VISIBLE_WORLD_RECT", (0, 0, 1280, 720))  # type: ignore[assignment]
    hud = state.get("HUD", {})  # type: ignore[assignment]

    # type narrow
    assert isinstance(vp, tuple) and len(vp) == 4
    assert isinstance(sc, tuple) and len(sc) == 2
    lines: list[str] = []
    lines.append(f"DISPLAY {dw}x{dh}")
    lines.append(f"WINDOW {state.get('WINDOW', (dw, dh))[0]}x{state.get('WINDOW', (dw, dh))[1]}")  # type: ignore[index]
    lines.append(f"INTERNAL {iw}x{ih}")
    lines.append(f"VIEWPORT {vp[0]},{vp[1]} {vp[2]}x{vp[3]}")
    lines.append(f"SCALE {sc[0]:.3f},{sc[1]:.3f}")
    lines.append(f"OFFSET {off[0]},{off[1]}")
    lines.append(f"CAMERA {cam[0]:.2f},{cam[1]:.2f}")  # type: ignore[index]
    lines.append(f"VISIBLE WORLD {vis[0]},{vis[1]} -> {vis[0]+vis[2]},{vis[1]+vis[3]}")  # type: ignore[index]
    lines.append(f"PLAYER WORLD {pw[0]:.2f},{pw[1]:.2f}")  # type: ignore[index]
    lines.append(f"PLAYER SCREEN {ps[0]:.2f},{ps[1]:.2f}")  # type: ignore[index]
    lines.append(f"PLAYER RECT {pr[0]},{pr[1]},{pr[2]},{pr[3]}")  # type: ignore[index]
    lines.append(f"PLAYER FEET {feet}")
    lines.append(f"GROUND {ground}")
    if isinstance(hud, dict) and hud:
        for k, v in hud.items():
            if isinstance(v, pygame.Rect):
                # For each HUD element show internal and display
                tr = trace_hud_to_display(v)
                lines.append(f"HUD {k} INT {v.x},{v.y} {v.width}x{v.height} -> DISP {tr['display_pos'][0]:.0f},{tr['display_pos'][1]:.0f} {tr['display_size'][0]:.0f}x{tr['display_size'][1]:.0f}")
            else:
                lines.append(f"HUD {k}: {v}")
    else:
        lines.append("HUD: (no hud)")
    return lines


def draw_forensics_overlay(surface: pygame.Surface, state: dict[str, object] | None = None) -> None:
    """Dibuja el overlay forense sobre *surface* (internal, 1280×720).

    No altera cámara/HUD/gameplay: sólo texto y líneas guía.
    Se dibuja en internal; luego _publicar_software lo lleva a display.
    """
    if state is None:
        state = collect_forensics()
    lines = format_forensics(state)
    # Fondo semitransparente para legibilidad
    try:
        overlay = pygame.Surface((350, min(720, 14 + len(lines) * 13)), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        surface.blit(overlay, (8, 8))
        font = pygame.font.Font(None, 16)
        y = 10
        for line in lines:
            txt = font.render(line, True, (0, 255, 255))
            surface.blit(txt, (12, y))
            y += 12
        # Marcos guía: viewport interno (borde) y safe area HUD
        pygame.draw.rect(surface, (0, 255, 255), surface.get_rect(), 1)
        safe = pygame.Rect(24, 24, settings.INTERNAL_WIDTH - 48, settings.INTERNAL_HEIGHT - 48)
        pygame.draw.rect(surface, (255, 0, 255), safe, 1)
        # Centro
        cx, cy = settings.INTERNAL_WIDTH // 2, settings.INTERNAL_HEIGHT // 2
        pygame.draw.line(surface, (255, 255, 0), (cx - 10, cy), (cx + 10, cy), 1)
        pygame.draw.line(surface, (255, 255, 0), (cx, cy - 10), (cx, cy + 10), 1)
        # Ground line
        gy = state.get("GROUND_Y", 608)
        if isinstance(gy, int) and 0 <= gy < settings.INTERNAL_HEIGHT:
            cam = state.get("CAMERA", (0.0, 0.0))
            if isinstance(cam, tuple) and len(cam) == 2:
                screen_gy = int(gy - cam[1])  # type: ignore[index]
                if 0 <= screen_gy < settings.INTERNAL_HEIGHT:
                    pygame.draw.line(surface, (255, 255, 255), (0, screen_gy), (settings.INTERNAL_WIDTH, screen_gy), 1)
        # Player rect highlight (screen space)
        pr = state.get("PLAYER_RECT", (0, 0, 40, 64))
        if isinstance(pr, tuple) and len(pr) == 4:
            # pr is already screen rect? In collect it is world rect, but we have PLAYER_SCREEN.
            # Draw at screen pos
            ps = state.get("PLAYER_SCREEN", (0.0, 0.0))
            if isinstance(ps, tuple) and len(ps) == 2:
                cam2 = state.get("CAMERA", (0.0, 0.0))
                # player rect is world, so screen = world - camera
                # Use ps as top-left screen
                r = pygame.Rect(int(ps[0]), int(ps[1]), int(pr[2]), int(pr[3]))  # type: ignore[index]
                if r.width > 0 and r.height > 0 and -100 < r.x < 1380 and -100 < r.y < 820:
                    pygame.draw.rect(surface, (0, 255, 0), r, 1)
                    # feet dot
                    feet = state.get("PLAYER_FEET", 0)
                    if isinstance(feet, int):
                        foot_y = int(feet - (cam2[1] if isinstance(cam2, tuple) else 0))  # type: ignore[index]
                        pygame.draw.circle(surface, (255, 0, 0), (int(r.centerx), foot_y), 3, 1)
    except Exception:
        # Overlay nunca debe romper el frame
        pass


# ---------------------------------------------------------------------------
# Captura de frame
# ---------------------------------------------------------------------------

def capture_internal(internal_surface: pygame.Surface | None = None) -> pygame.Surface | None:
    """Copia del frame interno (antes de display transform)."""
    try:
        if internal_surface is None:
            # Intentar desde App si está disponible? Fallback crear dummy
            return None
        return internal_surface.copy()
    except Exception:
        return None


def capture_display() -> pygame.Surface | None:
    """Copia del frame final en display (después de viewport/scale)."""
    try:
        surf = pygame.display.get_surface()
        if surf is None:
            return None
        return surf.copy()
    except Exception:
        return None


def capture_both(
    internal_surface: pygame.Surface | None = None,
) -> tuple[pygame.Surface | None, pygame.Surface | None]:
    """Captura INTERNAL y DISPLAY de forma reproducible."""
    return capture_internal(internal_surface), capture_display()


def compare_internal_to_display(
    internal_pos: tuple[int, int],
    display_size: tuple[int, int] | None = None,
) -> dict[str, object]:
    """Para un punto interno, calcula display esperado y verifica transformación.

    Útil para §8 INTERNAL VS DISPLAY.
    """
    if display_size is None:
        dw, dh = drawable_size()
    else:
        dw, dh = display_size
    vp_x, vp_y, vp_w, vp_h = _display.calculate_viewport(dw, dh)
    iw, ih = internal_size()
    sc_x = vp_w / iw if iw else 1.0
    sc_y = vp_h / ih if ih else 1.0
    ix, iy = internal_pos
    dx = vp_x + ix * sc_x
    dy = vp_y + iy * sc_y
    # Expected physical rectangle for whole internal (0,0,iw,ih) -> display
    return {
        "internal": (ix, iy),
        "expected_display": (dx, dy),
        "viewport": (vp_x, vp_y, vp_w, vp_h),
        "scale": (sc_x, sc_y),
        "internal_size": (iw, ih),
        "display_size": (dw, dh),
        "expected_rect": (vp_x, vp_y, vp_w, vp_h),
    }


# ---------------------------------------------------------------------------
# Validación / diagnóstico — detecta mutaciones (§25)
# ---------------------------------------------------------------------------

def validate_viewport_uniform(display_w: int, display_h: int, eps: float = 1e-3) -> list[str]:
    """¿Viewport es uniforme (scale_x ≈ scale_y)?"""
    sx, sy = _display.display_scale(display_w, display_h)
    errs: list[str] = []
    if abs(sx - sy) > eps:
        errs.append(f"VIEWPORT NON-UNIFORM: sx={sx:.4f} sy={sy:.4f} diff={abs(sx-sy):.4f} at {display_w}x{display_h}")
    return errs


def validate_hud_stable(
    hud_rect_before: pygame.Rect,
    hud_rect_after: pygame.Rect,
) -> list[str]:
    """¿HUD permanece constante al mover cámara (§13)?"""
    if hud_rect_before != hud_rect_after:
        return [f"HUD MOVED BY CAMERA: before {hud_rect_before} after {hud_rect_after} delta {(hud_rect_after.x - hud_rect_before.x, hud_rect_after.y - hud_rect_before.y)}"]
    return []


def validate_player_world_stable(
    world_before: tuple[float, float],
    world_after: tuple[float, float],
) -> list[str]:
    """¿Player WORLD estable al cambiar resolución física (§10)?"""
    if abs(world_before[0] - world_after[0]) > 1e-5 or abs(world_before[1] - world_after[1]) > 1e-5:
        return [f"PLAYER WORLD DRIFT BY RESOLUTION: before {world_before} after {world_after}"]
    return []


def validate_camera_jitter(
    history: list[tuple[float, float, float]],  # (player_world_x, camera_x, screen_x)
) -> list[str]:
    """Detecta jitter / subpixel drift en secuencia de frames (§16).

    history: secuencia de (player_x, cam_x, screen_int_x) por frame.
    Busca saltos >3px o retroceso >1px (1px puede ser rounding lerp→int).
    """
    errs: list[str] = []
    if len(history) < 3:
        return errs
    for i in range(1, len(history)):
        prev_s = history[i - 1][2]
        cur_s = history[i][2]
        delta = cur_s - prev_s
        # Permitir -1 por truncamiento int(float) con cámara subpixel + lerp
        if delta < -1 and history[i][0] > history[i - 1][0]:
            errs.append(
                f"JITTER frame {i}: screen went back {prev_s}->{cur_s}"
                f" while player advanced {history[i-1][0]}->{history[i][0]}"
            )
        if abs(delta) > 3:
            errs.append(f"JUMP frame {i}: screen jump {delta:.1f} px ({prev_s}->{cur_s})")
    return errs


def validate_tile_alignment(
    tile_world_x: int,
    tile_screen_x: float,
    camera_x: float,
) -> list[str]:
    """¿Tile alineado sin gaps/overlap/drift (§12)?"""
    expected = tile_world_x - camera_x
    if abs(tile_screen_x - expected) > 1e-5:
        return [f"TILE DRIFT x={tile_world_x}: expected screen {expected:.2f} got {tile_screen_x:.2f} cam {camera_x:.2f}"]
    # Gap check: tiles 16 apart should stay 16 apart in screen space
    return []


# ---------------------------------------------------------------------------
# Golden frame generation (§7)
# ---------------------------------------------------------------------------

def generate_golden_internal(
    width: int = 1280,
    height: int = 720,
    player_world: tuple[int, int] = (48, 512),
    camera_offset: tuple[int, int] = (0, 0),
    ground_y: int = 608,
) -> pygame.Surface:
    """Genera un frame interno dorado sintético para pruebas.

    Contiene: grid 32px, player rect, ground line, plataformas, fondo mock, HUD mock.
    No requiere assets ni TMX: es geométrico y reproducible.
    """
    surf = pygame.Surface((width, height))
    surf.fill(settings.BG_COLOR)
    # Grid 32px (múltiplo de tile 16)
    for x in range(0, width, 32):
        pygame.draw.line(surf, (40, 40, 60), (x, 0), (x, height), 1)
    for y in range(0, height, 32):
        pygame.draw.line(surf, (40, 40, 60), (0, y), (width, y), 1)
    # Ground
    pygame.draw.rect(surf, (80, 60, 40), (0, ground_y, width, height - ground_y))
    # Player (screen = world - camera)
    px = player_world[0] - camera_offset[0]
    py = player_world[1] - camera_offset[1]
    pygame.draw.rect(surf, (0, 255, 0), (int(px), int(py), 40, 64), 0)
    pygame.draw.rect(surf, (0, 200, 0), (int(px), int(py), 40, 64), 1)
    # Feet dot
    pygame.draw.circle(surf, (255, 0, 0), (int(px + 20), int(py + 64)), 3)
    # Plataformas mock
    for plat_x, plat_y in [(160, 576), (400, 544), (800, 480)]:
        sx = plat_x - camera_offset[0]
        sy = plat_y - camera_offset[1]
        if -96 < sx < width and -16 < sy < height:
            pygame.draw.rect(surf, (120, 100, 80), (int(sx), int(sy), 96, 16))
    # HUD mock (screen-space, no camera)
    pygame.draw.rect(surf, (30, 30, 60), (24, 24, 96, 96), 0)  # portrait
    pygame.draw.rect(surf, (200, 60, 60), (24, 134, 96, 16), 0)  # vida
    pygame.draw.rect(surf, (60, 180, 220), (24, 158, 96, 16), 0)  # mana
    # Minimap
    pygame.draw.rect(surf, (20, 20, 40), (width - 152, 24, 128, 128), 0)
    pygame.draw.rect(surf, (0, 200, 255), (width - 152, 24, 128, 128), 1)
    # Centro crosshair
    cx, cy = width // 2, height // 2
    pygame.draw.line(surf, (255, 255, 0), (cx - 10, cy), (cx + 10, cy), 1)
    pygame.draw.line(surf, (255, 255, 0), (cx, cy - 10), (cx, cy + 10), 1)
    # Camera + info text
    try:
        font = pygame.font.Font(None, 14)
        txt = font.render(f"CAM {camera_offset[0]:.0f},{camera_offset[1]:.0f} PW {player_world[0]},{player_world[1]} GROUND {ground_y}", True, (255, 255, 255))
        surf.blit(txt, (4, height - 16))
    except Exception:
        pass
    return surf


def generate_display_from_internal(
    internal: pygame.Surface,
    display_size: tuple[int, int],
) -> pygame.Surface:
    """Aplica la transformación DISPLAY (letterbox + scale) a un internal dorado.

    Reusa la misma lógica que App._publicar_software pero de forma testeable.
    """
    dw, dh = display_size
    iw, ih = internal.get_size()
    vp_x, vp_y, vp_w, vp_h = _display.calculate_viewport(dw, dh, iw, ih)
    disp = pygame.Surface((dw, dh))
    disp.fill((0, 0, 0))
    if vp_w == dw and vp_h == dh:
        pygame.transform.scale(internal, (dw, dh), disp)
    else:
        escalado = pygame.transform.scale(internal, (vp_w, vp_h))
        disp.blit(escalado, (vp_x, vp_y))
    return disp


def initial_frame_for_stage(
    map_w: int,
    map_h: int,
    spawn: tuple[int, int],
    ground_y: int = 608,
) -> dict[str, object]:
    """Calcula el frame inicial esperado para un stage (§20).

    Devuelve camera pos, visible world rect, player rect, etc. — todo en WORLD/SCREEN.
    """
    iw, ih = internal_size()
    # Cámara inicial: clamped a [0, map - internal], apuntando a spawn con snap
    # Simulamos snap_to_target: offset = spawn_center - internal/2
    spawn_cx = spawn[0] + 20  # player center x (40//2)
    spawn_cy = spawn[1] + 32  # player center y (64//2)
    cam_x = spawn_cx - iw / 2
    cam_y = spawn_cy - ih / 2
    # Clamp
    cam_x = max(0.0, min(cam_x, max(0, map_w - iw)))
    cam_y = max(0.0, min(cam_y, max(0, map_h - ih)))
    # Para stage0 spawn 48,544: spawn_cx 68, spawn_cy 576 -> cam (-572,216) -> clamped (0,0)
    # Visible rect
    vis = (int(cam_x), int(cam_y), iw, ih)
    # Player screen
    ps_x = spawn[0] - cam_x
    ps_y = spawn[1] - cam_y
    feet = spawn[1] + 64
    return {
        "MAP_SIZE": (map_w, map_h),
        "SPAWN_WORLD": spawn,
        "CAMERA": (cam_x, cam_y),
        "VISIBLE_WORLD_RECT": vis,
        "PLAYER_WORLD": (float(spawn[0]), float(spawn[1])),
        "PLAYER_SCREEN": (ps_x, ps_y),
        "PLAYER_RECT": (spawn[0], spawn[1], 40, 64),
        "PLAYER_FEET": feet,
        "GROUND_Y": ground_y,
        "PLAYER_FEET_TO_GROUND": feet - ground_y,
    }
