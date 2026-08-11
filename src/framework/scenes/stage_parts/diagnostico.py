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
        # AUD-304 — ruff no ve el contexto entre llamada y handler: este método
        # sólo se invoca desde un `except Exception` (stage_scene.py), donde
        # `.exception()` sí tiene contexto de excepción vivo. Esa es la razón
        # por la que `.exception()` aquí es correcto y hay que conservarla.
        #
        # AUD-353 — la supresión de LOG004 que acompañaba a este comentario
        # se ha quitado: ruff movió esa regla a *preview*, así que con la
        # regla apagada la directiva pasó a ser RUF100 («supresión inútil») y
        # **el gate de lint del CI quedó en rojo sin que cambiara una línea
        # de este fichero**. Si LOG004 vuelve a activarse, el sitio donde
        # reponerla es éste, y el motivo sigue escrito arriba.
        #
        # (La directiva no se escribe literalmente en esta explicación: ruff
        # lee cualquier comentario que empiece por la palabra mágica, aunque
        # sea prosa, y avisaba de que la frase no era un código de regla.)
        #
        # AUD-408 — y se activó: LOG004 salió de *preview* en ruff 0.16.0,
        # exactamente el modo de fallo que GAP-034 describía. Vuelve la
        # directiva con la versión fijada en `pyproject.toml` (0.16.1) y la
        # explicación de por qué el falso positivo es legítimo. El bloque
        # de arriba queda como registro: la cadena completa de la regla es
        # preview → activa → preview → activa.
        logging.getLogger(__name__).exception(  # noqa: LOG004 — ver AUD-304/408
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
        # AUD-400 — los objetivos del mapa (GAP-047). Un objetivo que el
        # jugador no puede ver no sirve de nada, y ésta es la superficie que
        # este motor ya tiene para enseñar el estado de un escenario. La fila
        # sólo aparece si el mapa declara alguno, para que los diecisiete que
        # no lo hacen no ganen una línea vacía en la consola.
        objetivos = getattr(self, "_objetivos", None)
        if objetivos is not None and objetivos.objetivos:
            medidas["Objetivos"] = " · ".join(objetivos.resumen())

        # AUD-347 — los tiempos del ECS, que el planificador mide desde
        # siempre con `perf_counter` y nadie mostraba: la pregunta de F11
        # cuando el juego va lento es «cuál sistema», no «cuánto va el
        # juego». El total primero y los dos sistemas más caros después.
        planificador = getattr(self, "_planificador", None)
        if planificador is not None and planificador.total_ms() > 0.0:
            lento = planificador.tiempos()[:2]
            detalles = ", ".join(f"{n} {ms:.1f} ms" for n, ms in lento)
            medidas["ECS"] = f"{planificador.total_ms():.2f} ms | {detalles}"
        # AUD-362 — el ambiente del fotograma. Es la fila que faltaba para
        # poder depurar un escenario atmosférico: con la luz, la niebla y el
        # agarre saliendo todos de la misma simulación, «se ve raro» deja de
        # tener una causa evidente. Aquí están los cuatro números que la
        # explican, en el orden en que se propagan (hora → clima → humedad →
        # agarre), y `factor_friccion` en vez de `frenado_del_suelo` porque lo
        # que hay que poder leer de un vistazo es **cuánto** se ha perdido de
        # agarre, no el px/s² que sale de esa fracción.
        ambiente = getattr(self, "ambiente", None)
        if ambiente is not None:
            medidas["Ambiente"] = (
                f"{ambiente.hora:04.1f}h {ambiente.fase_del_dia} | "
                f"{ambiente.clima} | humedad {ambiente.humedad:.0%} | "
                f"agarre {ambiente.factor_friccion:.0%}"
            )
        # AUD-289 — arriba del todo si ha pasado, y ausente si no. Una fila
        # «Entidades retiradas: 0» permanente enseña a ignorarla, y el día que
        # ponga 1 nadie lo va a mirar.
        if self.entidades_retiradas:
            medidas["!! Entidades retiradas"] = ", ".join(
                sorted(set(self.entidades_retiradas)))
        return medidas

