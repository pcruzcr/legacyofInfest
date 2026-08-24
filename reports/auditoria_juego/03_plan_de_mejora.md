# Plan de mejora (priorizado)

Ordenado por impacto en el juego y coste. Cada fase es un lote pequeño
(1 AUD por commit) según las reglas del repo.

## Fase 1 — Cerrar los dos hallazgos reales (bloqueantes de campaña)

1. **stage2_1_oficinas: añadir checkpoints.** El nivel entero se reinicia
   al morir (0 checkpoints en 3200 px, peor gap 3048 px ≈ 33 s). Mínimo:
   uno a mitad de nivel (tras el primer piso de oficinas). Medible: la
   prueba `test_checkpoint_gaps_registrados` pasará a verde sin xfail.
2. **boss_paburu: retirar el NextTrigger fantasma (y=-64).** Está fuera
   del mapa: sobra (el nivel se completa por jefe). Decisión del dueño:
   borrarlo o documentarlo; después `test_el_next_trigger_no_esta_fuera_del_mapa`
   pasa a verde.

## Fase 2 — Completar el contenido faltante

3. **Jefe Gavilán (~45 % de la rúbrica).** Fase 1 sola, `attack_patterns`
   vacío. Seguir el plan de `docs/87_REPORTE_DE_LO_QUE_FALTA.md` §27 y
   cerrar los GAP-058..065 de `KNOWN_GAPS.md`. Es el hueco de juego más
   visible: la campaña termina sin el jefe de su bloque.

## Fase 3 — Decisiones de diseño registradas

4. **Mensajes de estado vacío en los 7 menús sin datos** (LoadGame,
   Inventory, Bestiary, Achievement, Leaderboard, Progress): un texto de
   "no hay partidas / entradas / logros todavía" convierte pantallas que
   hoy parecen rotas en pantallas informativas.
5. **Créditos: recortar la ventana de entrada** (empezar el texto más
   arriba o fundir desde el título).
6. **Gaps de stage4_1/4_1c por decisión (AUD-516)**: confirmar con
   sesiones reales si 33 s de reintento en el peor tramo rítmico es la
   dureza que se quiere; si no, un checkpoint por sección.

## Fase 4 — Auditoría fina manual (no automatizable)

7. Confort de saltos y timings de los niveles de estudiantes (1_1, 1_2,
   1_3, 2_2, 3_1, 3_3, boss_rey): la batería garantiza que corren y se
   completan; el *feel* (velocidad, amortiguación, ventanas de salto) se
   juega a mano con una partida por nivel.
8. Balance de la sección de sigilo de stage_mecanicas (cono de visión +
   acosador): difícil de verificar sin jugador humano.

## Cómo queda la batería

- 2 xfail se convierten en pruebas verdes al hacer las fases 1 y 2.
- 7 skips documentados se convierten en pruebas de contenido al sembrar
  datos (partida de ejemplo, entradas de bestiario...) en la fase 3.
