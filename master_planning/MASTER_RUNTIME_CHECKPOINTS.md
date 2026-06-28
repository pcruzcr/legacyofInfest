# MASTER RUNTIME CHECKPOINTS (v3 - Exact Visual Gate Table)

**Fuente:** docs/33_SCOPE_ADJUSTMENT.md v2.0 Section 7

## Regla: Cada fase requiere TEST GATE + VISUAL GATE.
Si el visual gate falla, la fase NO esta completa.

| Phase | Test Gate | Visual Gate |
|---|---|---|
| 1 | pytest tests/test_event_bus.py tests/test_clock.py | python main.py -> window opens, dark navy background visible |
| 2 | pytest tests/test_math_utils.py tests/test_input_manager.py | Input events logged to console when keys pressed |
| 3 | pytest tests/test_scene_manager.py | python main.py -> splash shows non-black content, auto-advances to title |
| 4 | pytest tests/test_hud.py | HUD visible in a test scene - hearts, timer digits visible |
| 5 | pytest tests/test_player_physics.py tests/test_player_state_machine.py tests/test_player_damage.py | Blue player rectangle visible, moves with arrow keys, jumps with space |
| 6 | pytest tests/test_enemy_walker.py tests/test_enemy_shooter.py | Red enemy rectangle patrols, reverses at edges, does not fall |
| 7 | pytest tests/test_stage_loader.py tests/test_camera.py tests/test_checkpoint.py | Player rectangle in TMX scene, camera follows, checkpoint turns gold |
| 8 | pytest tests/test_color_tools.py tests/test_curve_tools.py | No visual gate (pure math) |
| 9 | Manual playthrough checklist | Stage 0 traversable start to finish with real sprites |
| 10 | pytest tests/test_filter_tools.py | FilterDemo scene shows filter effect on source surface |
| 11 | pytest tests/test_vision_tools.py | VisionDemo scene shows segmentation result |
| 12 | pytest tests/test_pattern_recognition_tools.py | PatternDemo scene shows classification result |
| 13 | Manual smoke test | All 3 demos accessible from menu, interactive |
| 14 | pytest tests/test_boss_base.py | Boss arena visible, phases change, bar shows |
| 15 | pytest tests/test_student_template.py | Template copies and runs in 15 minutes |
| 16 | pytest tests/ -v (zero failures) | Full scene flow Splash->Title->Story->Stage0 |

## CRITICO
- Background siempre (15,15,40) dark navy, nunca negro
- Placeholder Player: blue (0,120,255) 20x32
- Placeholder Walker: red (200,0,0) 24x28
- Placeholder Checkpoint active: gold (255,215,0) 16x32
- Checkpoint inactive: gray (120,120,120) 16x32
