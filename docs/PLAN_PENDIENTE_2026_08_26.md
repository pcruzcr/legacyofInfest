# Plan de trabajo pendiente — Legacy of InFest
# Generado: 2026-08-26, tras AUD-631
#
# Estado de la batería CI al generar este plan:
#   ruff: 0 errores (limpio)
#   mypy: 60 ficheros, 0 issues
#   tests core (i18n+nav+accesibilidad+fronteras+contracts+gates): 112/112 pasan
#   tests pre-existentes que fallaban (ambience/arco/puertas): 80/80 pasan
#   KNOWN_GAPS: 73/73 cerrados con Resolution
#
# Este plan cubre SOLO lo que falta y es accionable sin rediseño arquitectónico.

═══════════════════════════════════════════════════════════
FASE A — Infraestructura de calidad (pre-commit + CI gates)
═══════════════════════════════════════════════════════════

A1. Pre-commit hook
    Fichero: .pre-commit-config.yaml
    Acción: hook con ruff check --fix, ruff format, mypy (mypy_scope),
            check_translations --ci --permitted-orphans
    DoD:    git commit ejecuta los 3 checks; un commit con error ruff es bloqueado.
    AUD:    AUD-640

A2. Import-linter (hexagonal boundary en CI)
    Fichero: .importlinter + pyproject.toml [tool.importlinter]
    Acción: contrato "forbidden" — src.engine.core/ui/input/audio/utils
            no pueden importar src.framework ni src.stages.
            Excepción documentada: src/engine/core/app.py.
    DoD:    lint-imports pasa en el árbol actual; añadir un import prohibido lo bloquea.
    AUD:    AUD-641

A3. Perf regression gate (pytest-benchmark baseline)
    Fichero: pyproject.toml [tool.pytest.benchmark] + tests/benchmarks/baseline.json
    Acción: guardar baseline actual de los benchmarks existentes;
            configurar pytest-benchmark para fallar si p95 sube > 5%.
    DoD:    pytest tests/benchmarks/ pasa; modificar un benchmark para que sea
            más lento hace que el gate salte.
    AUD:    AUD-642

═══════════════════════════════════════════════════════════
FASE B — Scripts de verificación que faltan
═══════════════════════════════════════════════════════════

B1. scripts/generate_status.py — cifras vivas auto-generadas
    Acción: script que cuenta tests (--collect-only), GAPs resueltos,
            ficheros TMX, líneas de código → escribe docs/62_ESTADO_DEL_PROYECTO.md.
    DoD:    python scripts/generate_status.py regenera el doc sin cambios
            si las cifras son correctas; añadir una prueba cambia la cifra.
    Tests:  test_que_generate_status_produce_output_valido
    AUD:    AUD-643

B2. scripts/check_loudness.py — EBU R128 / -23 LUFS
    Acción: recorrer assets/music/*.wav y sfx/environment/*.wav,
            medir loudness con pyloudnorm (opcional), reportar desviaciones.
    DoD:    el script corre sin pyloudnorm instalado (skip con aviso);
            con pyloudnorm, reporta LUFS por fichero.
    Tests:  test_check_loudness_corre_sin_pyloudnorm
    AUD:    AUD-644

B3. scripts/check_contrast.py — contraste WCAG del Theme
    Acción: leer Theme tokens, calcular ratio para cada par visible,
            reportar tabla con nivel WCAG.
    DoD:    el script imprime tabla; exit 0 si todos pasan AA.
    Tests:  ya cubierto por tests/test_ui_ux_accesibilidad.py (34 tests).
    AUD:    AUD-645 (el script es la cara CLI del mismo chequeo)

B4. scripts/bench_ui_scaling.py — benchmark visual de escalado
    Acción: renderizar texto a escalas 0.5×–3× y medir tiempo + dimensiones;
            reportar si algún texto excede su contenedor asignado.
    DoD:    el script corre; reporta tiempos por escala; no crashea.
    Tests:  ya cubierto por TestEscaladoDeTexto (13 tests).
    AUD:    AUD-646

═══════════════════════════════════════════════════════════
FASE C — Gameplay: curva de dificultad y playtesting
═══════════════════════════════════════════════════════════

C1. scripts/analyze_difficulty.py — telemetría de curva
    Acción: leer saves/*.json (si existen) y agregar: muertes por escenario,
            tiempo medio por tramo, reintentos. Sin datos, genera plantilla vacía.
    DoD:    el script corre sin datos (genera plantilla); con datos produce informe.
    Tests:  test_analyze_difficulty_con_datos_sinteticos
    AUD:    AUD-647

C2. Assist Mode flags en UserSettings
    Acción: añadir a UserSettings: assist_invulnerable: bool = False,
            assist_infinite_jumps: bool = False, assist_slow_mo: float = 1.0.
            Cablear en Player.update() para que los flags tengan efecto.
    DoD:    UserSettings().assist_invulnerable existe; Player respeta el flag
            (no recibe daño cuando está activo).
    Tests:  test_assist_mode_invulnerabilidad, test_assist_mode_slow_mo
    AUD:    AUD-648

C3. Playtest bot mejorado
    Fichero: tests/playtest/bot.py (ya existe, mejorarlo)
    Acción: bot que navega stage0 completo: caminar, saltar obstáculos,
            recoger item, abrir puerta, llegar al checkpoint.
    DoD:    bot completa stage0 en < 5 min sin exploits.
    Tests:  test_playthrough_bot_stage0
    AUD:    AUD-649

═══════════════════════════════════════════════════════════
FASE D — Documentación
═══════════════════════════════════════════════════════════

D1. API docs desde docstrings (pdoc)
    Acción: pip install pdoc; pdoc src/engine/core/i18n.py > docs/api/i18n.html.
            Generar para los 10 módulos más usados. Commit de HTML generado.
    DoD:    docs/api/ tiene al menos 5 ficheros .html generados desde docstrings.
    AUD:    AUD-650

D2. Diagramas Mermaid en docs/03_ARCHITECTURE.md
    Acción: añadir diagrama de dependencias entre paquetes (Mermaid graph TD).
    DoD:    el diagrama renderiza en GitHub/Obsidian.
    AUD:    AUD-651

D3. ADR log inicial
    Acción: crear docs/adr/ con 5 ADRs de las decisiones más importantes:
            ADR-001: español como lengua única
            ADR-002: engine/framework separación hexagonal
            ADR-003: ECS bajo la jerarquía de entidades, no en su lugar
            ADR-004: catálogo JSON propio vs gettext
            ADR-005: física por contexto (PhysicsProfile) sin pymunk
    DoD:    docs/adr/ tiene ≥ 5 ficheros numerados con formato ADR estándar.
    AUD:    AUD-652

═══════════════════════════════════════════════════════════
FASE E — Gráficos y Audio (mejoras incrementales)
═══════════════════════════════════════════════════════════

E1. Presupuesto VRAM documentado
    Acción: medir memoria de texturas con memoria_de_textura.py (ya existe);
            documentar el presupuesto (< 128 MB atlas, < 64 MB pool);
            añadir gate en test_rendimiento_gates.py.
    DoD:    test_vram_budget pasa con el presupuesto actual.
    AUD:    AUD-653

E2. Frame pacing measurement
    Acción: script que mide frame time P50/P95/P99 sobre stage0 durante 30 s;
            documentar resultado; añadir gate si P95 > 16.67 ms.
    DoD:    script corre en Quadro M2200; resultado documentado.
    AUD:    AUD-654

═══════════════════════════════════════════════════════════
RESUMEN DE ESFUERZO ESTIMADO
═══════════════════════════════════════════════════════════

| Fase | Commits | Prioridad | Dependencias |
|------|---------|-----------|-------------|
| A (infra calidad) | 3 | ALTA — bloquea regresiones | Ninguna |
| B (scripts verificación) | 4 | MEDIA — visibilidad | Ninguna |
| C (gameplay) | 3 | MEDIA — jugabilidad | Ninguna |
| D (documentación) | 3 | BAJA — mantenimiento | Ninguna |
| E (gráficos/audio) | 2 | BAJA — optimización | Quadro M2200 |
| TOTAL | 15 commits | | |

═══════════════════════════════════════════════════════════
ORDEN DE EJECUCIÓN SUGERIDO
═══════════════════════════════════════════════════════════

1. A1 pre-commit          ← primero: previene nuevas regresiones
2. A2 import-linter       ← segundo: vigila frontera hexagonal
3. B1 generate_status     ← tercero: cifras vivas para el resto
4. C2 assist mode         ← cuarto: accesibilidad jugable visible
5. A3 perf regression     ← quinto: protege rendimiento
6. B2 check_loudness      ← sexto
7. C1 analyze_difficulty  ← séptimo
8. B4 bench_ui_scaling    ← octavo (tests ya existen, solo script)
9. B3 check_contrast      ← noveno (tests ya existen, solo script)
10. C3 playtest bot       ← décimo
11. D1-D3 docs            ← último lote
12. E1-E2 gráficos        ← opcional, requiere GPU dedicada