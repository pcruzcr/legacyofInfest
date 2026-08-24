"""
Directional Sprite Generator + Walk Cycle Procedural
Educational: teaches 4-directional sprite logic, procedural animation
"""

from __future__ import annotations

import math

from PIL import Image

# Import from shared module (avoids circular import)
from sprite_shared import (
    _gen_player_attack,
    _gen_player_idle,
    _gen_player_walk,
)


def flip_horizontal(frames: list[Image.Image]) -> list[Image.Image]:
    return [f.transpose(Image.FLIP_LEFT_RIGHT) for f in frames]


def flip_vertical(frames: list[Image.Image]) -> list[Image.Image]:
    return [f.transpose(Image.FLIP_TOP_BOTTOM) for f in frames]


class DirectionalSpriteGenerator:
    """
    Generates 4-directional sprite sets from base generators.
    Educational: teaches directional sprite logic, mirroring, coordinate transforms.
    """
    
    def __init__(self, palette: dict):
        self.palette = palette
    
    def generate_all_directions(self) -> dict[str, dict[str, list[Image.Image]]]:
        """
        Returns:
            {
                'idle': {'south': [...], 'north': [...], 'west': [...], 'east': [...]},
                'walk': {'south': [...], 'north': [...], 'west': [...], 'east': [...]},
                'attack': {'south': [...], 'north': [...], 'west': [...], 'east': [...]},
            }
        """
        base = {
            'idle': _gen_player_idle(self.palette),
            'walk': _gen_player_walk(self.palette),
            'attack_short': _gen_player_attack(self.palette, False),
            'attack_long': _gen_player_attack(self.palette, True),
        }
        
        result = {}
        for action, south_frames in base.items():
            result[action] = {
                'south': south_frames,
                'north': self._derive_north(south_frames),
                'west': self._derive_west(south_frames) if action != 'idle' else south_frames,
                'east': []
            }
            # East = horizontal flip of West
            if action != 'idle':
                result[action]['east'] = [f.transpose(Image.FLIP_LEFT_RIGHT) 
                                           for f in result[action]['west']]
            else:
                result[action]['east'] = result[action]['west']
        
        return result
    
    def _derive_north(self, south_frames: list[Image.Image]) -> list[Image.Image]:
        """Derive North from South: vertical flip + perspective adjustments"""
        north = []
        for frame in south_frames:
            flipped = frame.transpose(Image.FLIP_TOP_BOTTOM)
            # Could add pixel adjustments for better north facing
            north.append(flipped)
        return north
    
    def _derive_west(self, south_frames: list[Image.Image]) -> list[Image.Image]:
        """Derive West from South: horizontal flip + perspective adjustments"""
        return [f.transpose(Image.FLIP_LEFT_RIGHT) for f in south_frames]


# ─── Procedural Walk Cycle Generator ───

def generate_walk_cycle(base_idle: Image.Image, frames: int = 8, 
                        stride: int = 4, bounce: int = 2) -> list[Image.Image]:
    """
    Generate walk cycle from single idle pose using procedural animation.
    Educational: teaches procedural animation, inverse kinematics basics.
    """
    from pixel_asset_generator import PAL_PLAYER, SPRITE_H, SPRITE_W, _render_pixel_art
    
    frames = []
    for i in range(frames):
        phase = i * 2 * math.pi / frames
        
        def draw(phase=phase):
            pts = []
            cx, cy = 16, 16
            
            # Body bob
            bob_y = int(math.sin(phase) * bounce)
            
            # Head/hood
            for dy in range(-10 + bob_y, 11 + bob_y):
                for dx in range(-8, 9):
                    dist = abs(dx) + abs(dy - bob_y)
                    if dist < 11:
                        ci = 2 if dy < -6 + bob_y else (3 if dy < -2 + bob_y else 4)
                        pts.append((cx+dx, cy+dy, ci))
            
            # Eyes
            pts.append((cx-3, cy-2 + bob_y, 11))
            pts.append((cx+3, cy-2 + bob_y, 11))
            
            # Torso
            for dy in range(8 + bob_y, 14 + bob_y):
                for dx in range(-6, 7):
                    if abs(dx) + abs(dy - (11 + bob_y)) < 6:
                        pts.append((cx+dx, cy+dy, 8 if dy < 11 + bob_y else 7))
            
            # Leg swing
            leg_swing = int(math.sin(phase) * stride)
            pts.append((cx-3, cy+13 + bob_y, 10))
            pts.append((cx+3 + leg_swing, cy+13 + bob_y, 10))
            
            # Arm swing (opposite to legs)
            arm_swing = int(math.sin(phase + math.pi) * stride)
            pts.append((cx-8, cy+8 + bob_y + arm_swing//2, 5))  # left arm
            pts.append((cx+8, cy+8 + bob_y - arm_swing//2, 5))  # right arm
            
            return pts
        
        img = _render_pixel_art(SPRITE_W, SPRITE_H, PAL_PLAYER, draw)
        frames.append(img)
    
    return frames


def generate_idle_animation(base_idle: Image.Image, frames: int = 4, 
                           breathe_amount: float = 0.5) -> list[Image.Image]:
    """Generate breathing idle animation from single idle frame"""
    from animation_tween import create_smooth_animation
    
    # Generate subtle variations for breathing
    keyframes = [base_idle]
    
    # Create slight scale/bob variations
    for i in range(1, 3):
        phase = i * math.pi / 2
        _scale = 1.0 + breathe_amount * 0.02 * math.sin(phase)
        # Would need scaling function
        keyframes.append(base_idle)  # Simplified
    
    return create_smooth_animation(keyframes, frames_between=frames//3)


def generate_attack_animation(base_idle: Image.Image, base_attack: list[Image.Image],
                             frames_between: int = 1) -> list[Image.Image]:
    """Create smooth attack: idle -> attack -> idle"""
    from animation_tween import create_attack_animation
    return create_attack_animation(base_idle, base_attack, frames_between=2)