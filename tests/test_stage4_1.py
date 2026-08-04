"""
Nivel 4-1 — La Entrada al Cementerio.

Un nivel sin enemigos es un nivel donde **todo lo que hay es atmósfera**, y la
atmósfera es justo lo que se rompe sin que nadie se entere: un clima que no
cambia, un brasero que se apaga al retroceder o una visión espectral que no
revela nada se ven igual de bien en una captura de pantalla.

Así que estas pruebas no comprueban que las clases existan: mueven al jugador
por el mapa y **miran el resultado**.

Lo que defienden
-----------------
1. **La regla de oro.** Cero enemigos, contados sobre el mapa cargado.
2. **Que el fondo avance.** Cinco actos, cada uno con su clima, sus partículas
   y su luz — y que la progresión sea monótona, no un vaivén.
3. **Que los braseros sean la barra de progreso.** Se encienden al pasar y
   **no se apagan** al volver.
4. **Que la visión espectral revele.** Una huella que no se ve sin la visión y
   sí con ella, comprobada píxel a píxel.
5. **Que quepa en el presupuesto de fotograma.** Un efecto de pantalla completa
   a 60 fps es exactamente donde un nivel bonito se vuelve injugable.
"""
from __future__ import annotations

from itertools import pairwise

import pygame
import pytest

from src.engine.core import settings


@pytest.fixture(scope="module")
def _video():
    pygame.init()
    pygame.font.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((800, 600))


@pytest.fixture
def escena(_video):
    from src.engine.audio.audio_manager import AudioManager
    from src.engine.core.event_bus import EventBus
    from src.engine.core.game_context import GameContext
    from src.engine.core.save_manager import SaveManager
    from src.engine.input.input_manager import InputManager
    from src.engine.scene.scene_manager import SceneManager
    from src.framework.entities import entity_factory
    from src.stages.stage4_1.stage4_1 import Stage4_1

    entity_factory.ensure_registered()
    ctx = GameContext(
        input_manager=InputManager(), audio_manager=AudioManager(),
        scene_manager=None, event_bus=EventBus(), clock=None,
        save_manager=SaveManager(),
    )
    ctx.scene_manager = SceneManager(ctx)
    sc = Stage4_1(ctx)
    ctx.scene_manager.push(sc)
    yield sc
    sc.on_exit()


def _llevar_a(escena, fila: int, columna: int = 30) -> None:
    """Coloca al jugador en esa **fila** del pozo y espera a la cámara.

    Desde AUD-225 el nivel se baja, así que lo que sitúa al jugador en un acto
    es la fila y no la columna.

    La espera no es un número fijo de fotogramas: la cámara persigue con
    interpolación y aquí tiene 3.800 px de recorrido vertical. Con los cuatro
    fotogramas que bastaban en el mapa horizontal, la prueba de la visión
    espectral pedía un píxel que estaba fuera de la pantalla.
    """
    x = columna * settings.TILE_SIZE
    y = fila * settings.TILE_SIZE
    escena._player.rect.topleft = (x, y)
    escena._player.position.update(float(x), float(y))
    for _ in range(400):
        escena.update(1 / 60)
        objetivo = escena._player.rect.centery - settings.INTERNAL_HEIGHT / 2
        if abs(escena._camera.offset.y - objetivo) < 2.0:
            break


def _dentro_del_acto(numero: int) -> int:
    """Una fila que cae dentro del acto pedido, 1 a 5.

    Se calcula de la tabla y no se escribe a mano. Cuando el mapa cambió de
    forma (AUD-208 y AUD-225), las pruebas que apuntaban a coordenadas escritas
    a mano no fallaron: la del clima comprobaba el acto IV sobre una posición
    que ya era del acto II y **pasaba igual**, porque ahí también hay niebla.
    Una prueba que sigue en verde midiendo el sitio equivocado es peor que una
    que falla.
    """
    from src.stages.stage4_1.actos import ACTOS

    return ACTOS[numero - 1].desde_fila + 6


class TestLaReglaDeOro:
    """«Si el nivel aburre, se arregla con más marcas ocultas, no con
    serpientes.» — la ficha del nivel."""

    def test_no_hay_un_solo_enemigo(self, escena) -> None:
        from src.framework.entities.enemy_base import EnemyBase

        enemigos = [e for e in escena._stage_data.entity_list
                    if isinstance(e, EnemyBase)]
        assert enemigos == [], (
            f"el 4-1 tiene {len(enemigos)} enemigos y su regla de oro es cero"
        )

    def test_ni_siquiera_una_entidad(self, escena) -> None:
        """Se cuenta la lista entera, no sólo lo que hereda de `EnemyBase`.

        Un enemigo colocado por un tipo raro también contaría, y leer el XML
        no lo detectaría.
        """
        assert list(escena._stage_data.entity_list) == []

    def test_las_siluetas_no_son_entidades(self, escena) -> None:
        """El canon: «no atacan. Testifican.»"""
        from src.stages.stage4_1 import siluetas

        for _nombre, forma in siluetas.ESPIRITUS:
            assert callable(forma), "una silueta debe ser una forma, no un objeto"
        assert not hasattr(siluetas, "Enemigo")
        assert not hasattr(siluetas, "Cegua")


class TestNoHayTrampas:
    """AUD-225. La ficha llama a esto «travesía atmosférica» y prohíbe enemigos
    *«porque la tensión ya está»*. Tenía siete `DeathPit` y cinco `HazardZone`,
    y las zonas de daño **no se dibujan**: el motor sólo pinta las que suben, así
    que el jugador recibía daño desde un rectángulo invisible."""

    def test_no_queda_ni_un_foso(self, escena) -> None:
        assert escena._stage_data.death_pits == [], (
            f"quedan {len(escena._stage_data.death_pits)} fosos: el nivel es "
            f"un descenso, caer es el movimiento y no el castigo"
        )

    def test_no_queda_ni_una_zona_de_dano(self, escena) -> None:
        assert list(escena._stage_data.hazard_zones) == [], (
            "una zona de daño fija no la dibuja el motor: es daño invisible"
        )

    def test_el_mapa_no_declara_esos_tipos(self) -> None:
        """Se lee el XML además del mapa cargado. Si alguien vuelve a poner un
        `DeathPit` y el cargador lo ignora por otro motivo, esto lo ve."""
        from pathlib import Path

        xml = Path("assets/maps/stage4_1/stage4_1.tmx").read_text(encoding="utf-8")
        for tipo in ('type="DeathPit"', 'type="HazardZone"'):
            assert tipo not in xml, f"el TMX sigue declarando {tipo}"


class TestLasSuperficiesSeVen:
    """La regla del rediseño: **nada cambia el movimiento del jugador sin que se
    vea por qué**. Musgo verde que arrastra, lodo marrón que frena."""

    def _zonas(self, escena):
        from src.framework.ecs import ZonaDeFriccion

        return [z for _, z in escena._mundo.cada(ZonaDeFriccion)]

    def test_cada_repisa_de_musgo_arrastra(self, escena) -> None:
        from src.stages.stage4_1 import trazado

        arrastres = [z for z in self._zonas(escena) if z.arrastre]
        esperadas = len(trazado.INDICES_MUSGO)
        assert len(arrastres) == esperadas, (
            f"hay {esperadas} repisas de musgo y {len(arrastres)} zonas que "
            f"arrastran"
        )

    def test_cada_repisa_de_lodo_frena(self, escena) -> None:
        from src.stages.stage4_1 import trazado

        frenos = [z for z in self._zonas(escena) if z.multiplicador != 1.0]
        assert len(frenos) == len(trazado.INDICES_LODO)
        assert all(0.0 < z.multiplicador < 1.0 for z in frenos), (
            "un multiplicador >= 1 no frena: acelera o no hace nada"
        )

    def test_el_musgo_arrastra_hacia_el_hueco_y_no_contra_el(self) -> None:
        """Arrastrar hacia la pared sería empujar al jugador contra el sitio del
        que tiene que salir. Es la diferencia entre una ayuda y un castigo."""
        from src.stages.stage4_1 import trazado

        lista = trazado.repisas()
        for i in trazado.INDICES_MUSGO:
            x0, ancho, _fila = lista[i]
            hacia_la_derecha = x0 == trazado.MURO_ANCHO
            hueco_a_la_derecha = x0 + ancho < trazado.MW - trazado.MURO_ANCHO
            assert hacia_la_derecha == hueco_a_la_derecha, (
                f"la repisa de musgo {i} arrastra hacia el lado equivocado"
            )

    def test_musgo_y_lodo_se_pintan_distintos_del_suelo(self) -> None:
        """Si la baldosa fuera la misma, la superficie sería una trampa."""
        import sys
        from pathlib import Path

        sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
        from generate_stage4_1 import LODO, MUSGO, PIEDRA

        assert len({PIEDRA, MUSGO, LODO}) == 3

    def test_los_gid_apuntan_a_la_baldosa_que_dicen(self) -> None:
        """El contrato entre el mapa y la hoja de baldosas (AUD-237).

        Un GID es una posición en la hoja. Si alguien reordena `CEM_ORDEN` en el
        generador de assets y no toca las constantes del generador del mapa, el
        nivel se repinta entero con las baldosas equivocadas **sin que falle
        nada** — es exactamente cómo `stage_mecanicas` estuvo semanas pintando
        las tres primeras casillas de su hoja (AUD-115).
        """
        import sys
        from pathlib import Path

        sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
        from generate_all_assets import CEM_ORDEN
        from generate_stage4_1 import (
            LAPIDA_ALTA,
            LODO,
            LODO_RELLENO,
            LOSA,
            MURO,
            MUSGO,
            MUSGO_RELLENO,
            PIEDRA,
            RELLENO,
        )

        esperado = {
            "losa": PIEDRA, "relleno": RELLENO, "muro": MURO,
            "musgo": MUSGO, "musgo_relleno": MUSGO_RELLENO,
            "lodo": LODO, "lodo_relleno": LODO_RELLENO,
            "lapida_alta": LAPIDA_ALTA, "lapida_baja": LOSA,
        }
        for nombre, gid in esperado.items():
            assert CEM_ORDEN[gid - 1] == nombre, (
                f"el GID {gid} debería ser «{nombre}» y en la hoja es "
                f"«{CEM_ORDEN[gid - 1]}»: el nivel se pintaría con la baldosa "
                f"equivocada"
            )

    def test_la_hoja_del_cementerio_es_la_que_declara_el_mapa(self) -> None:
        """Y con el tamaño que declara: 128x128, 8 columnas, 64 baldosas."""
        import sys
        from pathlib import Path

        from PIL import Image

        sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
        from generate_stage4_1 import (
            TILESET,
            TS_COLUMNAS,
            TS_IMAGEN_PX,
            TS_TOTAL,
        )

        assert TILESET.endswith("tileset_cemetery.png"), (
            "el cementerio volvió a pintarse con la piedra del prólogo"
        )
        hoja = Image.open("assets/tilesets/tileset_cemetery.png")
        assert hoja.size == (TS_IMAGEN_PX, TS_IMAGEN_PX)
        assert TS_COLUMNAS * TS_COLUMNAS == TS_TOTAL

    def test_la_baldosa_pintada_coincide_con_la_zona(self) -> None:
        """La comprobación que de verdad importa: que la repisa que arrastra sea
        **la misma** que se pinta de verde. Una zona de fricción sobre una
        baldosa de piedra es exactamente el defecto que este nivel tenía."""
        import sys
        from pathlib import Path

        sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
        from generate_stage4_1 import BALDOSAS, _terreno

        from src.stages.stage4_1 import trazado

        g = _terreno()
        for x0, ancho, fila, material in trazado.superficies():
            esperada = BALDOSAS[material][0]
            fila_pintada = {g[fila][x] for x in range(x0, x0 + ancho)}
            assert fila_pintada == {esperada}, (
                f"la repisa de la fila {fila} es «{material}» y está pintada "
                f"con {fila_pintada}, no con {esperada}"
            )


class TestSuenaAOrgano:
    """AUD-227. La ficha pide órgano y sonaba un chiptune de onda cuadrada con
    caja de ritmos: `_gen_music_track` es el generador genérico de los otros
    diez temas. Esto no comprueba «que exista un fichero» —eso ya pasaba— sino
    las dos propiedades que distinguen un órgano de lo que había."""

    @staticmethod
    def _muestras():
        import struct
        import wave

        import numpy as np

        with wave.open("assets/music/bgm_final_approach.wav") as w:
            n, rate = w.getnframes(), w.getframerate()
            crudo = struct.unpack(f"<{n}h", w.readframes(n))
        return np.array(crudo, dtype=float) / 32768.0, rate

    def test_los_parciales_son_multiplos_enteros_de_la_nota(self) -> None:
        """Un registro de órgano **es** un armónico: un tubo que suena a un
        múltiplo entero de la fundamental. Si los picos no caen en múltiplos,
        no es un órgano, sea lo que sea."""
        import numpy as np

        x, rate = self._muestras()
        # El primer acorde, evitando el ataque y el fundido.
        tramo = x[int(1.0 * rate):int(3.0 * rate)]
        esp = np.abs(np.fft.rfft(tramo * np.hanning(len(tramo))))
        frec = np.fft.rfftfreq(len(tramo), 1.0 / rate)
        # Los diez picos más fuertes por encima de 30 Hz, separados entre sí.
        orden = np.argsort(esp)[::-1]
        picos: list[float] = []
        for i in orden:
            f = float(frec[i])
            if f < 30.0 or any(abs(f - p) < 4.0 for p in picos):
                continue
            picos.append(f)
            if len(picos) == 10:
                break

        import sys
        from pathlib import Path

        sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
        from generate_all_assets import ORGANO_ACORDES, ORGANO_PEDAL

        fundamentales = (*ORGANO_ACORDES[0], ORGANO_PEDAL[0])
        for pico in picos:
            assert any(
                abs(pico / f - round(pico / f)) < 0.04 and round(pico / f) >= 1
                for f in fundamentales
            ), (
                f"el pico de {pico:.1f} Hz no es múltiplo entero de ninguna nota "
                f"del acorde {fundamentales}: eso no es un registro de órgano"
            )

    #: Ataques bruscos por segundo que se toleran.
    #:
    #: No es un número inventado: está medido sobre los dos generadores. El
    #: órgano da 10 ataques en 16 s (0,63/s) —el ataque y la caída de cada uno de
    #: los cuatro acordes, más los dos fundidos— y el chiptune que sonaba antes
    #: da 43 en 10 s (4,3/s), porque mete un golpe de ruido blanco en cada
    #: pulso. Entre 0,63 y 4,3 hay sitio de sobra; 1,5 deja margen a los dos
    #: lados sin dejar pasar una caja de ritmos.
    ATAQUES_POR_SEGUNDO = 1.5

    def test_no_lleva_percusion(self) -> None:
        """Un órgano sostiene; el generador genérico golpea en cada pulso, y eso
        es lo que sonaba en un nivel donde «el silencio es el jefe»."""
        import numpy as np

        x, rate = self._muestras()
        ventana = int(rate * 0.02)
        energia = np.array([
            float(np.sqrt((x[i:i + ventana] ** 2).mean()))
            for i in range(0, len(x) - ventana, ventana)
        ])
        # Un golpe es un salto brusco de energía. Se cuentan los que superan
        # cuatro veces la mediana de los saltos.
        saltos = np.abs(np.diff(energia))
        golpes = int((saltos > 4.0 * np.median(saltos)).sum())
        por_segundo = golpes / (len(x) / rate)
        assert por_segundo <= self.ATAQUES_POR_SEGUNDO, (
            f"{golpes} ataques bruscos en {len(x) / rate:.0f} s "
            f"({por_segundo:.2f}/s): un órgano tiene uno por cambio de acorde, "
            f"no uno por pulso"
        )

    def test_el_nivel_apunta_a_esa_pista(self, escena) -> None:
        from src.stages.stage4_1.stage4_1 import Stage4_1

        assert Stage4_1.BGM_TRACK == "bgm_final_approach"
        assert escena._stage_data.bgm_track == Stage4_1.BGM_TRACK


class TestElLodoFrenaIgualEnCualquierMaquina:
    """AUD-236. `ZonaDeFriccion` multiplica la velocidad **sin escalar por
    `dt`**, y de ahí salió la sospecha de que el lodo del 4-1 frenara distinto
    según los fotogramas por segundo.

    Medido, es al revés de lo que parecía: el jugador reescribe `velocity.x`
    desde la entrada en cada fotograma y el multiplicador se aplica encima, así
    que se comporta como una **escala de velocidad** y sale igual a 30, 60 y
    120 fps. Esta prueba fija esa medición para que deje de ser una suposición.
    """

    def _recorrido(self, fps: int, con_entrada: bool) -> float:
        import pygame as pg

        from src.framework.ecs import (
            Transform,
            Velocidad,
            World,
            ZonaDeFriccion,
            systems,
        )
        from src.stages.stage4_1.trazado import FRENO_DEL_LODO

        dt = 1.0 / fps
        mundo = World()
        entidad = mundo.crear(
            Transform(posicion=pg.Vector2(0, 0), rect=pg.Rect(0, 0, 16, 32)),
            Velocidad(pg.Vector2(90, 0)),
        )
        mundo.crear(ZonaDeFriccion(
            rect=pg.Rect(-500, -500, 4000, 4000), multiplicador=FRENO_DEL_LODO,
        ))
        v = mundo.obtener(entidad, Velocidad)
        recorrido = 0.0
        for _ in range(fps):                 # un segundo
            if con_entrada:
                v.v.x = 90.0                 # andar es fijar la velocidad
            systems.sistema_friccion(mundo, dt)
            recorrido += v.v.x * dt
        return recorrido

    def test_andando_recorre_lo_mismo_a_cualquier_tasa(self) -> None:
        medidas = [self._recorrido(fps, True) for fps in (30, 60, 120)]
        assert max(medidas) - min(medidas) < 0.5, (
            f"el lodo frena distinto según los fps: {medidas}. Un nivel que se "
            f"juega distinto en dos máquinas no se puede calificar"
        )

    def test_frena_pero_deja_andar(self) -> None:
        """Un lodo que para al jugador no es lodo, es una pared."""
        andado = self._recorrido(60, True)
        assert 60.0 < andado < 88.0, (
            f"con el lodo se recorren {andado:.1f} px/s de los 90 normales"
        )

    def test_deslizarse_sin_empuje_si_depende_de_la_tasa(self) -> None:
        """La otra cara, documentada a propósito: sin entrada, cada fotograma
        vuelve a recortar lo que quedaba. Ese camino no lo recorre el jugador
        —fija su velocidad cada fotograma—, y por eso se deja como está en vez
        de meter un `** dt` que arreglaría el caso muerto y estropearía el vivo.

        Si algún día alguien conecta esto a un cuerpo que va sin empuje, esta
        prueba es la que le dice lo que va a encontrarse.
        """
        lento = self._recorrido(30, False)
        rapido = self._recorrido(120, False)
        assert lento > rapido * 2, (
            "si esto deja de cumplirse es que alguien tocó el sistema: "
            "reléase el docstring de ZonaDeFriccion antes de seguir"
        )


class TestElPozoNoEncierraANadie:
    """Un descenso con un sitio del que no se sale es peor que un foso: el foso
    al menos mata y devuelve al checkpoint."""

    def test_repisas_consecutivas_se_solapan(self) -> None:
        from itertools import pairwise

        from src.stages.stage4_1 import trazado

        for (x0, an, fila), (sx, san, sfila) in pairwise(trazado.repisas()):
            solape = min(x0 + an, sx + san) - max(x0, sx)
            assert solape > 0, (
                f"las repisas de las filas {fila} y {sfila} no se solapan: "
                f"desde la de arriba no se llega andando al hueco de la de abajo"
            )

    def test_se_puede_volver_a_subir(self) -> None:
        """80 px de desnivel contra 90,25 de salto. Con 96 —la primera versión—
        el calificador contaba 37 repechos imposibles."""
        from src.framework.stage.level_metrics import JumpEnvelope
        from src.stages.stage4_1 import trazado

        envolvente = JumpEnvelope.from_settings()
        desnivel = trazado.FILAS_POR_REPISA * trazado.TS
        assert desnivel < envolvente.max_height, (
            f"hay {desnivel} px entre repisas y el jugador sube "
            f"{envolvente.max_height}: el pozo no deja volver atrás"
        )

    def test_el_jugador_cabe_entre_dos_repisas(self) -> None:
        from src.stages.stage4_1 import trazado

        libre = (trazado.FILAS_POR_REPISA - trazado.GROSOR_REPISA) * trazado.TS
        assert libre >= 48, f"quedan {libre} px de hueco y el jugador mide 32"


class TestElNivelSePuedeJugar:
    def test_tiene_salida(self, escena) -> None:
        """La ficha la llama «Portal»; el motor sólo acepta `NextTrigger`."""
        assert escena._stage_data.next_trigger is not None

    def test_tiene_punto_de_aparicion_y_checkpoints(self, escena) -> None:
        assert escena._stage_data.spawn_point is not None
        assert len(escena._stage_data.checkpoints) >= 1

    def test_el_mapa_tiene_el_tamano_minimo(self, escena) -> None:
        """La ficha pide 1600×608 px. Es un **mínimo de superficie**, no de
        forma: desde AUD-225 el nivel es un pozo, así que se cumple a lo alto."""
        ancho, alto = escena._stage_data.map_pixel_size
        assert ancho * alto >= 1600 * 608, (
            f"la ficha pide al menos 1600x608 px de nivel y mide {ancho}x{alto}"
        )
        assert alto > ancho, (
            f"el 4-1 es un descenso: debería ser más alto que ancho, y mide "
            f"{ancho}x{alto}"
        )

    def test_la_escena_y_el_mapa_dicen_la_misma_zona(self, escena) -> None:
        """El 4-1 es de la zona 4 en el mapa y en la clase.

        Lo pilló la comprobación de mutación: poner `ZONE = 0` no rompía nada,
        y la zona es lo que decide la música, la progresión y en qué tramo del
        mundo cuenta este nivel.
        """
        from src.stages.stage4_1.stage4_1 import Stage4_1

        assert Stage4_1.ZONE == 4
        assert escena._stage_data.zone == Stage4_1.ZONE

    def test_el_reloj_va_de_las_19_a_las_23(self, escena) -> None:
        datos = escena._stage_data
        assert getattr(datos, "start_hour", None) == 19
        assert getattr(datos, "day_length", 0) == 900


class TestElFondoAvanzaConElJugador:
    """Los cinco actos. Sin esto el nivel es un pasillo con decoración."""

    def test_los_cinco_actos_se_alcanzan_en_orden(self, escena) -> None:
        vistos = []
        for numero in (1, 2, 3, 4, 5):
            _llevar_a(escena, _dentro_del_acto(numero))
            vistos.append(escena.acto.numero)
        assert vistos == [1, 2, 3, 4, 5], f"la progresión salió {vistos}"

    def test_cada_acto_ocupa_al_menos_una_pantalla(self) -> None:
        """AUD-208: con 20 baldosas por acto y 50 de pantalla, se veían dos
        actos y medio a la vez y la luna «bajaba un tramo» sin que el jugador
        se moviera de sitio. Un acto que no llena la pantalla no se lee como un
        acto."""
        from src.stages.stage4_1.trazado import ALTO_ACTO

        pantalla = settings.INTERNAL_HEIGHT // settings.TILE_SIZE
        assert ALTO_ACTO >= pantalla, (
            f"un acto mide {ALTO_ACTO} filas y la pantalla {pantalla}"
        )

    def test_el_clima_cambia_con_el_acto(self, escena) -> None:
        climas = {}
        for numero in (1, 3, 4, 5):
            _llevar_a(escena, _dentro_del_acto(numero))
            climas[escena.acto.numero] = escena._weather._climate
        assert climas[1] == "fog"
        assert climas[4] == "storm", "el acto de la tormenta no llueve"
        assert climas[5] == "clear", "el umbral no se queda en silencio"

    def test_el_acto_se_aplica_una_vez_y_no_en_cada_fotograma(
        self, escena,
    ) -> None:
        """El comentario del código lo dice: llamar a `set_climate` sesenta
        veces por segundo vacía el emisor de la tormenta y no se ve llover.

        Otro hallazgo de la comprobación de mutación: cambiar el `- 1` por un
        `+ 1` en la detección de cambio de acto dejaba todas las pruebas en
        verde y el clima reaplicándose sin parar.
        """
        _llevar_a(escena, _dentro_del_acto(4))
        veces = []
        original = escena._weather.set_climate
        escena._weather.set_climate = lambda c: (veces.append(c), original(c))[1]
        try:
            for _ in range(60):
                escena.update(1 / 60)
        finally:
            escena._weather.set_climate = original
        assert veces == [], (
            f"quieto dentro del acto IV, el clima se aplicó {len(veces)} veces"
        )

    def test_las_particulas_verdes_estan_encendidas(self, escena) -> None:
        """`spores` es el único efecto verde del motor, y el lore le pone al
        cementerio «luz espectral verde»."""
        _llevar_a(escena, _dentro_del_acto(2))
        assert escena._ambient_particles._particle_type == "spores"
        assert escena._ambient_particles.rate > 0.0

    def test_las_particulas_suben_hacia_la_tormenta(self, escena) -> None:
        _llevar_a(escena, _dentro_del_acto(2))
        pocas = escena._ambient_particles.rate
        _llevar_a(escena, _dentro_del_acto(4))
        muchas = escena._ambient_particles.rate
        assert muchas > pocas

    def test_la_luna_baja_y_crece(self) -> None:
        from src.stages.stage4_1.actos import ACTOS

        for anterior, siguiente in pairwise(ACTOS):
            assert siguiente.luna_y > anterior.luna_y, (
                f"la luna sube entre el acto {anterior.numero} y el "
                f"{siguiente.numero}: el reloj del nivel iría al revés"
            )
            assert siguiente.luna_radio > anterior.luna_radio

    def test_los_espiritus_se_acercan_y_no_se_van(self) -> None:
        from src.stages.stage4_1.actos import ACTOS

        for anterior, siguiente in pairwise(ACTOS):
            assert siguiente.espiritus >= anterior.espiritus
            assert siguiente.cegua >= anterior.cegua

    def test_el_umbral_es_el_acto_mas_claro(self) -> None:
        """En el acto V arden los doce braseros: tiene que verse."""
        from src.stages.stage4_1.actos import ACTOS

        assert ACTOS[-1].ambiente == max(a.ambiente for a in ACTOS)

    def test_solo_truena_en_la_tormenta(self) -> None:
        from src.stages.stage4_1.actos import ACTOS

        con_rayos = [a.numero for a in ACTOS if a.rayos_por_minuto > 0]
        assert con_rayos == [3, 4], (
            f"los rayos deben anunciarse en el III y caer en el IV; están en "
            f"{con_rayos}"
        )


class TestLosBraserosSonLaBarraDeProgreso:
    def test_arrancan_los_doce_apagados(self, escena) -> None:
        assert len(escena._luces) == 12
        assert escena.braseros_encendidos == 0
        assert all(luz.intensity == 0.0 for luz in escena._luces)

    def test_se_encienden_al_pasar(self, escena) -> None:
        for luz in list(escena._luces):
            escena._player.rect.center = (int(luz.position.x), int(luz.position.y))
            escena._player.position.update(luz.position)
            escena._actualizar_braseros(1 / 60)
        assert escena.braseros_encendidos == 12

    def test_la_llama_sube_en_vez_de_aparecer(self, escena) -> None:
        luz = escena._luces[0]
        escena._player.rect.center = (int(luz.position.x), int(luz.position.y))
        escena._player.position.update(luz.position)
        escena._actualizar_braseros(1 / 60)
        recien = luz.intensity
        for _ in range(60):
            escena._actualizar_braseros(1 / 60)
        assert 0.0 < recien < luz.intensity

    def test_no_se_apagan_al_volver(self, escena) -> None:
        """«El sendero queda marcado de luz detrás del jugador.»"""
        luz = escena._luces[0]
        escena._player.rect.center = (int(luz.position.x), int(luz.position.y))
        escena._player.position.update(luz.position)
        escena._actualizar_braseros(1 / 60)
        assert escena.braseros_encendidos == 1

        escena._player.rect.center = (5000, 200)
        escena._player.position.update(pygame.Vector2(5000, 200))
        for _ in range(30):
            escena._actualizar_braseros(1 / 60)
        assert escena.braseros_encendidos == 1, (
            "alejarse apagó el brasero: la barra de progreso retrocedería"
        )

    def test_el_ultimo_es_el_grande(self, escena) -> None:
        """El del umbral. Es la imagen final del nivel."""
        assert escena._luces[-1].radius > escena._luces[0].radius


class TestLaVisionEspectral:
    """La mecánica protagonista (Unidad VIII)."""

    def test_apagada_al_empezar(self, escena) -> None:
        assert escena.vision_activa is False

    def test_se_agota_sola(self, escena) -> None:
        escena._vision = 0.1
        for _ in range(12):
            escena._actualizar_vision(1 / 60)
        assert escena.vision_activa is False

    def test_no_se_puede_encadenar_sin_recarga(self, escena) -> None:
        escena._vision = 0.0
        escena._recarga = escena.RECARGA_DE_LA_VISION
        escena._actualizar_vision(1 / 60)
        assert escena.vision_activa is False

    def test_la_huella_solo_existe_con_la_vision(self, escena) -> None:
        """El corazón de la mecánica, comprobado píxel a píxel."""
        from src.stages.stage4_1.siluetas import VERDE_ESPECTRAL

        # Junto a la primera huella: tiene que estar en pantalla para poder
        # mirarle el color.
        marca = escena._marcas[0]
        _llevar_a(escena, marca.y // settings.TILE_SIZE - 2,
                  marca.x // settings.TILE_SIZE)
        marca = escena._marcas[0]

        def color_en_la_huella() -> tuple[int, int, int]:
            lienzo = pygame.Surface((800, 600))
            escena.draw(lienzo)
            off = escena._camera.offset
            return lienzo.get_at((int(marca.centerx - off.x),
                                  int(marca.centery - off.y)))[:3]

        assert color_en_la_huella() != VERDE_ESPECTRAL
        escena._vision = escena.DURACION_DE_LA_VISION
        assert color_en_la_huella() == VERDE_ESPECTRAL, (
            "la visión no reveló la huella: sin enemigos, ésta es la única "
            "mecánica del nivel"
        )

    def test_hay_huellas_en_los_actos_del_musgo_y_del_lodo(self, escena) -> None:
        from src.stages.stage4_1.actos import ACTOS
        from src.stages.stage4_1.trazado import ALTO_ACTO

        ts = settings.TILE_SIZE
        filas = [m.y // ts for m in escena._marcas]
        for numero in (3, 4):
            desde = ACTOS[numero - 1].desde_fila
            assert any(desde <= f <= desde + ALTO_ACTO for f in filas), (
                f"faltan huellas en el acto {numero}"
            )

    def test_cada_huella_marca_un_hueco_y_no_una_repisa(self, escena) -> None:
        """La huella dice «cae por aquí». Si cae sobre la repisa, miente.

        Es el fallo que AUD-208 quitó de raíz: las coordenadas de las huellas se
        escribían a mano en la escena y las del terreno en el generador, así que
        mover una desplazaba la otra y dejaba la marca donde no servía. Ahora
        las dos salen de `trazado.py` y esto lo comprueba.
        """
        from src.stages.stage4_1 import trazado

        ts = settings.TILE_SIZE
        por_fila = {fila: (x0, ancho) for x0, ancho, fila in trazado.repisas()}
        for marca in escena._marcas:
            fila = marca.y // ts + 1          # la repisa de la que se cae
            assert fila in por_fila, f"la huella de la fila {fila} no tiene repisa"
            x0, ancho = por_fila[fila]
            columnas = range(marca.x // ts, (marca.right - 1) // ts + 1)
            solapa = [c for c in columnas if x0 <= c < x0 + ancho]
            assert not solapa, (
                f"la huella de la fila {fila} cae sobre la repisa, en {solapa}: "
                f"debería marcar el hueco"
            )

    def test_la_vision_ilumina_y_no_oscurece(self, escena) -> None:
        """Lo primero que probé multiplicaba sobre la pantalla y el verde medio
        bajaba de 26 a 11. Una «visión» que quita luz no es una visión."""
        import numpy as np

        _llevar_a(escena, 44)
        lienzo = pygame.Surface((800, 600))
        escena.draw(lienzo)
        sin = np.asarray(pygame.surfarray.array3d(lienzo), dtype=int)[:, :, 1].mean()
        escena._vision = escena.DURACION_DE_LA_VISION
        escena.draw(lienzo)
        con = np.asarray(pygame.surfarray.array3d(lienzo), dtype=int)[:, :, 1].mean()
        assert con >= sin


class TestLasBrujasCruzanYNoSonEnemigos:
    """§4 del diseño: «2–3 cruzan con el relámpago». Estaban en el documento y
    en la checklist, y no en el juego (AUD-210)."""

    def test_no_hay_brujas_antes_de_la_niebla(self) -> None:
        from src.stages.stage4_1.actos import ACTOS

        assert [a.brujas for a in ACTOS[:2]] == [0, 0], (
            "las brujas aparecen en el III como anuncio del IV, no antes"
        )

    def test_la_tormenta_es_donde_mas_hay(self) -> None:
        from src.stages.stage4_1.actos import ACTOS

        assert ACTOS[3].brujas == max(a.brujas for a in ACTOS)

    def test_en_el_umbral_estan_quietas(self) -> None:
        """«Siluetas posadas en los árboles, quietas.»"""
        from src.stages.stage4_1.actos import ACTOS

        assert ACTOS[4].brujas_quietas is True
        assert [a.brujas_quietas for a in ACTOS[:4]] == [False] * 4

    def test_se_mueven_de_verdad(self, escena) -> None:
        """Una bruja que no cruza es una mancha en el fondo."""
        _llevar_a(escena, _dentro_del_acto(4))
        escena._rayo = escena.DURACION_DEL_RAYO

        def _pinta() -> pygame.Surface:
            lienzo = pygame.Surface((800, 600), pygame.SRCALPHA)
            escena._dibujar_brujas(lienzo, escena.acto, escena._camera.offset)
            return lienzo

        antes = pygame.surfarray.array3d(_pinta()).copy()
        escena._tiempo += 1.5
        assert not (pygame.surfarray.array3d(_pinta()) == antes).all()

    def test_no_son_entidades(self, escena) -> None:
        """La regla de oro no se negocia ni por el fondo."""
        assert list(escena._stage_data.entity_list) == []
        assert not hasattr(escena, "_brujas_entidades")


class TestLaOscuridadSusurraYNoCastiga:
    """§4: quedarse quieto a oscuras despierta al cementerio — y *«no hay daño
    ni castigo»* (AUD-211)."""

    def _a_oscuras_y_quieto(self, escena) -> None:
        escena._encendidos.clear()
        escena._quieto = 0.0
        escena._donde_estaba = float(escena._player.rect.centerx)
        for _ in range(int(escena.ESPERA_DEL_SUSURRO * 60) + 2):
            escena._actualizar_oscuridad(1 / 60)

    def test_a_oscuras_es_no_tener_braseros_cerca(self, escena) -> None:
        escena._encendidos.clear()
        assert escena.a_oscuras is True
        # Enciende el que tiene encima y deja de estarlo.
        escena._player.rect.center = (int(escena._luces[0].position.x),
                                      int(escena._luces[0].position.y))
        escena._encendidos.add(0)
        assert escena.a_oscuras is False

    def test_los_ojos_se_encienden_al_cabo_de_los_cuatro_segundos(
        self, escena,
    ) -> None:
        self._a_oscuras_y_quieto(escena)
        assert escena._ojos > 0.0

    def test_moverse_reinicia_la_cuenta(self, escena) -> None:
        escena._encendidos.clear()
        escena._donde_estaba = float(escena._player.rect.centerx)
        for _ in range(120):
            escena._player.rect.x += 3      # andando
            escena._actualizar_oscuridad(1 / 60)
        assert escena._ojos == 0.0, "el susurro llegó mientras el jugador andaba"

    def test_con_un_brasero_encendido_no_pasa_nada(self, escena) -> None:
        escena._player.rect.center = (int(escena._luces[0].position.x),
                                      int(escena._luces[0].position.y))
        escena._encendidos.add(0)
        escena._donde_estaba = float(escena._player.rect.centerx)
        for _ in range(400):
            escena._actualizar_oscuridad(1 / 60)
        assert escena._ojos == 0.0

    def test_no_quita_vida(self, escena) -> None:
        """La regla explícita del diseño. Es lo único que esta mecánica podría
        romper, y es lo que la haría estar mal."""
        antes = escena._player.current_health
        self._a_oscuras_y_quieto(escena)
        for _ in range(300):
            escena._actualizar_oscuridad(1 / 60)
        assert escena._player.current_health == antes


class TestElRelampagoEnsenaAntesDeCastigar:
    """«Ningún peligro aparece sin que un relámpago anterior lo haya
    mostrado.» — §5 del diseño."""

    def test_el_destello_sube_la_luz(self, escena) -> None:
        _llevar_a(escena, 65)
        base = escena._lighting.ambient_brightness
        escena._rayo = escena.DURACION_DEL_RAYO
        escena._actualizar_rayos(1 / 60)
        assert escena._lighting.ambient_brightness > base

    def test_el_destello_se_apaga(self, escena) -> None:
        _llevar_a(escena, 65)
        escena._rayo = escena.DURACION_DEL_RAYO
        for _ in range(40):
            escena._actualizar_rayos(1 / 60)
        assert escena._rayo == 0.0

    def test_no_hay_rayos_en_el_umbral(self, escena) -> None:
        """El silencio es el jefe."""
        _llevar_a(escena, 90)
        escena._rayo = 0.0
        for _ in range(600):
            escena._actualizar_rayos(1 / 60)
        assert escena._rayo == 0.0


class TestCabeEnElPresupuestoDeFotograma:
    #: 60 fps son 16,6 ms para todo. Un efecto de pantalla completa es donde un
    #: nivel bonito se vuelve injugable, así que se mide.
    PRESUPUESTO_MS = 12.0

    def _medir(self, escena, veces: int = 15) -> float:
        import time

        lienzo = pygame.Surface((800, 600))
        escena.draw(lienzo)          # calentar cachés
        t0 = time.perf_counter()
        for _ in range(veces):
            escena.draw(lienzo)
        return (time.perf_counter() - t0) / veces * 1000.0

    def test_el_dibujo_normal_cabe(self, escena) -> None:
        _llevar_a(escena, 44)
        assert self._medir(escena) < self.PRESUPUESTO_MS

    def test_con_la_vision_puesta_tambien(self, escena) -> None:
        _llevar_a(escena, 44)
        escena._vision = 999.0
        coste = self._medir(escena)
        assert coste < self.PRESUPUESTO_MS, (
            f"la visión cuesta {coste:.1f} ms por fotograma. Se umbraliza a 1/4 "
            f"de resolución justo por esto: a 1/2 medía 4,6 ms de más"
        )


class TestElMapaSigueAtadoASuGenerador:
    def test_el_tmx_es_el_que_produce_el_script(self) -> None:
        import sys
        from pathlib import Path

        raiz = Path(__file__).resolve().parent.parent
        sys.path.insert(0, str(raiz / "tools"))
        from generate_stage4_1 import DESTINO, generar

        assert DESTINO.read_text(encoding="utf-8") == generar(), (
            "stage4_1.tmx no coincide con su generador: ejecuta "
            "`python tools/generate_stage4_1.py`"
        )


class TestElGanchoDeFondoLlegaAlEscenario:
    """AUD-162 — sin él, la luna y las siluetas se dibujarían encima del
    jugador y dejarían de ser fondo."""

    def test_stage_scene_ofrece_el_gancho(self) -> None:
        from src.framework.scenes.stage_scene import StageScene

        assert hasattr(StageScene, "dibujar_fondo")

    def test_el_4_1_lo_sobreescribe(self) -> None:
        from src.framework.scenes.stage_scene import StageScene
        from src.stages.stage4_1.stage4_1 import Stage4_1

        assert Stage4_1.dibujar_fondo is not StageScene.dibujar_fondo

    def test_el_sistema_de_dibujo_lo_llama_antes_del_mapa(self) -> None:
        import inspect

        from src.framework.stage.drawing_system import DrawingSystem

        fuente = inspect.getsource(DrawingSystem.draw)
        i_fondo = fuente.index("fondo_del_escenario")
        i_mapa = fuente.index("_draw_stage_layers")
        assert i_fondo < i_mapa, (
            "el fondo del escenario se pinta después del mapa: taparía el nivel"
        )

    def test_un_fondo_que_falla_no_tumba_el_fotograma(self, escena) -> None:
        """Es decoración. El nivel tiene que seguir jugándose."""
        escena.dibujar_fondo = lambda *_a: 1 / 0
        lienzo = pygame.Surface((800, 600))
        escena.draw(lienzo)          # no debe lanzar
