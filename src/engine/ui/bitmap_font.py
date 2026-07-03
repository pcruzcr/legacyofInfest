from __future__ import annotations
import pygame
from pathlib import Path


class BitmapFont:
    """Bitmap font renderer for sprite-sheet based fonts."""

    def __init__(self, path: Path | str, char_width: int = 0, char_height: int = 0,
                 chars: str = "", first_ascii: int = 0) -> None:
        sheet = pygame.image.load(str(path))
        sheet_w, sheet_h = sheet.get_size()
        char_height = char_height or sheet_h

        if char_width > 0:
            count = sheet_w // char_width
            self._glyphs: list[pygame.Surface] = []
            for i in range(count):
                self._glyphs.append(sheet.subsurface((i * char_width, 0, char_width, char_height)))
        else:
            self._glyphs = self._auto_detect_glyphs(sheet, char_height)

        self._char_map: dict[str, tuple[pygame.Surface, int]] = {}
        if chars:
            n = min(len(chars), len(self._glyphs))
            for i in range(n):
                gw = self._glyphs[i].get_width()
                self._char_map[chars[i]] = (self._glyphs[i], gw)
        elif first_ascii > 0:
            for i, g in enumerate(self._glyphs):
                c = chr(first_ascii + i)
                self._char_map[c] = (g, g.get_width())

    @staticmethod
    def _auto_detect_glyphs(sheet: pygame.Surface, char_height: int) -> list[pygame.Surface]:
        w = sheet.get_width()
        glyphs: list[pygame.Surface] = []
        in_glyph = False
        start = 0
        for x in range(w):
            has = any(sheet.get_at((x, y)).a > 0 for y in range(char_height))
            if has and not in_glyph:
                start = x
                in_glyph = True
            elif not has and in_glyph:
                if x + 1 >= w or not any(sheet.get_at((x + 1, y)).a > 0 for y in range(char_height)):
                    glyphs.append(sheet.subsurface((start, 0, x - start, char_height)))
                    in_glyph = False
        if in_glyph:
            glyphs.append(sheet.subsurface((start, 0, w - start, char_height)))
        return glyphs

    def render(self, text: str) -> pygame.Surface:
        if not self._char_map:
            return pygame.Surface((0, 0))
        total_w = 0
        h = 0
        for c in text:
            glyph, gw = self._char_map.get(c, (None, 0))
            if glyph:
                total_w += gw
                if h == 0:
                    h = glyph.get_height()
            else:
                total_w += gw or 4
        if total_w == 0 or h == 0:
            return pygame.Surface((0, 0))
        surf = pygame.Surface((total_w, h))
        surf.set_colorkey((0, 0, 0))
        x = 0
        for c in text:
            glyph, gw = self._char_map.get(c, (None, 0))
            if glyph:
                surf.blit(glyph, (x, 0))
                x += gw
            else:
                x += gw or 4
        return surf

    @property
    def char_height(self) -> int:
        return next((g.get_height() for g in self._glyphs), 0)

    @property
    def glyph_count(self) -> int:
        return len(self._glyphs)
