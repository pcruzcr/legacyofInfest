"""Las presencias errantes del fondo (AUD-562).

Qué piden y qué NO son
=======================
Jugado el nivel completo, el dueño pidió dos cosas encima de lo que ya
existía:

1. *«más fantasmas o figuras que se muevan como fantasma en el fondo»* —
   el nivel ya tenía la Cegua, la Bruja, el fantasma personal de la Fase 1
   y la anomalía ambigua, pero todos son apariciones puntuales de un solo
   sitio. Esto añade presencias menores que **patrullan** un tramo corto,
   en fases que hoy no tienen ninguna.
2. *«sería bueno agregar enemigos que no hagan daño, sino que simplemente
   sigan su camino, para llenar algo de estrés»* — el nivel tiene una
   regla de oro documentada en tres sitios (`docs/niveles/13_STAGE_4_1.md`
   regla 1, los comentarios de `siluetas.py`, y la prueba automática
   `tests/test_stage4_1.py::TestLaReglaDeOro::test_no_hay_un_solo_enemigo`)
   de **cero enemigos**. La resolución que aprobó el dueño (2026-08-19):
   fauna decorativa, no `EnemyBase` — la misma arquitectura que ya usa la
   sombra del Gavilán o la serpiente de fondo de la Fase 3. Se ve, cruza,
   no tiene colisión y no se puede tocar. La regla de oro y la prueba que
   la vigila siguen intactas.

Por eso `PresenciaErrante` no es una entidad del ECS: es un dato que
`Stage4_1._actualizar_presencias_errantes`/`_dibujar_presencias_errantes`
leen cada fotograma, exactamente igual que ya hacen `HORIZONTE_POR_FASE` o
`COLUMNAS_DE_HUESOS_FASE3`.

Por qué aparecen y desaparecen, no quedan fijas
--------------------------------------------------
Una figura parada en el mismo sitio todo el tramo se convierte en
decoración de fondo a los pocos segundos — dejaría de inquietar. Cada
presencia tiene su propia ventana de visibilidad aleatoria (mismo
mecanismo que ya usa la anomalía de la Fase 1, AUD-478): aparece, patrulla
un rato, se desvanece, puede volver a aparecer más tarde en otro punto de
su rango. Nunca se confirma qué es — ninguna dispara diálogo, sonido único
ni cambia el estado del nivel.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PresenciaErrante:
    """Una figura de fondo que patrulla un tramo corto de una fase."""

    id: str
    #: Número de `Fase` (1-6) en el que se ve. Fuera de esa fase no existe.
    fase: int
    #: Columna de mundo alrededor de la que patrulla.
    columna_centro: float
    #: Cuánto se aleja del centro a cada lado, en columnas.
    rango_columnas: float
    #: Segundos que tarda en ir de un extremo al otro y volver.
    periodo_patrullaje: float
    #: "fantasma" (contorno de `siluetas._fantasma`) o "infestado" (el
    #: sprite real de `WalkerEstudiante`, `enemy_walker_walk.png` — un
    #: infectado más, no un monstruo inventado: encaja con el lore de la
    #: infestación mejor que una silueta genérica).
    tipo: str
    color: tuple[int, int, int]
    #: Alto de la figura en píxeles de pantalla; el ancho sale de éste.
    alto: int
    #: Cuánto puede tardar en aparecer la próxima vez, y cuánto dura visible
    #: una vez que aparece — igual que `ESPERA_ENTRE_ANOMALIA_FASE1` /
    #: `DURACION_ANOMALIA_FASE1`, pero por presencia.
    espera: tuple[float, float]
    duracion: tuple[float, float]
    #: Alfa máximo (0-255) cuando está visible del todo.
    alfa: int = 130


# ── Las tres presencias del nivel ────────────────────────────────────
#
# Una por fase de las que hoy no tienen ninguna reforzando la sensación de
# "algo más se mueve aquí", repartidas para no acumular todas en un mismo
# tramo:
#
# * Fase 2 (El Venado): un infestado errante — la fase cuyo propio guion
#   pide *"la sensación de que algo observa o sigue al jugador"*; un
#   sobreviviente que ya no lo es, cruzando entre los árboles, es
#   literalmente esa sensación hecha figura.
# * Fase 3 (El Rey Terciopelo): un fantasma menor entre el camino de
#   huesos — no es la Bruja (que es un cameo de un instante en el
#   relámpago) ni el Rey Terciopelo (que testifica y asciende): alguien
#   más se quedó aquí.
# * Fase 5 (La Planicie de los Muertos): otro de los conquistadores que
#   el propio diseño ya menciona (*"representa también a los
#   conquistadores que murieron en este lugar"*) — vagando entre las
#   tumbas, no sólo nombrado en el texto.
PRESENCIAS: tuple[PresenciaErrante, ...] = (
    PresenciaErrante(
        "infestado_del_bosque", fase=2, columna_centro=210.0,
        rango_columnas=14.0, periodo_patrullaje=16.0, tipo="infestado",
        color=(20, 22, 18), alto=52, espera=(10.0, 18.0), duracion=(5.0, 9.0),
        alfa=150,
    ),
    PresenciaErrante(
        "fantasma_de_los_huesos", fase=3, columna_centro=355.0,
        rango_columnas=10.0, periodo_patrullaje=13.0, tipo="fantasma",
        color=(196, 202, 210), alto=64, espera=(8.0, 16.0), duracion=(4.0, 7.0),
        alfa=110,
    ),
    PresenciaErrante(
        "conquistador_errante", fase=5, columna_centro=680.0,
        rango_columnas=16.0, periodo_patrullaje=18.0, tipo="fantasma",
        color=(150, 156, 170), alto=64, espera=(9.0, 15.0), duracion=(5.0, 8.0),
        alfa=100,
    ),
)
