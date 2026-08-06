"""
El diagnóstico del escenario: qué publica en la consola y qué hace cuando una
entidad revienta.

Extraído de `stage_scene.py` en AUD-290 sin cambiar una línea de lógica.

Por qué estos dos juntos
========================
Los dos contestan a la misma pregunta —«¿qué está pasando aquí dentro?»— y los
dos nacieron el mismo día por el mismo motivo: este motor **ejecuta código de
veintiséis estudiantes** y hasta AUD-283/289 no tenía ni forma de mirar dentro
ni forma de sobrevivir a un fallo ajeno.

`medidas_de_depuracion` es lo que la consola de F11 enseña, y
`_retirar_entidad_rota` es lo que pasa cuando una entidad lanza en su `update`.
Se tocan: lo segundo alimenta a lo primero, porque una entidad retirada en
silencio sería peor que la excepción que sustituye.

Es un mixin, no un colaborador, por la misma razón que los otros cinco: una
entrega puede sobreescribir `medidas_de_depuracion` para publicar lo suyo, y con
un colaborador esa subclase dejaría de tener efecto sin decir nada.
"""
from __future__ import annotations

import logging
from typing import Any

from src.engine.core import settings
from src.framework.stage import culling


class DiagnosticoDeEscenario:
    """La consola y la red de seguridad del escenario.

    Espera de la escena: `_stage_data`, `_camera`, `_squad`, `_subtitles`,
    `_particle_system` y `entidades_retiradas`.
    """

    def _retirar_entidad_rota(self, entidad: Any) -> None:
        """Una entidad que lanza se va del nivel; el nivel sigue — AUD-289.

        Por qué esto existe
        -------------------
        Este motor **ejecuta código de veintiséis estudiantes**. Hasta AUD-289 no
        había red ninguna en el bucle de juego: un `IndexError` en el `update` de
        un enemigo de una entrega tumbaba el fotograma entero, `App` lo cazaba
        arriba del todo y devolvía al menú de título. Desde el asiento del
        estudiante eso se ve como «el juego se cierra», y el mensaje que explica
        qué pasó queda en un fichero de registro que nadie mira mientras juega.

        Al cargar sí había red desde AUD-055 (`StageErrorScene`): un `.tmx` mal
        formado enseña su diagnóstico en pantalla y `R` recarga. Faltaba la otra
        mitad, la de ejecución.

        Lo importante: **esto no silencia nada.** Registra con traza completa
        —`logger.exception`, al fichero de registro que AUD-268 dejó junto a las
        partidas—, lo apunta en `entidades_retiradas` para que la consola de F11
        lo enseñe mientras se juega, y retira a la entidad para que el fallo no
        se repita sesenta veces por segundo. Un `except` que se calla
        convertiría un fallo ruidoso en uno invisible, que es peor que el
        problema original.

        Y se puede apagar. `settings.AISLAR_FALLOS_DE_ENTIDAD = False` vuelve a
        propagar la excepción, que es lo que quiere quien está depurando el
        motor y necesita la traza donde ocurre.
        """
        if not getattr(settings, "AISLAR_FALLOS_DE_ENTIDAD", True):
            raise

        nombre = type(entidad).__name__
        logging.getLogger(__name__).exception(
            "la entidad %r falló en update() y se retira del nivel", nombre)
        # Se marca muerta **y** se saca de la lista: sólo lo primero la dejaría
        # sin dibujar pero seguiría recibiendo `set_player_ref` cada fotograma,
        # y `on_enemy_died` la contaría como una baja del jugador — puntuación y
        # monedas por un fallo de programación.
        entidad.is_alive = False
        entidad._was_alive = False
        if self._stage_data is not None:
            try:
                self._stage_data.entity_list.remove(entidad)
            except ValueError:
                pass
        self._squad.forget(entidad)
        self.entidades_retiradas.append(nombre)
        self._subtitles.push(f"[{nombre} falló y se retiró: mira el registro]")

    def medidas_de_depuracion(self) -> dict[str, object]:
        """Lo que este escenario publica en la consola (F11) — AUD-283.

        Las cuatro cuentas que hacen falta para decidir sobre rendimiento en
        este motor: cuántas entidades se están simulando de verdad —no cuántas
        hay, que con el culling de AUD-279 ya no es lo mismo—, cuántas
        partículas vivas, y qué está decidiendo la IA.

        Lo del escuadrón es lo que cierra un cabo suelto de su propio módulo:
        `SquadBrain.stats()` llevaba desde AUD-050 comentado como «introspección
        para el overlay de debug» **sin un solo llamante**. El dato se calculaba
        cada fotograma y no se enseñaba en ninguna parte.
        """
        from src.framework.entities.enemy_base import EnemyBase

        stage = self._stage_data
        entidades = list(stage.entity_list) if stage is not None else []
        vivos = [e for e in entidades if isinstance(e, EnemyBase) and e.is_alive]
        zona = culling.zona_activa(self._camera.offset)
        simulados = sum(1 for e in vivos if culling.se_simula(e, zona))

        particulas = 0
        sistema = getattr(self, "_particle_system", None)
        if sistema is not None:
            particulas = sum(em.count for em in sistema._emitters.values())

        stats = self._squad.stats
        medidas: dict[str, object] = {
            "Enemigos": f"{simulados} simulados de {len(vivos)} vivos",
            "Partículas": particulas,
            "Escuadrón": (
                f"{stats['fraccion_modelo'] * 100:.0f}% por modelo, "
                f"{int(stats['por_reglas'])} por reglas"
            ),
        }
        # AUD-289 — arriba del todo si ha pasado, y ausente si no. Una fila
        # «Entidades retiradas: 0» permanente enseña a ignorarla, y el día que
        # ponga 1 nadie lo va a mirar.
        if self.entidades_retiradas:
            medidas["!! Entidades retiradas"] = ", ".join(
                sorted(set(self.entidades_retiradas)))
        return medidas

