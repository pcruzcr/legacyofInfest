"""Candado de regresión para B-042: el destello blanco del impacto del STOMP
(`_dibujar_destello`, §2.2 del diseño AAA fase 2) debe recortar la silueta
VIVA del venado -- nunca pintar un rectángulo gris opaco sobre todo el área
del sprite. Ver `docs\\superpowers\\REGISTRO-DE-BUGS.md` B-042 y
`J:\\Centro de pruebas CPG I\\reports\\FINDINGS.md`, campaña
`bughunt_20260823` (filmstrip con zoom sobre el STOMP, f1816).
"""
import pygame

from src.stages.boss_venado.boss_venado import BossVenado

FONDO = (10, 10, 10)


def make_boss() -> BossVenado:
    return BossVenado(pygame.Vector2(3168, 240))


def test_destello_de_stomp_recorta_la_silueta_no_pinta_un_rectangulo_gris():
    """Reproduce B-042 por el camino REAL del destello: `_do_stomp()` arma
    `_flash_frames` exactamente igual que en una pelea real -- de paso fija
    el estado de animación a "stomp" (el sprite que el jugador ve durante el
    impacto, vía `_get_animation_key`) -- y `boss.draw()` es el mismo método
    que pinta al jefe en el juego real; nada de superficies fabricadas a
    mano ni de mocks del frame.

    Causa (confirmada empíricamente, ver `verify_fix2.py` de la sesión de
    diagnóstico): `_dibujar_destello` sube a blanco el RGB de TODO el rect
    del sprite con `BLEND_RGB_MAX` (ignora el alfa por completo -- también
    lo sube en los píxeles totalmente transparentes del fondo del PNG) y
    luego lo compone con `BLEND_RGBA_ADD`, que TAMPOCO pondera por alfa (no
    hay premultiplicación en ese modo de mezcla -- la misma lección de
    B-037/H-28): ese RGB "fantasma" de los píxeles de fondo se suma igual
    que el de los píxeles de cuerpo, y el resultado es un bloque gris
    parejo -- literalmente el MISMO valor en la esquina transparente que en
    el centro opaco -- en vez de una silueta.
    """
    boss = make_boss()
    boss._do_stomp()  # arma _flash_frames Y el estado de animación "stomp" real
    vivo = boss._frame_vivo()
    assert vivo is not None
    frame, destino, _clave = vivo
    alfa_original = pygame.surfarray.array_alpha(frame)
    fw, fh = frame.get_size()

    # Esquinas del frame REAL (medidas del propio sprite, no un número
    # mágico): el arte del venado deja transparente el fondo de su lienzo de
    # 48x48. Verificar la precondición aquí, no solo confiar en ella --  si
    # el arte cambiara algún día, este test debe fallar por su propia
    # precondición, no dar un falso verde.
    esquinas = [(0, 0), (fw - 1, 0), (0, fh - 1), (fw - 1, fh - 1)]
    for ex, ey in esquinas:
        assert alfa_original[ex, ey] == 0, (
            "precondición del test: la esquina del sprite debe ser transparente "
            "en el arte real -- si esto falla, el arte cambió y el test necesita "
            "otro punto de muestreo")

    # Al menos un píxel de cuerpo opaco real (centro del frame) para
    # confirmar que el destello SÍ enciende algo -- el fix no debe apagarlo.
    cx, cy = fw // 2, fh // 2
    assert alfa_original[cx, cy] == 255, (
        "precondición del test: el centro del sprite debe ser opaco en el arte real")

    offset = pygame.Vector2(int(boss.rect.centerx) - 100, int(boss.rect.centery) - 100)
    surface = pygame.Surface((200, 200))
    surface.fill(FONDO)
    boss.draw(surface, offset)

    def pixel_en_frame(local_x: int, local_y: int) -> tuple[int, int, int]:
        sx = int(destino[0] - offset.x) + local_x
        sy = int(destino[1] - offset.y) + local_y
        color = surface.get_at((sx, sy))
        return (color.r, color.g, color.b)

    for ex, ey in esquinas:
        color_esquina = pixel_en_frame(ex, ey)
        assert color_esquina == FONDO, (
            f"la esquina transparente del sprite ({ex},{ey}) no debe verse "
            f"afectada por el destello -- salió {color_esquina} en vez de "
            f"{FONDO}: volvió el rectángulo gris de B-042 (RGB fantasma "
            f"sumado sin ponderar por alfa)")

    color_centro = pixel_en_frame(cx, cy)
    assert color_centro != FONDO, "el destello debe iluminar el cuerpo (centro opaco del sprite)"
    assert sum(color_centro) > sum(FONDO), "el centro debe quedar más claro que el fondo, no más oscuro"


def test_destello_de_stomp_recorta_la_silueta_en_los_dos_frames_del_flash():
    """Repite el candado principal en CADA uno de los `FLASH_PISOTON_FRAMES`
    (2) fotogramas reales del destello, no solo en el primero -- por si el
    bug fuera intermitente frame a frame. Cada iteración rellena la
    superficie de nuevo (como hace el motor real cada fotograma) y verifica
    que la esquina transparente del sprite sigue siendo fondo puro mientras
    el centro opaco sí se enciende."""
    boss = make_boss()
    boss._do_stomp()
    vivo = boss._frame_vivo()
    assert vivo is not None
    frame, destino, _clave = vivo
    fw, fh = frame.get_size()
    cx, cy = fw // 2, fh // 2
    esquina = (0, 0)

    offset = pygame.Vector2(int(boss.rect.centerx) - 100, int(boss.rect.centery) - 100)
    surface = pygame.Surface((200, 200))

    def pixel_en_frame(local_x: int, local_y: int) -> tuple[int, int, int]:
        sx = int(destino[0] - offset.x) + local_x
        sy = int(destino[1] - offset.y) + local_y
        color = surface.get_at((sx, sy))
        return (color.r, color.g, color.b)

    for numero_de_frame in range(2):  # FLASH_PISOTON_FRAMES == 2
        assert boss._flash_frames > 0, f"el destello debe seguir activo en el frame {numero_de_frame}"
        surface.fill(FONDO)
        boss.draw(surface, offset)
        assert pixel_en_frame(*esquina) == FONDO, (
            f"frame {numero_de_frame} del destello: la esquina transparente "
            f"del sprite no debe verse afectada (B-042)")
        assert sum(pixel_en_frame(cx, cy)) > sum(FONDO), (
            f"frame {numero_de_frame} del destello: el centro opaco debe encenderse")
    assert boss._flash_frames == 0, "tras 2 fotogramas dibujados el destello debe agotarse"
