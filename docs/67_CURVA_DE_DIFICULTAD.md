---
document_id: "LOI-CURVA-067"
title: "La curva de dificultad, medida"
tags: ["diseno", "dificultad", "curva", "auditoria"]
source: "docs/67_CURVA_DE_DIFICULTAD.md"
date_processed: "2026-08-01"
---

# La curva de dificultad, medida

**Fecha:** 1 de agosto de 2026
**Se regenera con:** `python scripts/difficulty_curve.py --md`

---

## Por qué medirla

Quince escenarios de catorce autores distintos, y nadie los ha jugado
seguidos. «¿Está bien ordenado?» se venía respondiendo por intuición, y la
intuición del que escribió un nivel no sirve para juzgar ese nivel: quien lo
diseñó sabe dónde están las cosas.

Esto no dice si un nivel es **divertido**. Dice cuánto **exige**, con cinco
números que se pueden contar sin jugar: enemigos y peligros por pantalla,
saltos cerca del límite de lo posible, cuánto se pierde al morir y cuántas
mecánicas distintas hay que entender.

**El índice no es una nota.** Un 48 no es peor que un 17. Lo único que importa
es que la serie suba y que no lo haga a escalones.

---

## La medida de hoy

| # | Escenario | Pantallas | Enem./pant. | Pelig./pant. | Saltos exigentes | Sin checkpoint | Mecánicas | Índice |
|---|---|---|---|---|---|---|---|---|
| 1 | `stage0` | 2.0 | 4.5 | 1.0 | 1 | 368 px | 5 | **48.8** |
| 2 | `stage1_1` | 4.8 | 2.3 | 0.0 | 1 | 484 px | 0 | **23.5** |
| 3 | `stage1_2_la_soda` | 1.0 | 2.0 | 0.0 | 0 | 393 px | 0 | **17.5** |
| 4 | `stage1_3_las_aulas` | 4.0 | 3.0 | 1.0 | 0 | 640 px | 0 | **36.5** |
| 5 | `boss_venado` | 4.1 | 0.2 | 0.0 | 0 | 3280 px | 0 | **16.8** |
| 6 | `stage2_1_oficinas` | 4.0 | 2.0 | 0.0 | 0 | 3048 px | 0 | **30.0** |
| 7 | `stage2_2` | 2.4 | 2.9 | 0.4 | 1 | 455 px | 0 | **32.2** |
| 8 | `boss_rey` | 1.4 | 0.7 | 0.0 | 0 | 1120 px | 0 | **12.4** |
| 9 | `stage3_1_la_entrada_de_piedra` | 2.0 | 5.0 | 0.0 | 0 | 785 px | 0 | **34.9** |
| 10 | `stage3_3_el_patio` | 1.2 | 9.2 | 0.0 | 1 | 489 px | 0 | **36.4** |
| 11 | `boss_paburu` | 1.0 | 1.0 | 0.0 | 0 | 941 px | 0 | **13.4** |

Fuera de la curva a propósito: `hall` y `lobby_datacenter` (tránsito),
`stage_mecanicas` (laboratorio del profesor) y `stage3_4_boss_gavilan` (el
jefe no existe — ver `17_BOSS_SPEC.md` §0).

---

## Los tres hallazgos

### 1. El tutorial es el nivel más exigente del juego

`stage0` saca **48,8**, y no lo vuelve a superar nadie. Es el escenario donde
el jugador aprende a caminar, y tiene 4,5 enemigos y 1 peligro por pantalla:
más presión de combate que el patio del final y más peligros que ningún otro
nivel.

No es un fallo del escenario —está bien construido, y su nota de rúbrica es
130/130—: es un fallo de **orden**. Un tutorial enseña; para enseñar hace
falta sitio para equivocarse.

**Qué haría:** repartir. `stage0` mide dos pantallas y mete cinco mecánicas;
la primera pantalla debería tener un enemigo y ningún peligro.

### 2. Hay dos escalones de más del doble

* `stage1_2_la_soda` (17,5) → `stage1_3_las_aulas` (36,5)
* `boss_rey` (12,4) → `stage3_1_la_entrada_de_piedra` (34,9)

El primero es el que preocupa: dos niveles seguidos del mismo tramo, y el
segundo exige el doble. El segundo escalón es menos grave —se sale de un jefe,
y volver al mundo normal siempre sube— pero conviene mirarlo.

**Un escalón no es un nivel difícil.** El jugador no abandona en el nivel
difícil: abandona en el que **se vuelve** difícil de golpe sin haberle
enseñado nada nuevo.

### 3. Los jefes puntúan bajo, y está bien

`boss_venado` 16,8, `boss_rey` 12,4, `boss_paburu` 13,4. Un jefe tiene un
enemigo y ningún peligro de escenario, así que por definición saca poco en una
medida de densidad. **La medida no sabe leer un jefe** y no debe intentarlo:
por eso el detector de escalones los salta.

Lo que sí dice el número: `boss_venado` tiene 3.280 px sin checkpoint. Morir
allí cuesta un paseo largo.

---

## Lo que esta medida NO ve

Escrito aquí para que nadie construya encima suponiendo lo contrario:

* **La colocación.** Tres enemigos en fila india y tres rodeando una plataforma
  son el mismo número y dos niveles distintos.
* **La legibilidad.** Un peligro que no se ve a tiempo no es difícil: es
  injusto, y eso no se cuenta.
* **El ritmo.** Un nivel que alterna tensión y descanso se juega mejor que uno
  plano con la misma densidad.
* **La curva de aprendizaje.** Enseñar una mecánica y luego pedirla es diseño;
  pedirla sin enseñarla, también cuenta 1 en «mecánicas».

Para eso hay que jugarlos. Esto sirve para **saber por dónde empezar a
mirar**, que con quince niveles y un cuatrimestre es la mitad del trabajo.

---

## Documentos relacionados

- [[63_REGISTRO_DE_LO_NO_IMPLEMENTADO.md|Registro de pendientes]]
- [[60_GUIA_COMPLETA_DEL_MOTOR.md|Manual del diseñador]]
- [[17_BOSS_SPEC.md|Especificación de jefes]]
