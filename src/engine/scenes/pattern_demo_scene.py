from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pygame
import numpy as np

from src.engine.core import settings
from src.engine.input.action_map import Action
from src.engine.scene.base_scene import BaseScene
from src.engine.scenes.demo_common import (
    COLOR_BG,
    COLOR_TEXT,
    COLOR_HIGHLIGHT,
    COLOR_ACCENT,
    COLOR_DIVIDER,
    COLOR_TOP_BAR_BG,
    COLOR_BOTTOM_BAR_BG,
    FONT_SMALL,
    FONT_MEDIUM,
    FONT_LARGE,
    RIGHT_PANEL_W,
    RIGHT_PANEL_X,
    PANEL_H,
    PANEL_SIZE,
    TOP_BAR_Y,
    TOP_BAR_H,
    BOTTOM_BAR_Y,
    BOTTOM_BAR_H,
    draw_top_bar,
    draw_bottom_bar,
    draw_bottom_bar_error,
    draw_panel_border,
    draw_divider,
    draw_save_notification,
    save_png,
    build_default_sources,
    SourceSurfaceManager,
    FrameThrottle,
)
from src.engine.utils.asset_loader import AssetLoader
from src.framework.processing.vision_tools import VisionTools
from src.framework.processing.pattern_recognition_tools import (
    PatternRecognitionTools,
    TrainedModel,
)

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext


MODE_NAMES = [
    "INFERENCE", "FEATURE_COMPARE", "CLASS_GRID", "CONFUSION", "PIPELINE", "TREE_VIEW",
]

FEATURE_METHODS = ["hog", "lbp", "color_hist", "combined"]

CLASS_COLORS: list[tuple[int, int, int]] = [
    (255, 80, 80), (80, 255, 80), (80, 160, 255), (255, 200, 80),
    (200, 80, 255), (80, 255, 200), (255, 140, 80), (200, 200, 200),
]

_MODEL_DIR = Path("assets") / "models"
_DEFAULT_MODEL = _MODEL_DIR / "professor_sample.pkl"


class PatternDemoScene(BaseScene):
    def __init__(self, context: GameContext) -> None:
        super().__init__(context)
        self._mode: int = 0
        self._sources: SourceSurfaceManager = build_default_sources()
        self._throttle = FrameThrottle()

        # Analysis rect
        self._rect_x: int = 64
        self._rect_y: int = 74
        self._rect_size: int = 32

        # Model
        self._model: TrainedModel | None = None
        self._model_name: str = "professor_sample"
        self._method_idx: int = 0

        # Text input for model loading
        self._text_input_active: bool = False
        self._text_buffer: str = ""
        self._cursor_visible: bool = True
        self._cursor_timer: float = 0.0

        # Cached results
        self._cached_class_label: str = ""
        self._cached_probas: dict[str, float] = {}
        self._cached_feature: np.ndarray | None = None
        self._cached_result_surf: pygame.Surface | None = None
        self._param_changed: bool = True
        self._frame_count: int = 0

        # TREE_VIEW state
        self._tree_depth: int = 2
        self._tree_structure: list[dict] | None = None

        # Save / error / notifications
        self._save_msg: str = ""
        self._save_timer: float = 0.0
        self._error_msg: str = ""
        self._error_timer: float = 0.0
        self._status_msg: str = ""
        self._status_timer: float = 0.0

        self._font_small = AssetLoader.load_font(settings.ASSETS_DIR / "fonts" / "game.ttf", FONT_SMALL)
        self._font_medium = AssetLoader.load_font(settings.ASSETS_DIR / "fonts" / "game.ttf", FONT_MEDIUM)
        self._font_large = AssetLoader.load_font(settings.ASSETS_DIR / "fonts" / "game.ttf", FONT_LARGE)

        # Pre-computed dataset samples (for class grid)
        self._dataset_samples: list[tuple[np.ndarray, str]] = []
        self._class_grid_generated: bool = False

    def _load_default_model(self) -> None:
        try:
            if _DEFAULT_MODEL.exists():
                self._model = PatternRecognitionTools.load_model(str(_DEFAULT_MODEL))
                self._model_name = "professor_sample"
                self._status_msg = f"Loaded: {self._model_name}"
                self._status_timer = 2.0
            else:
                self._error_msg = "Default model not found"
                self._error_timer = 2.0
        except Exception as e:
            self._error_msg = f"Model load error: {e}"[:60]
            self._error_timer = 2.0

    def on_enter(self) -> None:
        self._mode = 0
        self._throttle.reset()
        self._param_changed = True
        self._load_default_model()

    def on_exit(self) -> None:
        pass

    def update(self, dt: float) -> None:
        im = self.input
        if im is None:
            return

        self._frame_count += 1
        self._throttle.tick()
        self._param_changed = False

        # Timers
        for attr in ["_save_timer", "_error_timer", "_status_timer", "_cursor_timer"]:
            val = getattr(self, attr)
            if val > 0:
                setattr(self, attr, val - dt)
        if self._save_timer <= 0:
            self._save_msg = ""
        if self._error_timer <= 0:
            self._error_msg = ""
        if self._status_timer <= 0:
            self._status_msg = ""

        # Cursor blink
        if self._cursor_timer <= 0:
            self._cursor_visible = not self._cursor_visible
            self._cursor_timer = 0.5

        # Handle text input mode
        if self._text_input_active:
            self._handle_text_input(im)
            return

        # Normal mode controls
        if im.is_raw_key_pressed(pygame.K_TAB):
            self._mode = (self._mode + 1) % len(MODE_NAMES)
            self._cached_result_surf = None
            self._param_changed = True
            self._throttle.reset()
            if self._mode == 5:
                self._extract_tree()

        if im.is_raw_key_pressed(pygame.K_SPACE):
            self._sources.cycle()
            self._cached_result_surf = None
            self._param_changed = True

        if im.is_raw_key_pressed(pygame.K_f):
            if self._sources.is_frozen:
                self._sources.unfreeze()
            else:
                self._sources.freeze()
            self._cached_result_surf = None
            self._param_changed = True

        if im.is_raw_key_pressed(pygame.K_s):
            if self._cached_result_surf is not None:
                path = save_png("pattern", MODE_NAMES[self._mode].lower(), self._cached_result_surf)
                self._save_msg = f"Saved: {path}"
                self._save_timer = 2.0

        if im.is_raw_key_pressed(pygame.K_r):
            self._load_default_model()
            self._cached_result_surf = None
            self._param_changed = True
            self._tree_structure = None

        if im.is_raw_key_pressed(pygame.K_l):
            self._text_input_active = True
            self._text_buffer = ""
            self._cursor_visible = True
            self._cursor_timer = 0.5

        if im.is_raw_key_pressed(pygame.K_m):
            self._method_idx = (self._method_idx + 1) % len(FEATURE_METHODS)
            self._cached_result_surf = None
            self._param_changed = True

        if im.is_action_pressed(Action.CANCEL):
            self._text_input_active = False
            from src.engine.scenes.demo_menu_scene import DemoMenuScene
            self.context.scene_manager.replace(DemoMenuScene(self.context))
            return

        # TREE_VIEW depth control
        if self._mode == 5 and self._tree_structure:
            if im.is_raw_key_pressed(pygame.K_LEFT):
                self._tree_depth = max(0, self._tree_depth - 1)
                self._param_changed = True
            if im.is_raw_key_pressed(pygame.K_RIGHT):
                self._tree_depth = min(6, self._tree_depth + 1)
                self._param_changed = True

        # Analysis rect movement (modes 0, 1)
        if self._mode in (0, 1):
            held = pygame.key.get_pressed()
            if held[pygame.K_w]:
                self._rect_y = max(0, self._rect_y - 8)
                self._param_changed = True
            if held[pygame.K_s]:
                self._rect_y = min(PANEL_H - self._rect_size, self._rect_y + 8)
                self._param_changed = True
            if held[pygame.K_a]:
                self._rect_x = max(0, self._rect_x - 8)
                self._param_changed = True
            if held[pygame.K_d]:
                self._rect_x = min(RIGHT_PANEL_W - self._rect_size, self._rect_x + 8)
                self._param_changed = True
            if im.is_raw_key_pressed(pygame.K_PLUS) or im.is_raw_key_pressed(pygame.K_EQUALS):
                self._rect_size = min(80, self._rect_size + 8)
                self._param_changed = True
            if im.is_raw_key_pressed(pygame.K_MINUS):
                self._rect_size = max(16, self._rect_size - 8)
                self._param_changed = True

        # Compute result every N frames (throttled)
        if self._param_changed or self._frame_count % 3 == 0:
            self._compute_result()

    def _handle_text_input(self, im):
        if im.is_raw_key_pressed(pygame.K_RETURN):
            self._text_input_active = False
            filename = self._text_buffer.strip()
            if not filename:
                return
            if not filename.endswith(".pkl"):
                filename += ".pkl"
            path = _MODEL_DIR / filename
            try:
                self._model = PatternRecognitionTools.load_model(str(path))
                self._model_name = filename
                self._status_msg = f"Loaded: {filename}"
                self._status_timer = 2.0
                self._cached_result_surf = None
                self._param_changed = True
            except Exception as e:
                self._error_msg = f"Failed: {e}"[:60]
                self._error_timer = 2.0
                self._load_default_model()
            self._text_buffer = ""
            return

        if im.is_raw_key_pressed(pygame.K_ESCAPE):
            self._text_input_active = False
            self._text_buffer = ""
            return

        if im.is_raw_key_pressed(pygame.K_BACKSPACE):
            self._text_buffer = self._text_buffer[:-1]
            return

        # Check for printable characters via event unicode
        # (simplified: only alphanumeric, underscore, dot, dash)
        for key, char in _get_printable_keys(im):
            self._text_buffer += char

    def _compute_result(self) -> None:
        src = self._sources.current_source
        if src is None or self._model is None:
            self._cached_result_surf = pygame.Surface(PANEL_SIZE)
            self._cached_result_surf.fill((0, 0, 0))
            return

        try:
            # Extract features from analysis rect
            rect = pygame.Rect(self._rect_x, self._rect_y, self._rect_size, self._rect_size)
            region = src.subsurface(rect)
            method = FEATURE_METHODS[self._method_idx]
            scaled = pygame.transform.scale(region, (32, 32))
            features = VisionTools.extract_features(scaled, method=method)

            self._cached_feature = features

            if self._mode == 0:  # INFERENCE
                label = PatternRecognitionTools.classify(features, self._model)
                probas = PatternRecognitionTools.classify_proba(features, self._model)
                self._cached_class_label = label
                self._cached_probas = probas
                self._cached_result_surf = self._render_inference(probas, label, method, features)

            elif self._mode == 1:  # FEATURE_COMPARE
                # Find nearest training sample (brute force)
                nearest_dist, nearest_label, nearest_feat = self._find_nearest(features)
                self._cached_result_surf = self._render_feature_compare(
                    features, nearest_feat, nearest_label, nearest_dist, method,
                )

            elif self._mode == 2:  # CLASS_GRID
                self._generate_class_grid()
                self._cached_result_surf = self._render_class_grid()

            elif self._mode == 3:  # CONFUSION
                self._cached_result_surf = self._render_confusion()

            elif self._mode == 4:  # PIPELINE
                self._cached_result_surf = self._render_pipeline(src, rect, features, method)

            elif self._mode == 5:  # TREE_VIEW
                if self._tree_structure:
                    self._cached_result_surf = self._render_tree()

            self._error_msg = ""
        except Exception as e:
            self._error_msg = f"Error: {e}"[:60]
            self._error_timer = 2.0

    def _find_nearest(self, features: np.ndarray) -> tuple[float, str, np.ndarray]:
        best_dist = float("inf")
        best_label = ""
        best_feat = np.zeros_like(features)
        if not self._dataset_samples:
            return 0.0, "unknown", best_feat
        for feat, label in self._dataset_samples:
            d = float(np.linalg.norm(features - feat))
            if d < best_dist:
                best_dist = d
                best_label = label
                best_feat = feat
        return best_dist, best_label, best_feat

    def _generate_class_grid(self) -> None:
        if self._class_grid_generated and self._dataset_samples:
            return
        # Try to load from sample_dataset.npz
        ds_path = Path("assets") / "datasets" / "sample_dataset.npz"
        if ds_path.exists():
            try:
                data = np.load(str(ds_path))
                X = data["features"]
                y = data["labels"]
                self._dataset_samples = [(X[i], str(y[i])) for i in range(min(len(X), 16))]
            except Exception:
                pass
        # Generate random if empty
        if not self._dataset_samples:
            rng = np.random.RandomState(42)
            for i in range(16):
                feat = rng.randn(512).astype(np.float32)
                self._dataset_samples.append((feat, f"class_{i % 3}"))
        self._class_grid_generated = True

    def _render_inference(self, probas: dict, label: str, method: str,
                          features: np.ndarray) -> pygame.Surface:
        surf = pygame.Surface(PANEL_SIZE)
        surf.fill((5, 5, 15))
        y = 10

        # Class label
        lc = self._class_color(label)
        cls_text = self._font_large.render(f"  CLASS: {label}", True, lc)
        surf.blit(cls_text, (10, y))
        y += 16

        # Confidence
        conf = max(probas.values()) if probas else 0.0
        conf_text = self._font_medium.render(f"  Confidence: {conf:.2f}", True, COLOR_TEXT)
        surf.blit(conf_text, (10, y))
        y += 14

        # Top 3 predictions
        sorted_p = sorted(probas.items(), key=lambda x: -x[1])[:3]
        y += 4
        section_label = self._font_small.render("  TOP 3 PREDICTIONS", True, COLOR_ACCENT)
        surf.blit(section_label, (10, y))
        y += 10
        for p_label, p_val in sorted_p:
            pc = self._class_color(p_label)
            bar_w = int(p_val * 120)
            label_t = self._font_small.render(f"  {p_label:15s}", True, pc)
            surf.blit(label_t, (10, y))
            if bar_w > 0:
                pygame.draw.rect(surf, pc, (80, y + 1, bar_w, 6))
            pct_t = self._font_small.render(f" {p_val * 100:.0f}%", True, COLOR_TEXT)
            surf.blit(pct_t, (210, y))
            y += 10

        # Feature vector bar chart
        y += 4
        fv_label = self._font_small.render("  FEATURE VECTOR", True, COLOR_ACCENT)
        surf.blit(fv_label, (10, y))
        y += 10
        self._draw_feature_bars(surf, features, 10, y, 140, 30, _method_color(method))

        # Info
        y += 36
        info = self._font_small.render(
            f"  Model: {self._model_name}  |  Method: {method}  |  Vector: {len(features)}",
            True, COLOR_TEXT,
        )
        surf.blit(info, (10, y))

        return surf

    def _render_feature_compare(self, features: np.ndarray, nearest_feat: np.ndarray,
                                nearest_label: str, distance: float,
                                method: str) -> pygame.Surface:
        surf = pygame.Surface(PANEL_SIZE)
        surf.fill((5, 5, 15))
        y = 10

        src_label = self._font_small.render("Source Feature Vector:", True, COLOR_ACCENT)
        surf.blit(src_label, (10, y))
        y += 10
        self._draw_feature_bars(surf, features, 10, y, 140, 25, _method_color(method))

        y += 30
        nrst_label = self._font_small.render("Nearest Training Sample:", True, COLOR_ACCENT)
        surf.blit(nrst_label, (10, y))
        y += 10
        self._draw_feature_bars(surf, nearest_feat, 10, y, 140, 25,
                                self._class_color(nearest_label))

        y += 30
        info = self._font_small.render(
            f"  Distance: {distance:.3f}  |  Nearest: {nearest_label}",
            True, COLOR_TEXT,
        )
        surf.blit(info, (10, y))

        return surf

    def _render_class_grid(self) -> pygame.Surface:
        surf = pygame.Surface(PANEL_SIZE)
        surf.fill((5, 5, 15))
        cell_w = 36
        cell_h = 44
        cols = 4
        for i, (feat, label) in enumerate(self._dataset_samples[:16]):
            col = i % cols
            row = i // cols
            x = 4 + col * cell_w
            y = 4 + row * cell_h
            color = self._class_color(label)
            # Cell background
            pygame.draw.rect(surf, color, (x, y, cell_w - 2, cell_h - 2), 2)
            # Class label
            lt = self._font_small.render(label[:8], True, COLOR_TEXT)
            surf.blit(lt, (x + 2, y + cell_h - 14))
        return surf

    def _render_confusion(self) -> pygame.Surface:
        surf = pygame.Surface(PANEL_SIZE)
        surf.fill((5, 5, 15))
        meta = getattr(self._model, "metadata", {}) if self._model else {}
        ev = meta.get("evaluation", {})

        # Try matplotlib report first
        if self._model is not None and ev and "confusion_matrix" in ev:
            try:
                classes = list(self._model.classes)
                report_surf = PatternRecognitionTools.generate_training_report(
                    self._model, figure_size=(8, 6), dpi=80,
                )
                if report_surf is not None:
                    scaled = pygame.transform.scale(report_surf, PANEL_SIZE)
                    return scaled
            except Exception:
                pass

        # Fallback: manual grid rendering
        if not ev or "confusion_matrix" not in ev:
            msg = self._font_small.render(
                "Confusion matrix not available — run evaluate() during training",
                True, COLOR_TEXT,
            )
            surf.blit(msg, (10, 30))
            return surf

        cm = ev["confusion_matrix"]
        accuracy = ev.get("accuracy", 0.0)
        n = len(cm)
        cell_sz = 20
        max_diag = max((cm[i][i] for i in range(n)), default=1)
        max_off = max((cm[i][j] for i in range(n) for j in range(n) if i != j), default=1)

        ox, oy = 10, 10
        for i in range(n):
            for j in range(n):
                val = cm[i][j]
                x = ox + j * cell_sz
                y = oy + i * cell_sz
                if i == j:
                    intensity = min(val / max_diag, 1.0)
                    color = (int(40 * (1 - intensity)), int(180 * intensity), 40)
                else:
                    intensity = min(val / max_off, 1.0)
                    color = (int(180 * intensity), 40, 40)
                pygame.draw.rect(surf, color, (x, y, cell_sz - 1, cell_sz - 1))
                vt = self._font_small.render(str(val), True, COLOR_TEXT)
                surf.blit(vt, (x + 2, y + 2))

        bottom = oy + n * cell_sz + 4
        acc_text = self._font_small.render(
            f"  Accuracy: {accuracy:.1%}  |  Classes: {n}",
            True, COLOR_HIGHLIGHT,
        )
        surf.blit(acc_text, (ox, bottom))

        return surf

    def _render_pipeline(self, src: pygame.Surface, rect: pygame.Rect,
                         features: np.ndarray, method: str) -> pygame.Surface:
        surf = pygame.Surface(PANEL_SIZE)
        surf.fill((5, 5, 15))
        y = 6

        steps = [
            ("Source Region", self._render_step_surface(src, rect, (32, 32))),
            ("Preprocessed", self._render_step_surface(src, rect, (32, 32))),
            ("HOG vis", None),
            ("Feature Vector", features),
            ("Class Label", self._cached_class_label if hasattr(self, '_cached_class_label') else ""),
        ]

        for step_name, step_data in steps:
            if step_name == "HOG vis":
                # Show cell grid viz
                cell_surf = pygame.Surface((32, 32))
                cell_surf.fill((20, 20, 40))
                for gy in range(0, 32, 8):
                    for gx in range(0, 32, 8):
                        pygame.draw.rect(cell_surf, (60, 60, 80), (gx, gy, 8, 8), 1)
                step_surf = cell_surf
            elif isinstance(step_data, np.ndarray):
                step_surf = pygame.Surface((80, 20))
                self._draw_feature_bars(step_surf, step_data, 0, 0, 80, 20, _method_color(method))
            elif isinstance(step_data, str):
                step_surf = self._font_small.render(step_data, True, COLOR_HIGHLIGHT)
            elif isinstance(step_data, tuple):
                step_surf = step_data[0]
            elif isinstance(step_data, pygame.Surface):
                step_surf = step_data
            else:
                step_surf = self._font_small.render("(empty)", True, COLOR_TEXT)

            label_t = self._font_small.render(f"  {step_name}", True, COLOR_ACCENT)
            surf.blit(label_t, (4, y))
            y += 10
            if hasattr(step_surf, 'get_width'):
                surf.blit(step_surf, (20, y))
                y += step_surf.get_height() + 8
            else:
                y += 12

            # Arrow
            if step_name != "Class Label":
                arr_t = self._font_small.render("     v", True, COLOR_DIVIDER)
                surf.blit(arr_t, (4, y))
                y += 10

        return surf

    @staticmethod
    def _render_step_surface(src: pygame.Surface, rect: pygame.Rect,
                             size: tuple[int, int]) -> pygame.Surface:
        try:
            sub = src.subsurface(rect)
            return pygame.transform.scale(sub, size)
        except Exception:
            s = pygame.Surface(size)
            s.fill((40, 40, 60))
            return s

    def _draw_feature_bars(self, surf: pygame.Surface, feat: np.ndarray,
                           x: int, y: int, w: int, h: int, color: tuple) -> None:
        n = min(len(feat), w)
        max_val = max(abs(feat).max(), 1e-6)
        bar_w = max(w // n, 1)
        cy = y + h // 2
        for i in range(n):
            bar_h = int((feat[i] / max_val) * (h // 2 - 1))
            bx = x + i * bar_w
            if bar_h >= 0:
                pygame.draw.rect(surf, color, (bx, cy - bar_h, bar_w, bar_h))
            else:
                pygame.draw.rect(surf, color, (bx, cy, bar_w, -bar_h))

    @staticmethod
    def _class_color(label: str) -> tuple[int, int, int]:
        idx = hash(label) % len(CLASS_COLORS)
        return CLASS_COLORS[idx]

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(COLOR_BG)
        draw_top_bar(surface, "PATTERN DEMO", "UNIT IX")

        # Top info
        info_line = f"  Model: {self._model_name}  |  Method: {FEATURE_METHODS[self._method_idx]}  |  Mode: {MODE_NAMES[self._mode]}"
        top_info = self._font_small.render(info_line, True, COLOR_HIGHLIGHT)
        surface.blit(top_info, (4, TOP_BAR_Y + TOP_BAR_H - 14))

        # Left panel (source with analysis rect)
        src = self._sources.current_source
        if src is not None:
            scaled = pygame.transform.scale(src, PANEL_SIZE)
            surface.blit(scaled, (0, TOP_BAR_H))
            # Draw analysis rect
            rect = pygame.Rect(self._rect_x, self._rect_y, self._rect_size, self._rect_size)
            pygame.draw.rect(surface, (255, 220, 80), rect, 1)
        draw_panel_border(surface, pygame.Rect(0, TOP_BAR_H, PANEL_SIZE[0], PANEL_H))

        src_label = self._font_small.render(
            f"  {self._sources.current_name}{' [FROZEN]' if self._sources.is_frozen else ''}  ",
            True, COLOR_ACCENT,
        )
        surface.blit(src_label, (4, TOP_BAR_H + PANEL_H - 12))

        # Right panel
        right_rect = pygame.Rect(RIGHT_PANEL_X, TOP_BAR_H, PANEL_SIZE[0], PANEL_H)
        if self._cached_result_surf is not None:
            scaled_r = pygame.transform.scale(self._cached_result_surf, PANEL_SIZE)
            surface.blit(scaled_r, (RIGHT_PANEL_X, TOP_BAR_H))
        draw_panel_border(surface, right_rect)

        draw_divider(surface)

        # Bottom bar
        self._draw_bottom_bar(surface)

        if self._save_msg:
            pygame.draw.rect(surface, COLOR_TOP_BAR_BG,
                             (0, BOTTOM_BAR_Y, settings.INTERNAL_WIDTH, BOTTOM_BAR_H))
            draw_save_notification(surface, self._save_msg, self._font_small)

    def _extract_tree(self) -> None:
        if self._model is None:
            self._tree_structure = None
            return
        model = getattr(self._model, "model", self._model)
        # Check for sklearn tree attributes
        if hasattr(model, "tree_"):
            self._tree_structure = self._extract_sklearn_tree(model)
        elif hasattr(model, "estimators_"):
            # Random Forest — use first tree
            try:
                self._tree_structure = self._extract_sklearn_tree(model.estimators_[0])
            except Exception:
                self._tree_structure = None
        else:
            self._tree_structure = None

    @staticmethod
    def _extract_sklearn_tree(tree_model) -> list[dict] | None:
        tree = tree_model.tree_
        n_nodes = tree.node_count
        features = tree.feature
        thresholds = tree.threshold
        children_left = tree.children_left
        children_right = tree.children_right
        try:
            values = tree.value
        except Exception:
            values = None
        classes = getattr(tree_model, "classes_", None)
        if classes is not None:
            class_names = [str(c) for c in classes]
        elif values is not None:
            class_names = [f"C{i}" for i in range(values.shape[1])]
        else:
            class_names = []
        nodes = []
        for i in range(n_nodes):
            is_leaf = children_left[i] == -1 and children_right[i] == -1
            feat = int(features[i]) if features[i] >= 0 else -1
            vals = values[i].ravel().tolist() if values is not None else []
            nodes.append({
                "id": i,
                "feature": feat,
                "threshold": float(thresholds[i]),
                "left": int(children_left[i]),
                "right": int(children_right[i]),
                "is_leaf": is_leaf,
                "values": vals,
                "class_names": list(class_names),
            })
        return nodes

    def _render_tree(self) -> pygame.Surface:
        surf = pygame.Surface(PANEL_SIZE)
        surf.fill((5, 5, 15))
        if not self._tree_structure:
            msg = self._font_small.render("No tree structure available for this model", True, COLOR_TEXT)
            surf.blit(msg, (10, 30))
            return surf
        self._draw_tree_nodes(surf, self._tree_structure, 0, 0, PANEL_SIZE[0] - 10, 0)
        depth_label = self._font_small.render(
            f"  Max Depth: {self._tree_depth}  |  [LEFT/RIGHT] adjust  |  Pruning depth shown",
            True, COLOR_ACCENT,
        )
        surf.blit(depth_label, (4, PANEL_H - 12))
        return surf

    def _draw_tree_nodes(self, surf: pygame.Surface, nodes: list[dict],
                         node_id: int, x: int, w: int, depth: int) -> None:
        if node_id < 0 or node_id >= len(nodes) or depth > self._tree_depth:
            return
        node = nodes[node_id]
        y = 16 + depth * 24
        cx = x + w // 2

        # Node box
        if node["is_leaf"]:
            major = max(node["values"]) if node["values"] else 0
            majority_idx = node["values"].index(major) if node["values"] else 0
            color = self._class_color(str(majority_idx))
            label = node["class_names"][majority_idx] if node["class_names"] and majority_idx < len(node["class_names"]) else str(majority_idx)
            pygame.draw.rect(surf, color, (cx - 20, y, 40, 18))
            lbl = self._font_small.render(label, True, (0, 0, 0))
            surf.blit(lbl, (cx - 18, y + 2))
        else:
            feat = node["feature"]
            thresh = node["threshold"]
            label = f"f[{feat}]<={thresh:.1f}"
            pygame.draw.rect(surf, COLOR_HIGHLIGHT, (cx - 36, y, 72, 18), 1)
            lbl = self._font_small.render(label, True, COLOR_HIGHLIGHT)
            surf.blit(lbl, (cx - 34, y + 2))
            # Draw branches
            left = node["left"]
            right = node["right"]
            lw = w // 2
            if left >= 0:
                lx = x + lw // 2
                pygame.draw.line(surf, (60, 180, 60), (cx - 10, y + 18), (lx, y + 44), 1)
                self._draw_tree_nodes(surf, nodes, left, x, lw, depth + 1)
            if right >= 0:
                rx = x + w // 2 + lw // 2
                pygame.draw.line(surf, (180, 60, 60), (cx + 10, y + 18), (rx, y + 44), 1)
                self._draw_tree_nodes(surf, nodes, right, x + lw, lw, depth + 1)

    def _draw_bottom_bar(self, surface: pygame.Surface) -> None:
        if self._error_msg:
            draw_bottom_bar_error(surface, self._error_msg)
            return
        if self._save_msg:
            return
        if self._text_input_active:
            self._draw_text_input(surface)
            return
        if self._status_msg:
            draw_bottom_bar(surface, self._status_msg)
            return

        method = FEATURE_METHODS[self._method_idx]
        text = (f"  [L] Load model  |  [M] Cycle method ({method})  |  "
                f"[WASD] Move rect  |  [+/-] Resize  |  [TAB] Mode  |  [R] Reload default")
        draw_bottom_bar(surface, text)

    def _draw_text_input(self, surface: pygame.Surface) -> None:
        prefix = "Load model: assets/models/"
        display = prefix + self._text_buffer
        if self._cursor_visible:
            display += "|"
        pygame.draw.rect(surface, COLOR_BOTTOM_BAR_BG,
                         (0, BOTTOM_BAR_Y, settings.INTERNAL_WIDTH, BOTTOM_BAR_H))
        text = self._font_small.render(display, True, COLOR_HIGHLIGHT)
        surface.blit(text, (4, BOTTOM_BAR_Y + 2))


def _get_printable_keys(im) -> list[tuple[int, str]]:
    result = []
    for key, char in _KEY_CHAR_MAP.items():
        if im.is_raw_key_pressed(key):
            result.append((key, char))
    return result


_KEY_CHAR_MAP: dict[int, str] = {}
for ch in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-":
    try:
        k = getattr(pygame, f"K_{ch}")
        _KEY_CHAR_MAP[k] = ch
    except AttributeError:
        pass


def _method_color(method: str) -> tuple[int, int, int]:
    return {
        "hog": (80, 160, 255),
        "lbp": (60, 200, 60),
        "color_hist": (200, 60, 60),
        "combined": (255, 200, 80),
    }.get(method, (200, 200, 200))
