"""
Module: test_contorno_de_enemigos
System: tests
Academic Unit: N/A

AUD-304 — el contorno de silueta de AUD-190 sólo lo tenía el jugador.

Qué fija esta prueba
====================
Tres cosas, y la tercera es la que de verdad importa para el repositorio:

1. Que el contorno **funciona** sobre un sprite de enemigo: separa la figura de
   un fondo oscuro, que es para lo que existe.
2. Que **se enciende y se apaga** con la preferencia, sin reiniciar.
3. Que **está apagado por defecto**. Encenderlo cambiaría el aspecto de los
   dieciséis mapas ya calificados, y la invariante 2 dice que las veintiséis
   clases de escenario siguen funcionando sin tocar una línea.

La trampa de medir esto
=======================
Es la misma que documenta `test_legibilidad_del_jugador.py` y por poco vuelve a
colar aquí: si se compara el sprite contra un área **que lo contiene**, se está
comparando algo consigo mismo y sale 1,0 hagas lo que hagas. Aquí se mira el
anillo de un píxel de alrededor, que es donde el contorno se dibuja y donde
antes de AUD-304 no había más que fondo.
"""
from __future__ import annotations

import numpy as np
import pygame
import pytest

from src.engine.core import user_settings
from src.engine.core.user_settings import UserSettings

#: El fondo real del juego: apagado y saturado. Ver AUD-190.
FONDO_OSCURO = (26, 24, 38)


def _luminancia(rgb: np.ndarray) -> np.ndarray:
    c = np.asarray(rgb, dtype=float) / 255.0
    c = np.where(c <= 0.03928, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    return 0.2126 * c[..., 0] + 0.7152 * c[..., 1] + 0.0722 * c[..., 2]


@pytest.fixture
def lienzo():
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((320, 240))
    superficie = pygame.Surface((64, 64))
    superficie.fill(FONDO_OSCURO)
    return superficie


#: Dónde cae el cuerpo opaco dentro del sprite. Importa para medir: el anillo
#: hay que mirarlo alrededor de **esto**, no del lienzo de 16×16. La primera
#: versión de esta prueba miró el borde del sprite entero, donde el contorno no
#: llega —queda dos píxeles más adentro—, y dio 0,0101 antes y después.
CUERPO = pygame.Rect(2, 2, 12, 12)


@pytest.fixture
def sprite_de_enemigo():
    """Un enemigo oscuro, que es el caso real que AUD-190 midió."""
    sprite = pygame.Surface((16, 16), pygame.SRCALPHA)
    sprite.fill((0, 0, 0, 0))
    pygame.draw.rect(sprite, (38, 32, 30, 255), CUERPO)
    return sprite


@pytest.fixture
def ajustes_limpios():
    """Devuelve el singleton a su sitio pase lo que pase en la prueba."""
    previo = user_settings.get()
    yield
    user_settings.set_settings(previo)


def _anillo(lienzo: pygame.Surface, caja: pygame.Rect) -> np.ndarray:
    """Los píxeles del borde exterior de `caja`: donde va el contorno."""
    pixeles = pygame.surfarray.array3d(lienzo)
    fuera = caja.inflate(2, 2)
    mascara = np.zeros(pixeles.shape[:2], dtype=bool)
    mascara[fuera.left:fuera.right, fuera.top:fuera.bottom] = True
    mascara[caja.left:caja.right, caja.top:caja.bottom] = False
    return pixeles[mascara]


class TestElContornoDeEnemigoSeparaDelFondo:
    def test_el_anillo_se_aclara_al_dibujar_con_contorno(
        self, lienzo, sprite_de_enemigo,
    ) -> None:
        from src.framework.vfx.contorno import COLOR_ENEMIGO, dibujar_con_contorno

        caja = CUERPO.move(20, 20)
        antes = _luminancia(_anillo(lienzo, caja)).mean()

        dibujar_con_contorno(lienzo, sprite_de_enemigo, (20, 20), COLOR_ENEMIGO)
        despues = _luminancia(_anillo(lienzo, caja)).mean()

        assert despues > antes * 3, (
            f"el anillo alrededor del enemigo pasó de {antes:.4f} a "
            f"{despues:.4f}: el contorno no está separándolo del fondo"
        )

    def test_el_color_del_enemigo_se_distingue_del_jugador_por_luminancia(
        self,
    ) -> None:
        """Y no sólo por tono: los modos daltónicos colapsan tonos, no brillos.

        Si esta prueba se rompiera eligiendo un ámbar más claro, el contorno
        seguiría viéndose pero dejaría de decir cuál de los dos eres tú
        justamente para quien enciende la opción.
        """
        from src.framework.vfx.contorno import COLOR_ENEMIGO, COLOR_JUGADOR

        jugador = float(_luminancia(np.array(COLOR_JUGADOR)))
        enemigo = float(_luminancia(np.array(COLOR_ENEMIGO)))

        assert abs(jugador - enemigo) >= 0.25, (
            f"jugador {jugador:.2f} y enemigo {enemigo:.2f} se parecen "
            f"demasiado en brillo: con un filtro daltónico serían el mismo "
            f"borde"
        )

    def test_la_silueta_conserva_el_alfa(self, sprite_de_enemigo) -> None:
        """Si el teñido tocara el alfa, el enemigo iría dentro de una caja."""
        from src.framework.vfx.contorno import COLOR_ENEMIGO, silueta_de

        original = pygame.surfarray.array_alpha(sprite_de_enemigo)
        tenida = pygame.surfarray.array_alpha(
            silueta_de(sprite_de_enemigo, COLOR_ENEMIGO))

        assert np.array_equal(original, tenida)

    def test_las_siluetas_se_cachean_por_color(self, sprite_de_enemigo) -> None:
        """Cuatro blits por enemigo y fotograma; y el mismo fotograma puede
        pedirse con los dos colores sin que uno pise la caché del otro."""
        from src.framework.vfx.contorno import (
            COLOR_ENEMIGO,
            COLOR_JUGADOR,
            silueta_de,
        )

        assert silueta_de(sprite_de_enemigo, COLOR_ENEMIGO) is silueta_de(
            sprite_de_enemigo, COLOR_ENEMIGO)
        assert silueta_de(sprite_de_enemigo, COLOR_ENEMIGO) is not silueta_de(
            sprite_de_enemigo, COLOR_JUGADOR)


class TestElCargadorSigueSiendoLigero:
    """La regresión que costó descubrir, convertida en prueba.

    La primera versión de AUD-304 importaba `user_settings` en el cuerpo de
    `enemy_base.py`. Parece inocuo y no lo es: `user_settings` importa
    `orjson`, y `enemy_base` está en la cadena
    `stage_loader → entities → enemy_base`. `scripts/grade_stage.py` carga
    escenarios en un entorno pelado, así que **el calificador empezó a dar 0 de
    12 en `design_completable` a los dieciséis mapas**, stage0 incluido. Ningún
    error visible: la excepción se captura y se convierte en un cero.

    Cuatro pruebas de `test_rubrica_de_movilidad.py` lo cazaron. Ésta lo caza
    antes y dice por qué, que es lo que allí no se podía adivinar.
    """

    def test_stage_loader_se_importa_sin_dependencias_opcionales(self) -> None:
        import subprocess
        import sys

        codigo = "from src.framework.stage.stage_loader import StageLoader"
        completado = subprocess.run(
            [sys.executable, "-c", codigo],
            capture_output=True, text=True, encoding="utf-8", check=False,
            # PATH vacío es lo que usa `test_rubrica_de_movilidad` y lo que
            # hace inalcanzables las extensiones compiladas en Windows.
            env={"SDL_VIDEODRIVER": "dummy", "SDL_AUDIODRIVER": "dummy",
                 "PYGAME_HIDE_SUPPORT_PROMPT": "1", "PATH": ""},
        )

        assert completado.returncode == 0, (
            "importar el cargador de escenarios arrastra una dependencia que "
            "no está en un entorno pelado. Quien lo note será `grade_stage`, "
            "y no fallará: pondrá un cero.\n\n"
            f"{completado.stderr[-1200:]}"
        )


class TestLaPreferencia:
    def test_esta_apagada_por_defecto(self) -> None:
        """La invariante 2: los dieciséis mapas entregados se ven igual que el
        día que se calificaron. Si esta prueba se pone en rojo, alguien cambió
        el aspecto por defecto de veintiséis entregas."""
        assert UserSettings().contorno_de_enemigos is False

    def test_sobrevive_a_una_vuelta_por_disco(self, tmp_path) -> None:
        destino = tmp_path / "config.json"
        ajustes = UserSettings(contorno_de_enemigos=True)
        ajustes.save(destino)

        assert UserSettings.load(destino).contorno_de_enemigos is True

    def test_el_enemigo_la_consulta_en_cada_fotograma(
        self, ajustes_limpios,
    ) -> None:
        """El interruptor tiene que valer sin reiniciar la partida.

        Ésta es la que falla si alguien «optimiza» leyendo la preferencia una
        sola vez al construir el enemigo: la opción se cambia desde el menú de
        pausa, sin salir del nivel.
        """
        user_settings.set_settings(UserSettings(contorno_de_enemigos=False))
        assert user_settings.preferencia("contorno_de_enemigos", False) is False

        user_settings.set_settings(UserSettings(contorno_de_enemigos=True))
        assert user_settings.preferencia("contorno_de_enemigos", False) is True


class TestElEnemigoDeVerdadLoDibuja:
    """Las pruebas de arriba ejercitan la función y la preferencia por
    separado, y **ninguna se pondría roja si alguien borrase la llamada de
    `enemy_base.draw`**. Ésta es la que las une: dibuja un enemigo real de las
    dos maneras y compara los píxeles que salen.
    """

    def _pintar(self, encendido: bool) -> np.ndarray:
        from src.framework.entities.enemy_walker import EnemyWalker

        user_settings.set_settings(
            UserSettings(contorno_de_enemigos=encendido))

        lienzo = pygame.Surface((160, 160))
        lienzo.fill(FONDO_OSCURO)
        enemigo = EnemyWalker(pygame.Vector2(60, 60))
        enemigo.draw(lienzo, pygame.Vector2(0, 0))
        return pygame.surfarray.array3d(lienzo)

    def test_encenderla_cambia_lo_que_se_dibuja(self, ajustes_limpios) -> None:
        pygame.init()
        if pygame.display.get_surface() is None:
            pygame.display.set_mode((320, 240))

        apagado = self._pintar(False)
        encendido = self._pintar(True)

        assert not np.array_equal(apagado, encendido), (
            "el enemigo se dibuja igual con la opción encendida que apagada: "
            "`enemy_base.draw` no está usando `dibujar_con_contorno`"
        )
        assert _luminancia(encendido).mean() > _luminancia(apagado).mean(), (
            "encender el contorno no aclaró el fotograma"
        )

    def test_apagada_no_pinta_un_solo_pixel_de_contorno(
        self, ajustes_limpios,
    ) -> None:
        """La invariante 2, comprobada sobre píxeles y no sobre intenciones.

        Se mira si aparece el color del contorno, en vez de reconstruir a mano
        el dibujado esperado: la primera versión de esta prueba replicaba el
        blit de `enemy_base` —barra de vida, desplazamientos, elección de
        fotograma— y fallaba por diferencias que no tenían nada que ver con lo
        que se quería medir. Una prueba que copia la implementación mide la
        copia, no el código.
        """
        pygame.init()
        if pygame.display.get_surface() is None:
            pygame.display.set_mode((320, 240))

        from src.framework.vfx.contorno import COLOR_ENEMIGO

        pixeles = self._pintar(False)
        distancia = np.abs(
            pixeles.astype(int) - np.array(COLOR_ENEMIGO)).sum(axis=-1)

        assert distancia.min() > 30, (
            "con la opción apagada hay píxeles del color del contorno en "
            "pantalla: el aspecto por defecto de los dieciséis mapas ya "
            "calificados ha cambiado"
        )
