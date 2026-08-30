"""
Animation Tweening / Interpolation
Educational: teaches frame interpolation, easing functions, morphing
Deterministic: pure math, no randomness
"""

from __future__ import annotations

from collections.abc import Generator

import numpy as np
from PIL import Image


# Easing functions (educational: teaches animation curves)
def ease_linear(t: float) -> float:
    return t

def ease_in_quad(t: float) -> float:
    return t * t

def ease_out_quad(t: float) -> float:
    return 1 - (1 - t) * (1 - t)

def ease_in_out_quad(t: float) -> float:
    if t < 0.5:
        return 2 * t * t
    return 1 - (1 - 2 * t) * (1 - 2 * t) / 2

def ease_in_cubic(t: float) -> float:
    return t ** 3

def ease_out_cubic(t: float) -> float:
    return 1 - (1 - t) ** 3

def ease_in_out_cubic(t: float) -> float:
    if t < 0.5:
        return 4 * t ** 3
    return 1 - (-2 * t + 2) ** 3 / 2


EASING_FUNCTIONS = {
    'linear': ease_linear,
    'ease_in_quad': ease_in_quad,
    'ease_out_quad': ease_out_quad,
    'ease_in_out_quad': ease_in_out_quad,
    'ease_in_cubic': ease_in_cubic,
    'ease_out_cubic': ease_out_cubic,
    'ease_in_out_cubic': ease_in_out_cubic,
}


def interpolate_images(img_a: Image.Image, img_b: Image.Image, 
                       steps: int, easing: str = 'linear') -> Generator[Image.Image, None, None]:
    """
    Morph between two images using pixel-wise interpolation with easing.
    Educational: teaches pixel-wise interpolation, color space blending.
    """
    if img_a.size != img_b.size:
        raise ValueError("Images must have same dimensions")
    
    arr_a = np.array(img_a.convert('RGBA'), dtype=np.float32)
    arr_b = np.array(img_b.convert('RGBA'), dtype=np.float32)
    
    easing_fn = EASING_FUNCTIONS.get(easing, ease_linear)
    
    for i in range(steps):
        t = (i + 1) / (steps + 1)
        eased_t = easing_fn(t)
        
        interp = arr_a * (1 - eased_t) + arr_b * eased_t
        result = Image.fromarray(np.clip(interp, 0, 255).astype(np.uint8), 'RGBA')
        yield result


def create_smooth_animation(keyframes: list[Image.Image], 
                           frames_between: int = 3,
                           easing: str = 'ease_in_out_quad') -> list[Image.Image]:
    """
    Create smooth animation by interpolating between keyframes.
    Educational: teaches keyframe animation, interpolation.
    """
    if len(keyframes) < 2:
        return keyframes
    
    result = [keyframes[0]]
    for i in range(len(keyframes) - 1):
        interpolated = list(interpolate_images(
            keyframes[i], keyframes[i + 1], 
            frames_between, easing
        ))
        result.extend(interpolated)
        result.append(keyframes[i + 1])
    
    return result


def create_smooth_walk_cycle(base_idle: Image.Image, base_walk: list[Image.Image],
                            frames_between: int = 2) -> list[Image.Image]:
    """
    Create smooth walk cycle by interpolating between walk frames.
    Educational: teaches cycle smoothing, loop continuity.
    """
    if not base_walk:
        return []
    
    smoothed = []
    n = len(base_walk)
    
    for i in range(n):
        current = base_walk[i]
        
        smoothed.append(current)
        
        if frames_between > 0:
            for interp in interpolate_images(current, base_walk[(i + 1) % n], 
                                             frames_between, 'ease_in_out_quad'):
                smoothed.append(interp)
    
    return smoothed


def create_attack_animation(base_idle: Image.Image, base_attack: list[Image.Image],
                           frames_between: int = 1,
                           easing: str = 'ease_out_cubic') -> list[Image.Image]:
    """
    Create smooth attack animation from idle -> attack frames -> idle.
    Educational: teaches action animation transitions.
    """
    if not base_attack:
        return []
    
    result = [base_idle]
    
    # Idle to first attack frame
    if len(base_attack) > 0:
        for interp in interpolate_images(base_idle, base_attack[0], 
                                         frames_between=2, easing='ease_out_cubic'):
            result.append(interp)
    
    # Attack frames with smoothing between
    for i in range(len(base_attack) - 1):
        result.append(base_attack[i])
        for interp in interpolate_images(base_attack[i], base_attack[i+1], 
                                         frames_between=1, easing='ease_in_out_quad'):
            result.append(interp)
    result.append(base_attack[-1])
    
    # Last attack frame back to idle
    for interp in interpolate_images(base_attack[-1], base_idle, 
                                     frames_between=3, easing='ease_in_quad'):
        result.append(interp)
    result.append(base_idle)
    
    return result