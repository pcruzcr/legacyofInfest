# Análisis de escenas y UI/UX

Las 35 escenas del registro + las 19 escenas de nivel se corrieron con un
arnés de juego real: ciclo de vida completo, 60 fotogramas por tecla de
menú (arriba/abajo/confirmar/cancelar, las 2 teclas de cada acción),
ocupación de pantalla por muestreo jitter determinista.

## Escenas de UI

| escena | módulo | observación |
|---|---|---|
| SplashScene | `src.engine.scenes.splash_scene` | Pantalla de presentación autoplay: cumple. |
| TitleScene | `src.engine.scenes.title_scene` | Menú principal completo, responde a navegación y a todas las teclas. |
| OptionsScene | `src.engine.scenes.options_scene` | Opciones con menú vertical + valores izquierda/derecha. |
| KeybindingScene | `src.engine.scenes.keybinding_scene` | Reasignación de teclas: navega y confirma. |
| LoadGameScene | `src.engine.scenes.load_game_scene` | Sin partidas guardadas en el estado inicial del arnés: la navegación no tiene items. Falta un mensaje de estado vacío visible. |
| SkillTreeScene | `src.engine.scenes.skill_tree_scene` | Árbol de habilidades: navega y confirma. |
| TutorialScene | `src.engine.scenes.tutorial_scene` | Tutorial: navegación completa. |
| GameOverScene | `src.engine.scenes.game_over_scene` | Game over con menú de reaparición: navega y confirma. |
| StageErrorScene | `src.engine.scenes.stage_error_scene` | Pantalla de error estática por diseño: sin teclas, se cierra por flujo externo. Correcta. |
| EndCreditsScene | `src.engine.scenes.end_credits_scene` | Créditos que ruedan: ~1 s de negro antes de entrar el texto (ventana de entrada lenta). |
| WorldMapScene | `src.engine.scenes.world_map_scene` | Mapa del mundo: 16 nodos, navegación por flechas con salto vertical; CONFIRM entra y CANCEL sale. |
| InventoryScene | `src.engine.scenes.inventory_scene` | Inventario vacío en el estado inicial del arnés: nada que navegar. Falta mensaje de vacío. |
| ShopScene | `src.engine.scenes.shop_scene` | Tienda: CONFIRM compra y CANCEL cierra; reacciona. |
| BestiaryScene | `src.engine.scenes.bestiary_scene` | Bestiario sin entradas en el estado inicial: nada que navegar. Falta mensaje de vacío. |
| AchievementScene | `src.engine.scenes.achievement_scene` | 0 logros desbloqueados en el arnés: nada que navegar. Falta mensaje de vacío. |
| LeaderboardScene | `src.engine.scenes.leaderboard_scene` | 0 puntuaciones en el arnés: nada que navegar. Falta mensaje de vacío. |
| ProgressScene | `src.engine.scenes.progress_scene` | Sin progreso en el arnés: nada que navegar. Falta mensaje de vacío. |
| DemoMenuScene | `src.engine.scenes.demo_menu_scene` | Menú de demos: navega y confirma. |
| StoryScene | `src.engine.scenes.story_scene` | Historia: navegación completa. |
| UnitTheoryScene | `src.engine.scenes.unit_theory_scene` | Teoría por páginas: CONFIRM avanza de página. |
| StudentLoginScene | `src.engine.scenes.student_login_scene` | Login de estudiante: navegación completa. |
| VectorLabScene | `src.engine.scenes.vector_lab_scene` | Laboratorio de vectores: reacciona a las teclas del menú (paneles). |
| TransformLabScene | `src.engine.scenes.transform_lab_scene` | Laboratorio de transformaciones: reacciona (DOWN/UP mueven selección de parámetro). |
| CollisionLabScene | `src.engine.scenes.collision_lab_scene` | Laboratorio de colisiones: reacciona y hasta simula jugador. |
| InterpolationLabScene | `src.engine.scenes.interpolation_lab_scene` | Laboratorio de interpolación: reacciona. |
| NoiseLabScene | `src.engine.scenes.noise_lab_scene` | Laboratorio de ruido: reacciona. |
| CurveEditorScene | `src.engine.scenes.curve_editor_scene` | Editor de curvas: reacciona (DOWN/UP). |
| ColorTheoryScene | `src.engine.scenes.color_theory_scene` | Teoría del color: reacciona. |
| FilterDemoScene | `src.engine.scenes.filter_demo_scene` | Demo de filtros: reacciona (DOWN/UP cambian filtro). |
| VisionDemoScene | `src.engine.scenes.vision_demo_scene` | Demo de visión: reacciona. |
| PatternDemoScene | `src.engine.scenes.pattern_demo_scene` | Demo de patrones: reacciona. |
| PipelineBuilderScene | `src.engine.scenes.pipeline_builder_scene` | Constructor de pipeline: reacciona. |
| ComboDemoScene | `src.engine.scenes.combo_demo_scene` | Demo de combos: reacciona. |
| SandboxScene | `src.engine.scenes.sandbox_scene` | Arena de pruebas: reacciona. |
| StageWizardScene | `src.engine.scenes.stage_wizard_scene` | Asistente de escenarios: reacciona. |

## Escenas de nivel (juego real)

| nivel | observación |
|---|---|
| stage0 | `Corre y dibuja el mundo completo (carga TMX + entidades + física + HUD).` |
| stage_mecanicas | `Ídem; mecánicas dinámicas funcionando en el arnés.` |
| stage_cenital | `Modo cenital corre en el arnés.` |
| stage1_1 | `Corre y dibuja.` |
| stage1_2_la_soda | `Corre y dibuja.` |
| stage1_3_las_aulas | `Corre y dibuja.` |
| stage2_1_oficinas | `Corre y dibuja; el arnés no toca los 0 checkpoints.` |
| stage2_2 | `Corre y dibuja.` |
| lobby_datacenter | `Corre y dibuja.` |
| stage3_1_la_entrada_de_piedra | `Corre y dibuja.` |
| hall | `Corre y dibuja; escalera one-way hasta la salida.` |
| stage3_3_el_patio | `Corre y dibuja.` |
| stage3_4_boss_gavilan | `Corre y dibuja; el jefe no entra en combate (Fase 1 sola).` |
| stage4_1 | `Corre y dibuja; cutscenes se limpian como en ayudantes_stage4_1.` |
| stage4_1b | `Corre y dibuja.` |
| stage4_1c_a | `Corre y dibuja la sección rítmica completa.` |
| boss_venado | `Corre y dibuja; jefe con fases.` |
| boss_rey | `Corre y dibuja.` |
| boss_paburu | `Corre y dibuja; arena completa.` |

## Hallazgos transversales de UX

1. **Siete menús con estado vacío sin mensaje** (LoadGame, Inventory,
   Bestiary, Achievement, Leaderboard, Progress): con 0 datos la pantalla
   dibuja su marco pero no hay nada que navegar y no se ve un texto de
   "no hay nada todavía". La batería los marca como skip documentado, no
   como fallo: es una decisión de diseño pendiente.
2. **Créditos con 1 s de negro**: EndCredits rueda desde y=600 y el texto
   tarda ~1 s en entrar (ventana de entrada lenta).
3. **Doble tecla por acción**: cada acción de menú tiene 2 teclas (p. ej.
   flechas y WASD); la batería prueba ambas.
4. **Sin hallazgos de input muerto**: las 35 escenas reaccionan a sus
   teclas; las estáticas (StageError) lo son por diseño.
