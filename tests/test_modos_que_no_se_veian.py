"""AUD-201/202 — los dos modos que el jugador no podía ver.

Boss Rush entraba y se quedaba en negro
========================================
`TitleScene._activate_option` hace lo mismo en las once opciones: arrancar el
fundido y **luego** cambiar de pantalla. La rama de Boss Rush lo hacía al revés
—entraba al jefe y después pedía el fundido de salida— y ese orden importa,
porque `replace()` arranca el fundido de **entrada**. Invertido, el de salida
llegaba el último y ganaba.

`TransitionManager.update` deja `_fade_alpha = 255` al terminar un fundido de
salida, y `draw` pinta el velo negro siempre que el alfa sea mayor que cero, sin
mirar si la transición sigue activa. Así que no era un parpadeo: el jefe se
cargaba, se ejecutaba y sonaba debajo de una pantalla negra permanente.

El speedrun no existía para el jugador
=======================================
El cronómetro corría en todos los escenarios y nadie llegaba a ver un solo
número:

* `SpeedrunTimer.save()` no lo llamaba nadie, así que los tiempos vivían en
  memoria y morían con la escena;
* `LeaderboardScene` no leía la partida —pese a que su docstring lo prometía—
  sino que mostraba **tiempos escritos a mano**: «Stage 0: 1:23.45», «Boss
  Venado: 0:45.12». Números inventados presentados como récords del jugador;
* ninguna opción de menú llevaba a esa pantalla.

Un marcador que enseña cifras falsas es peor que no tener marcador: el jugador
que ve «1:23.45» sin haber jugado nunca aprende que el juego miente.
"""
from __future__ import annotations

import json

import pytest

from src.engine.core import settings


@pytest.fixture
def contexto(_pygame_init):
    """Un `GameContext` cableado como en producción."""
    import pygame

    from src.engine.audio.audio_manager import AudioManager
    from src.engine.core.event_bus import EventBus
    from src.engine.core.game_context import GameContext
    from src.engine.core.save_manager import SaveManager
    from src.engine.input.input_manager import InputManager
    from src.engine.scene.scene_manager import SceneManager
    from src.framework.entities import entity_factory

    pygame.display.set_mode((settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT))
    entity_factory.ensure_registered()

    ctx = GameContext(
        input_manager=InputManager(),
        audio_manager=AudioManager(),
        scene_manager=None,
        event_bus=EventBus(),
        clock=None,
        save_manager=SaveManager(),
    )
    ctx.scene_manager = SceneManager(ctx)
    return ctx


def _titulo(contexto):
    from src.engine.scenes.title_scene import TitleScene

    escena = TitleScene(contexto)
    # Por la pila real: `SceneManager.current` lee `_stack[-1]`, y colocar la
    # escena en un atributo inventado deja a `replace()` operando en el vacío.
    contexto.scene_manager.replace(escena)
    return escena


def _alfa_tras_la_transicion(contexto, opcion: str) -> int:
    """El alfa del velo negro cuando la transición ya ha terminado."""
    escena = _titulo(contexto)
    transicion = contexto.scene_manager.transition
    escena._activate_option(opcion)
    for _ in range(120):  # 2 s a 60 fps; el fundido dura 0,4 s
        transicion.update(1.0 / 60.0)
    return int(transicion._fade_alpha)


# ── Boss Rush ──────────────────────────────────────────────────


def test_boss_rush_no_deja_la_pantalla_en_negro(contexto) -> None:
    """Entrar al modo tiene que dejar el jefe **visible**.

    255 es negro opaco. Antes de AUD-201 ése era exactamente el valor final:
    el modo arrancaba bien y no se veía nada.
    """
    assert _alfa_tras_la_transicion(contexto, "BOSS RUSH") == 0


def test_boss_rush_termina_como_cualquier_otra_opcion(contexto) -> None:
    """La prueba de fondo: ninguna opción del título se comporta distinto.

    Se compara contra una pantalla que siempre funcionó en vez de fijar el
    número a mano, para que el día que cambie el sistema de transiciones esto
    siga midiendo «igual que las demás» y no «igual que en agosto de 2026».
    """
    referencia = _alfa_tras_la_transicion(contexto, "BESTIARY")
    assert _alfa_tras_la_transicion(contexto, "BOSS RUSH") == referencia


def test_boss_rush_encuentra_los_cuatro_jefes() -> None:
    """Si el pareo de escenarios se rompe, el modo se queda sin combates."""
    from src.engine.scenes.boss_rush_entry import escenarios_de_jefe

    jefes = escenarios_de_jefe()
    assert [stage_id for stage_id, _ in jefes] == [
        "stage1_4_boss_venado",
        "stage2_4_boss_rey",
        "stage3_4_boss_gavilan",
        "stage4_2_boss_paburu",
    ]


# ── Speedrun ───────────────────────────────────────────────────


def test_el_titulo_lleva_a_los_records(contexto) -> None:
    """Sin entrada de menú, la pantalla de récords no existe para el jugador."""
    escena = _titulo(contexto)
    etiquetas = [str(item.value) for item in escena._menu.items]
    assert "RECORDS" in etiquetas


def test_elegir_records_abre_la_pantalla_de_records(contexto) -> None:
    from src.engine.scenes.leaderboard_scene import LeaderboardScene

    escena = _titulo(contexto)
    escena._activate_option("RECORDS")
    assert isinstance(contexto.scene_manager.current, LeaderboardScene)


def test_alguien_anota_la_marca_al_terminar_un_escenario() -> None:
    """El defecto no era que la persistencia fallara: era que nadie la llamaba.

    Se comprueba el **cableado**, por AST, porque es la forma del fallo: un
    subsistema entero, terminado y probado, que ninguna parte del juego invoca.
    Ejercitar la persistencia a mano habria pasado desde el primer dia sin que
    el jugador viera jamas un tiempo.

    Mira `registrar_marca` y no `save`: AUD-231 cambio cual de las dos es la
    correcta aqui, y esta prueba tiene que seguir a la que de verdad alimenta la
    pantalla de records.
    """
    import ast
    import pathlib

    ruta = (pathlib.Path(__file__).resolve().parent.parent
            / "src" / "framework" / "scenes" / "stage_scene.py")
    arbol = ast.parse(ruta.read_text(encoding="utf-8"))

    nombres = {
        nodo.func.id
        for nodo in ast.walk(arbol)
        if isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Name)
    }
    assert "registrar_marca" in nombres, (
        "stage_scene.py cronometra la partida y no anota la marca en ningun "
        "sitio. Los tiempos mueren con la escena y la tabla de records no "
        "tiene que leer"
    )


def test_lo_que_escribe_el_cronometro_es_lo_que_lee_la_tabla(tmp_path) -> None:
    """Contrato entre quien escribe el fichero y quien lo muestra.

    Los dos lados se escribieron por separado y con años de diferencia; si el
    formato se mueve, esto lo dice antes que el jugador.
    """
    from src.engine.scenes import leaderboard_scene
    from src.framework.stage.speedrun_mode import SpeedrunTimer

    ruta = tmp_path / "speedrun.json"
    reloj = SpeedrunTimer()
    reloj.start()
    reloj.update(12.5)
    reloj.split("stage0")
    reloj.save(ruta)

    assert ruta.exists(), "el cronómetro no escribió nada"
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    assert datos["splits"][0]["stage_id"] == "stage0"
    assert datos["splits"][0]["time"] == pytest.approx(12.5)

    # Y el lector lo entiende sin traducción por medio.
    marcas = leaderboard_scene.mejores_tiempos(ruta)
    assert marcas["stage0"] == pytest.approx(12.5)


def test_la_tabla_de_records_no_inventa_tiempos(contexto, monkeypatch, tmp_path) -> None:
    """Sin partidas jugadas, la tabla no puede enseñar marcas.

    Antes mostraba «Stage 0: 1:23.45» y «Boss Venado: 0:45.12» escritos en el
    código. Un jugador recién instalado veía récords que nunca hizo.
    """
    from src.engine.scenes import leaderboard_scene

    monkeypatch.setattr(
        leaderboard_scene, "_RUTA_SPEEDRUN", tmp_path / "no_existe.json",
    )
    escena = leaderboard_scene.LeaderboardScene(contexto)
    escena.on_enter()

    lineas = " ".join(escena._lineas_de_tiempos())
    assert "1:23.45" not in lineas
    assert "0:45.12" not in lineas
    assert "--:--" in lineas, "sin datos, los huecos se marcan como vacíos"


def test_la_tabla_de_records_lee_los_tiempos_reales(
    contexto, monkeypatch, tmp_path,
) -> None:
    """Y cuando sí hay partida, enseña la de verdad."""
    from src.engine.scenes import leaderboard_scene

    ruta = tmp_path / "speedrun.json"
    ruta.write_text(json.dumps({
        "global_time": 65.0,
        "splits": [{"stage_id": "stage0", "time": 65.0}],
    }), encoding="utf-8")
    monkeypatch.setattr(leaderboard_scene, "_RUTA_SPEEDRUN", ruta)

    escena = leaderboard_scene.LeaderboardScene(contexto)
    escena.on_enter()
    lineas = " ".join(escena._lineas_de_tiempos())
    assert "1:05.00" in lineas, f"no aparece el tiempo guardado: {lineas}"


# ── El libro de récords tiene que acumular (AUD-231) ───────────


class TestLasMarcasSobrevivenAlNivelSiguiente:
    """AUD-231 — guardar el tiempo no basta si guardar borra el anterior.

    AUD-202 conecto `save()` al final de cada escenario y con eso la tabla dejo
    de inventarse los tiempos. Pero `StageScene.on_enter` llama a
    `SpeedrunTimer.start()`, y `start()` hace `_splits = []`. Es decir: entrar a
    un nivel vacia los parciales, y el `save()` del final escribe un fichero con
    **una sola marca** encima del anterior.

    Resultado medido: terminar `stage0` en 30 s y luego `stage1_1` en 45 dejaba
    en disco `{"splits": [{"stage_id": "stage1_1", "time": 45.0}]}`. La marca de
    `stage0` se perdia. La tabla de records solo podia ensenar el ultimo nivel
    jugado y `--:--.--` en los otros diez, que es casi tan inutil como los
    tiempos inventados que sustituyo.

    El fichero es un libro de records, no el diario de una partida: acumula, y
    una marca solo se pisa a si misma cuando mejora.
    """

    def test_terminar_un_nivel_no_borra_la_marca_del_anterior(self, tmp_path):
        from src.engine.scenes.leaderboard_scene import mejores_tiempos
        from src.framework.stage.speedrun_mode import registrar_marca

        ruta = tmp_path / "speedrun.json"
        registrar_marca("stage0", 30.0, ruta)
        registrar_marca("stage1_1", 45.0, ruta)

        marcas = mejores_tiempos(ruta)
        assert marcas == pytest.approx({"stage0": 30.0, "stage1_1": 45.0})

    def test_una_marca_solo_se_pisa_cuando_mejora(self, tmp_path):
        """Repetir un nivel y hacerlo peor no debe borrar el record."""
        from src.engine.scenes.leaderboard_scene import mejores_tiempos
        from src.framework.stage.speedrun_mode import registrar_marca

        ruta = tmp_path / "speedrun.json"
        registrar_marca("stage0", 30.0, ruta)
        registrar_marca("stage0", 41.0, ruta)
        assert mejores_tiempos(ruta)["stage0"] == pytest.approx(30.0)

        registrar_marca("stage0", 22.5, ruta)
        assert mejores_tiempos(ruta)["stage0"] == pytest.approx(22.5)

    def test_el_fichero_no_crece_sin_limite(self, tmp_path):
        """Una entrada por escenario, no una por partida jugada."""
        from src.framework.stage.speedrun_mode import registrar_marca

        ruta = tmp_path / "speedrun.json"
        for i in range(20):
            registrar_marca("stage0", 60.0 - i, ruta)
        datos = json.loads(ruta.read_text(encoding="utf-8"))
        assert len(datos["splits"]) == 1

    def test_un_fichero_ilegible_no_tumba_la_partida(self, tmp_path):
        """Anotar una marca ocurre al terminar un nivel: no puede lanzar."""
        from src.engine.scenes.leaderboard_scene import mejores_tiempos
        from src.framework.stage.speedrun_mode import registrar_marca

        ruta = tmp_path / "speedrun.json"
        ruta.write_text("{esto no es JSON", encoding="utf-8")
        registrar_marca("stage0", 30.0, ruta)
        assert mejores_tiempos(ruta)["stage0"] == pytest.approx(30.0)


# ── Qué es hoy el Boss Rush, y qué no (AUD-232 / GAP-030) ──────


class TestLoQueElBossRushHaceDeVerdad:
    """El modo se juega, pero no es el que la documentación describe.

    AUD-201 lo hizo visible. Al comprobar qué hace una vez dentro, aparece que
    `BossRushMode` se construye, se arranca con `start()` y **nadie vuelve a
    hablarle**: `context.boss_rush` se escribe y no lo lee ningún sitio, y
    `advance_to_next()` y `record_hit()` no se llaman desde fuera del módulo.
    El encadenado real lo hace la cola de escenarios normal del `SceneManager`.

    Consecuencias medidas, todas contra lo que promete `docs/44`:

    * la salud **no** se arrastra entre combates —`_carry_over_health` y
      `_carry_over_meter` se inicializan a 0.0, se reponen a 0.0 en `start()` y
      no tienen ni getter ni setter: la función no existe tampoco dentro del
      módulo—;
    * la puntuación nunca se calcula, porque la aplica `advance_to_next()`;
    * `hits_taken` se queda en 0, porque lo incrementa `record_hit()`.

    Lo que sí hay es un combate seguido contra los cuatro jefes, a vida llena
    cada vez. Es jugable y no está roto; simplemente no es lo especificado.

    Estas pruebas fijan **eso**, no lo deseable. El día que alguien conecte el
    arrastre de vida o la puntuación, fallan — y eso es lo que se busca: obliga
    a actualizar `docs/44` y GAP-030 en el mismo cambio, en vez de dejar que la
    especificación y el juego vuelvan a separarse en silencio.

    **Ese día llegó: AUD-261, el 4 de agosto de 2026.** Las dos pruebas que
    describían el hueco fallaron en cuanto `StageScene` empezó a conducir el
    modo, y con ellas en rojo no había forma de dar el cambio por terminado sin
    tocar `docs/44` §4 y `KNOWN_GAPS.md`. Se dan la vuelta y pasan a fijar lo
    contrario. La lección se queda escrita aquí: **una prueba que describe un
    hueco vale tanto como una que describe una función**, siempre que falle
    cuando el hueco se cierre.
    """

    def test_el_modo_encadena_los_cuatro_jefes(self, contexto) -> None:
        from src.engine.scenes.boss_rush_entry import empezar_boss_rush

        modo = empezar_boss_rush(contexto)
        assert modo is not None
        assert len(contexto.scene_manager._stage_queue) == 4

    def test_la_salud_ya_se_arrastra(self) -> None:
        """AUD-261 — esta prueba estaba escrita al revés, y a propósito.

        Decía «si esto falla, el arrastre se conectó: actualiza la spec». Falló
        el 4 de agosto de 2026, que es exactamente para lo que se escribió: la
        obligación de tocar `docs/44` y `KNOWN_GAPS.md` en el mismo cambio se
        cumplió porque una prueba la hizo imposible de olvidar.

        Lo que fija ahora es lo contrario: que el arrastre siga siendo API
        pública y no vuelva a ser un campo muerto.
        """
        from src.framework.stage.boss_rush_mode import BossRushMode

        modo = BossRushMode()

        assert hasattr(modo, "salud_arrastrada")
        assert hasattr(modo, "medidor_arrastrado")

    def test_el_juego_conduce_el_modo(self) -> None:
        """AUD-261, GAP-030 cerrado. Antes exigía que **nadie** lo condujera."""
        import ast
        import pathlib

        raiz = pathlib.Path(__file__).resolve().parent.parent / "src"
        conducen = set()
        for fichero in raiz.rglob("*.py"):
            if fichero.name == "boss_rush_mode.py":
                continue
            arbol = ast.parse(fichero.read_text(encoding="utf-8"))
            for nodo in ast.walk(arbol):
                if (isinstance(nodo, ast.Call)
                        and isinstance(nodo.func, ast.Attribute)
                        and nodo.func.attr in {"acreditar_combate", "record_hit",
                                               "registrar_tiempo"}):
                    conducen.add(fichero.name)
        assert conducen, (
            "nadie conduce el modo: la puntuación y el recuento de golpes han "
            "vuelto a estar muertos, que es GAP-030 otra vez"
        )
