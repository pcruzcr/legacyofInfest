"""
El sonido de muerte de un enemigo llega desde el golpe hasta el fichero .wav.

AUD-133 — una afirmación mía que era falsa
===========================================
En `docs/63_REGISTRO_DE_LO_NO_IMPLEMENTADO.md` escribí, sobre los sonidos de
muerte de enemigo:

    **No existen.** Los enemigos mueren en silencio.
    Es el hallazgo jugable.

**Era falso.** El barrido automático encontró que `05_ENEMY_SPEC.md` cita
`sfx_walker_die`, `sfx_flying_die` y `sfx_shooter_die`, y que ninguno de esos
tres identificadores existe. Eso sí es cierto. Lo que hice mal fue saltar de
«el nombre no existe» a «la función no existe», que son cosas distintas:

* el motor **sí** emite un sonido al morir un enemigo, desde `EnemyBase._die`;
* lo hace con dos nombres distintos —`SFX_ENEMY_DIE_SMALL` y `_LARGE`, según
  el tamaño del enemigo, que es mejor diseño que uno por especie—;
* `StageScene` los traduce a `sfx_enemies_die_small` y `sfx_enemies_die_large`;
* y los dos ficheros **están en el disco**, en `assets/sfx/enemies/`.

La especificación describe un esquema anterior. El código hace lo mismo mejor.

Por qué esto importa más que el error
--------------------------------------
Es exactamente el falso positivo contra el que escribí el propio script:

    «no entiende contexto, así que un documento puede citar legítimamente
     algo que aún no existe»

Puse el aviso en la herramienta y luego no me lo apliqué al interpretar su
salida. Una lista de hallazgos automáticos no es una lista de defectos hasta
que alguien comprueba cada uno **contra el código**, y eso es lo que hacen las
pruebas de abajo: recorren la cadena entera en vez de buscar un nombre.
"""
from __future__ import annotations

import pathlib

import pygame
import pytest

from src.engine.core.events import Events

RAIZ = pathlib.Path(__file__).resolve().parent.parent


class _BusEspia:
    def __init__(self) -> None:
        self.emitidos: list[str] = []

    def emit(self, nombre: str, **_datos) -> None:
        self.emitidos.append(nombre)

    def subscribe(self, *_a, **_k) -> None:
        pass

    def unsubscribe(self, *_a, **_k) -> None:
        pass


@pytest.fixture(autouse=True)
def _video():
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((320, 240))


def _matar(enemigo) -> list[str]:
    bus = _BusEspia()
    enemigo._event_bus = bus
    enemigo._die()
    return bus.emitidos


class TestElEnemigoNoMuereEnSilencio:
    def test_morir_emite_un_sonido(self) -> None:
        from src.framework.entities.enemy_walker import EnemyWalker

        emitidos = _matar(EnemyWalker(pygame.Vector2(0, 0)))
        sonidos = [e for e in emitidos if e.startswith("SFX_")]
        assert sonidos, (
            "un enemigo murió sin emitir ningún sonido. Es lo que yo afirmé "
            "en docs/63 sin comprobarlo, y era falso"
        )

    def test_tambien_emite_el_evento_de_muerte(self) -> None:
        """El sonido no debe sustituir al evento: los logros lo escuchan."""
        from src.framework.entities.enemy_walker import EnemyWalker

        assert Events.ENEMY_DIED in _matar(EnemyWalker(pygame.Vector2(0, 0)))

    def test_un_enemigo_grande_suena_distinto_de_uno_pequeno(self) -> None:
        """Dos sonidos por tamaño es mejor diseño que uno por especie.

        Con treinta especies, un sonido por especie son treinta ficheros que
        mantener y treinta oportunidades de que falte uno. Por tamaño son dos,
        y el jugador percibe lo mismo: si lo que murió era grande o pequeño.
        """
        from src.framework.entities.enemy_brute import EnemyBrute
        from src.framework.entities.enemy_walker import EnemyWalker

        pequeno = [e for e in _matar(EnemyWalker(pygame.Vector2(0, 0)))
                   if e.startswith("SFX_")]
        grande = [e for e in _matar(EnemyBrute(pygame.Vector2(0, 0)))
                  if e.startswith("SFX_")]
        assert pequeno != grande, (
            f"un Walker y un Brute emiten el mismo sonido al morir: "
            f"{pequeno} y {grande}"
        )


class TestLaCadenaLlegaHastaElFichero:
    """Emitir un evento no es sonar. Tres eslabones, tres comprobaciones."""

    def test_la_escena_traduce_el_evento_a_un_nombre_de_sonido(self) -> None:
        import inspect

        from src.framework.scenes.stage_scene import StageScene

        # Se lee la clase **y sus padres**: AUD-152 movió la tabla de sonidos
        # a un mixin, y mirar sólo `StageScene` habría dado un fallo que dice
        # «el enemigo muere en silencio» cuando lo único que pasó es que el
        # texto está una clase más arriba.
        fuente = "\n".join(
            inspect.getsource(c) for c in StageScene.__mro__
            if c.__module__.startswith("src.")
        )
        assert "sfx_enemies_die_small" in fuente
        assert "sfx_enemies_die_large" in fuente

    @pytest.mark.parametrize(
        "nombre", ["sfx_enemies_die_small", "sfx_enemies_die_large"],
    )
    def test_el_fichero_de_sonido_existe_en_el_disco(self, nombre) -> None:
        """El último eslabón, y el que más fácil se rompe al reorganizar."""
        ruta = RAIZ / "assets" / "sfx" / "enemies" / f"{nombre}.wav"
        assert ruta.exists(), (
            f"la escena pide «{nombre}» y no hay fichero: el enemigo moriría "
            f"en silencio y el jugador leería que el golpe no conectó"
        )

    def test_el_banco_registra_los_dos(self) -> None:
        """El banco escanea el directorio; si cambia el esquema, se entera."""
        from src.engine.audio.sound_bank import SoundBank

        directorio = getattr(SoundBank, "SFX_DIR", None)
        assert directorio is not None
        encontrados = {p.stem for p in pathlib.Path(directorio).rglob("*.wav")}
        assert {"sfx_enemies_die_small", "sfx_enemies_die_large"} <= encontrados


class TestLoQueLaEspecificacionSiTieneMal:
    """Separar el error real del que yo inventé.

    De las cinco cosas que `05_ENEMY_SPEC.md` promete y no existen, cuatro son
    nombres viejos de algo que sí está. La quinta es real.
    """

    def test_wind_up_no_existe_y_telegraphing_hace_su_trabajo(self) -> None:
        from src.framework.entities.enemy_base import EnemyState

        nombres = {s.name for s in EnemyState}
        assert "WIND_UP" not in nombres
        assert "TELEGRAPHING" in nombres, (
            "no hay ni WIND_UP ni TELEGRAPHING: los enemigos atacarían sin "
            "avisar, y eso no es dificultad, es injusticia"
        )

    def test_la_deteccion_existe_con_otro_nombre(self) -> None:
        """`detection_rect` no existe; `detection_range_x/y` sí."""
        from src.framework.entities.enemy_walker import EnemyWalker

        e = EnemyWalker(pygame.Vector2(0, 0))
        assert hasattr(e, "detection_range_x")
        assert hasattr(e, "detection_range_y")
