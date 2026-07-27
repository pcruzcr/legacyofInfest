# Verificación del informe «Legacy of InFest — Exhaustive Multidisciplinary Audit v1.0»

**Fecha:** 2026-07-27
**Objeto:** contrastar cada cifra y cada afirmación del informe recibido contra
el repositorio, ejecutando lo que se pueda ejecutar.
**Método:** ninguna afirmación de este documento procede de leer código y
deducir. Cada número lleva al lado el comando que lo produjo.

---

## 1. Resumen ejecutivo de la verificación

El informe recibido acierta en el diagnóstico cualitativo —la arquitectura es
limpia, el proyecto está muy documentado, la remediación fue real— y **falla en
las cifras y en el estado de dos hallazgos críticos**. Su conclusión
(«Production Ready, 91/100, ningún issue crítico») no está sostenida por lo que
el repositorio permite medir hoy.

Tres correcciones que cambian la conclusión:

| Afirmación del informe | Medición real | Comando |
|---|---|---|
| «568 tests, 0 failures» | **1082 pruebas** | `pytest --co -q` |
| «AUD-062 … Fixed» | Estaba **escrito pero sin ejecutar** cuando se emitió el informe | — |
| «65+ documentos en EN/ES» | **70 documentos, 1 con versión .es** | `ls docs/*.md \| wc -l` |
| «Localization 85/100» | No existe ningún sistema i18n | `grep -rn "import gettext" src/` → vacío |
| «COD-004 … no-ops … Acceptable» | Ese no-op causó los dos bugs críticos de esta sesión | AUD-060, AUD-062 |

---

## 2. Lo que sí verifiqué, con resultado

Ejecutado el 2026-07-27 sobre el árbol de trabajo actual.

| Comprobación | Resultado |
|---|---|
| Suite completa (por tramos) | **1082 pruebas, 0 fallos, 3 omitidas** |
| `ruff check src/ tests/ scripts/ tools/ main.py` | All checks passed |
| `pylint --errors-only src/framework` | 0 errores |
| `scripts/validate_tmx.py --ci` | 2/2 mapas |
| `scripts/validate_assets.py` | 0 errores, 0 avisos |
| `scripts/generate_tmx_reference.py --check` | al día |
| `scripts/check_dependency_sync.py` | 15 dependencias coinciden |
| Cadena de escenas | Stage0 → BossVenadoScene → EndCreditsScene |
| Combate en ambas direcciones | verificado por prueba de mutación (§4) |

---

## 3. Correcciones al informe recibido, hallazgo por hallazgo

### 3.1 «568 tests» — cifra obsoleta

`pytest --co -q` devuelve **1082**. La diferencia no es cosmética: entre las
que faltaban en ese recuento están las 17 pruebas de integración que son las
únicas capaces de detectar los dos bugs críticos de esta sesión.

El informe además lista archivos de prueba que **no existen**
(`test_player.py`, `test_player.py:50+`) y omite once que sí:
`test_gameplay_integration.py`, `test_tmx_diagnostics.py`,
`test_tmx_validator.py`, `test_student_guidance.py`,
`test_toolchain_consistency.py`, `test_boss_encounter.py`,
`test_squad_brain.py`, `test_bestiary_roster.py`, `test_level_design_qa.py`,
`test_enemy_state_machine.py`, `test_scene_smoke.py`.

Un inventario de pruebas que nombra archivos inexistentes sugiere que se
construyó desde la documentación y no desde el disco.

### 3.2 «AUD-062 — Fixed» — no lo estaba cuando se escribió

El informe marca AUD-062 («Boss contact damage never applied») como resuelto.
En el momento de emitirse, el arreglo estaba escrito en el árbol de trabajo
**sin haberse ejecutado ni una vez**: el entorno de ejecución se había caído.
Lo dejé explícitamente sin confirmar y documentado en `PENDIENTE_VERIFICAR.md`
por ese motivo.

Ahora **sí** está verificado, y merece la pena decir cómo, porque «pasa la
prueba» no basta:

```
$ pytest tests/test_gameplay_integration.py -k Combat
4 passed

# quitando la línea del arreglo:
3 failed, 1 passed
```

Tres de las cuatro pruebas fallan sin el arreglo. Ésa es la evidencia de que
prueban algo; que pasen, por sí solo, no lo es.

### 3.3 «COD-004 … no-ops retenidos por compatibilidad … Acceptable»

Esta es la corrección más importante del documento.

`CollisionSystem.update_enemies()` era un no-op silencioso cuyo docstring
afirmaba: *«Enemy movement is integrated by EnemyBase.update; there is nothing
to sync here»*. La segunda mitad era falsa — **era el único sitio del proyecto
que llamaba a `EnemyBase.update`**, y también a `_check_player_contact`.

Consecuencia medida, no supuesta:

* ningún enemigo del juego se movía (0 llamadas a `update()` en 120 fotogramas);
* ninguno podía dañar al jugador;
* sus fotogramas de invencibilidad no corrían, así que 2000 golpes en 33 s
  bajaron la vida del jefe de 12,0 a 11,5.

Clasificar eso como «Acceptable» es exactamente el juicio que permitió que el
defecto sobreviviera a una auditoría entera. **AUD-063**: los dos no-ops ahora
emiten `DeprecationWarning`. Un método que no hace nada debe decirlo; el
silencio tranquilizador es lo que hizo daño.

### 3.4 Localización: 85/100 no es defendible

El propio informe enumera, en su sección de localización, que no hay toggle de
idioma, que las cadenas no están externalizadas y que el español es sólo
documentación. Eso describe un sistema de localización **inexistente**, no uno
de 85/100.

Medido:

```
grep -rn "import gettext\|from gettext" src/   → sin resultados
ls locales/                                    → no existe
ls docs/*.md | wc -l                           → 70
ls docs/*.es.md | wc -l                        → 1
grep -roh '"[A-Z][A-Za-z ]\{4,\}"' src/engine/scenes/*.py | wc -l → 310
```

70 documentos y **uno** con versión en español. La afirmación «65+ documentos
bilingües» del resumen ejecutivo es falsa: lo bilingüe es el informe de
auditoría, no el corpus.

### 3.5 Colisión de identificadores

El informe usa `AUD-001` para dos cosas distintas: el congelamiento por
hit-stop en `clock.py` (sección 12) y los canales huérfanos de música dinámica
(sección 7). Con 63 identificadores en uso, dos hallazgos con el mismo número
hacen imposible rastrear cuál se corrigió.

### 3.6 Cifras menores que no coinciden

| Informe | Real | Comando |
|---|---|---|
| «19+ player states» / «25 states documented» | 27 clases de estado | `grep -c 'class .*State' src/framework/entities/states/*.py` |
| «9 enemy types» | 30 tipos registrados para TMX | registro de `StageLoader` |
| «37 test files» | 61 | `ls tests/test_*.py tests/*/test_*.py \| wc -l` |
| «Test Coverage 88» | sin medición de cobertura ejecutada | — |

---

## 4. Hallazgo nuevo de esta pasada

### AUD-063 — Los no-ops silenciosos vuelven a ser ruidosos

**Severidad:** Media (mecanismo que causó dos críticos)
**Archivos:** `src/framework/stage/collision_system.py`
**Evidencia:** `update_enemies()` y `step()` retornaban `None` con docstrings
que sugerían que la ausencia de trabajo era correcta.
**Causa raíz:** conservar la firma «por compatibilidad» sin conservar el
contrato, y documentar la decisión con una afirmación no verificada.
**Impacto:** dos bugs de severidad crítica sobrevivieron a la auditoría porque
el código que los causaba parecía deliberado.
**Corrección:** ambos emiten `DeprecationWarning` describiendo dónde vive ahora
la responsabilidad.
**Validación:** `pytest -k NoOps` → 3 pruebas, incluida una que comprueba que
la escena no vuelva a delegar en ellos.
**Riesgo de regresión:** nulo; ninguna ruta de producción los invoca.

---

## 5. Puntuaciones corregidas

Sólo se corrigen las categorías donde la medición contradice al informe. El
resto se acepta.

| Categoría | Informe | Corregido | Por qué |
|---|---|---|---|
| Localización | 85 | **34** | No hay i18n, 310 cadenas fijas, 1 de 70 docs en español |
| Testing & QA | 95 | **88** | Las pruebas no detectaban que el juego no se jugaba |
| Cobertura de pruebas | 88 | **sin medir** | No se ejecutó cobertura; audio, VFX y sistemas de stage sin pruebas |
| Mantenibilidad | 82 | **74** | `StageScene` sigue en 1000 líneas; 30 de 34 escenas sin migrar al kit de UI |
| Documentación | 96 | **80** | Excelente en volumen; el corpus no es bilingüe y el índice de pruebas no coincide con el disco |
| **Global** | **91** | **~82** | Beta avanzada verificada, no «Production Ready» |

### Sobre el veredicto

«Production Ready» no es sostenible con:

- un sistema de localización que no existe, en un proyecto cuyo público es
  hispanohablante;
- 30 de 34 escenas sin migrar al kit de UI;
- audio, VFX y sistemas de escenario sin pruebas;
- y, sobre todo, con la lección de esta semana: **dos defectos que hacían el
  juego injugable sobrevivieron a una auditoría completa y a 1060 pruebas en
  verde**.

La calificación honesta es **Beta avanzada**: el motor arranca, el combate
funciona en ambas direcciones, el escenario se completa y la cadena llega a los
créditos — todo ello **verificado por ejecución hoy**. Eso es mucho, y es
menos que producción.

---

## 6. Lo que sigue sin verificar

Por honestidad, lo que este documento **no** puede afirmar:

- **Diversión.** Ninguna métrica automática la mide. Requiere personas jugando.
- **Balance.** Los valores de vida y daño no se han ajustado desde que el
  combate empezó a funcionar de verdad; hasta esta semana era imposible
  probarlos, porque los enemigos ni se movían.
- **Calidad visual y sonora.** No puedo juzgar si el pixel art se ve bien ni si
  la música acompaña.
- **Cobertura real.** No se ha ejecutado `pytest --cov`.
- **Rendimiento en la máquina del usuario.** Los benchmarks corren en un
  sandbox Linux headless, no en su Windows con GPU.
