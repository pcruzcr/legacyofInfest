"""
preview_tmx.py — mira tu escenario sin lanzar el juego.

F3.2 — el ciclo de trabajo del estudiante estaba abierto
--------------------------------------------------------
Hoy un estudiante coloca objetos en Tiled y **no ve nada** hasta lanzar el
juego, cargar la partida y caminar hasta la zona que acaba de tocar. Los focos
son el caso peor: en Tiled un `Light` es un rectángulo de 16x16 idéntico a
cualquier otro objeto, así que ajustar `radius` o `intensity` significaba una
partida entera por cada intento.

Esto renderiza el mapa entero de una vez —terreno, colisiones, objetos,
focos con su radio y su color reales, y la iluminación aplicada— y lo guarda
como PNG o lo muestra en una ventana. Segundos en lugar de minutos.

No sustituye a jugar el nivel. Sustituye a jugarlo **para ver dónde cae una
antorcha**, que es otra cosa.

Uso:
    python scripts/preview_tmx.py assets/maps/stage0/stage0.tmx
    python scripts/preview_tmx.py mi_mapa.tmx --salida vista.png
    python scripts/preview_tmx.py mi_mapa.tmx --sin-luz --con-etiquetas
    python scripts/preview_tmx.py mi_mapa.tmx --hora 22       # nocturno
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

_RAIZ = Path(__file__).resolve().parent.parent
if str(_RAIZ) not in sys.path:
    sys.path.insert(0, str(_RAIZ))

from scripts._cli_paths import display_path  # noqa: E402  (tras ajustar sys.path)

# AUD-254: el resumen dice «estación» y la consola de Windows escribía la «ó»
# en cp1252. La herramienta no moría —la «ó» sí existe en cp1252, así que el
# guardián de AUD-177 no la señalaba—, pero quien leyera la salida esperando
# UTF-8 recibía `estaciM-sn`: el alumno veía basura y la prueba que comprueba
# que el previsualizador informa de la estación estaba en rojo por eso.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

#: Colores del calco de diagnóstico. Coinciden con los que usa el modo de
#: depuración del juego (F1) para que lo aprendido aquí sirva allí.
COLORES = {
    "Solid": (200, 80, 80),
    "Platform": (80, 200, 120),
    "PlayerSpawn": (120, 200, 255),
    "Checkpoint": (255, 220, 100),
    "NextTrigger": (255, 140, 255),
    "DeathPit": (255, 60, 60),
    "HazardZone": (255, 140, 60),
    "Cutscene": (200, 120, 230),
    "PushBlock": (150, 120, 85),
    "BreakableBlock": (120, 115, 110),
    "MessageTrigger": (140, 140, 255),
    "MessageTrigger_Once": (140, 140, 255),
    "CameraLock": (180, 180, 180),
    "Light": (255, 230, 150),
}
COLOR_ENEMIGO = (255, 100, 100)


def _preparar_pygame(headless: bool) -> None:
    if headless:
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")


def construir_vista(
    tmx: Path,
    con_luz: bool = True,
    con_etiquetas: bool = False,
    hora: float | None = None,
):
    """Devuelve una superficie con el mapa completo dibujado.

    El mapa se dibuja **entero**, no una ventana: el objetivo es ver la
    composición del nivel de un vistazo, que es justo lo que el juego no
    permite porque sigue a la cámara.
    """
    import pygame
    from pytmx.util_pygame import load_pygame

    from src.framework.stage.stage_loader import StageLoader

    datos_tmx = load_pygame(str(tmx))
    ancho = datos_tmx.width * datos_tmx.tilewidth
    alto = datos_tmx.height * datos_tmx.tileheight
    lienzo = pygame.Surface((ancho, alto))
    lienzo.fill((18, 18, 24))

    # 1. Capas de tiles, en orden.
    for capa in datos_tmx.visible_layers:
        if not hasattr(capa, "tiles"):
            continue
        for x, y, imagen in capa.tiles():
            if imagen is not None:
                lienzo.blit(imagen, (x * datos_tmx.tilewidth,
                                     y * datos_tmx.tileheight))

    # 2. Iluminación, con las mismas reglas que el juego.
    stage = StageLoader.load(tmx)
    if con_luz:
        _aplicar_luz(lienzo, stage, datos_tmx, hora)

    # 3. Calco de diagnóstico encima: siempre visible, aunque haya luz.
    _dibujar_objetos(lienzo, datos_tmx, con_etiquetas)
    return lienzo, stage, (ancho, alto)


def _aplicar_luz(lienzo, stage, datos_tmx, hora: float | None) -> None:
    import pygame

    from src.framework.stage.day_night import luz_a_las
    from src.framework.stage.seasons import aplicar_tinte, estacion
    from src.framework.vfx.lighting import LightSource, LightSystem

    ambiente = getattr(stage, "ambient_light", None)
    if ambiente is None:
        ambiente = 0.62
    est = estacion(getattr(stage, "season", ""))

    if hora is None:
        hora = getattr(stage, "start_hour", None)
    if hora is None:
        hora = 12.0
    luz_hora = luz_a_las(float(hora))

    sistema = LightSystem(ambient_brightness=max(
        0.30, ambiente * luz_hora.factor_ambiente * est.factor_luz))
    sistema.ambient_color = aplicar_tinte(luz_hora.color, est)
    for spec in getattr(stage, "lights", []):
        sistema.add_light(LightSource(
            position=pygame.Vector2(*spec.position),
            radius=spec.radius, color=spec.color, intensity=spec.intensity,
        ))
    sistema.render(lienzo, pygame.Vector2(0, 0))


def _dibujar_objetos(lienzo, datos_tmx, con_etiquetas: bool) -> None:
    """Marca cada objeto con su color, y los focos con su radio real."""
    import pygame

    fuente = None
    if con_etiquetas:
        pygame.font.init()
        fuente = pygame.font.Font(None, 14)

    for capa in datos_tmx.layers:
        if not hasattr(capa, "__iter__") or not hasattr(capa, "name"):
            continue
        if capa.name not in ("Objects", "Collision"):
            continue
        for obj in capa:
            tipo = getattr(obj, "type", None) or getattr(obj, "class", None) or ""
            color = COLORES.get(tipo, COLOR_ENEMIGO)
            rect = pygame.Rect(
                int(obj.x), int(obj.y),
                max(2, int(obj.width or 8)), max(2, int(obj.height or 8)))

            if tipo == "Light":
                # El círculo de alcance es la razón de ser de esta herramienta:
                # en Tiled un foco es un cuadrado de 16 px y no hay forma de
                # saber si su radio de 130 llega a donde se pretende.
                props = dict(obj.properties or {})
                try:
                    radio = int(float(props.get("radius", 80)))
                except (TypeError, ValueError):
                    radio = 80
                pygame.draw.circle(lienzo, color, rect.center, radio, 1)
                pygame.draw.circle(lienzo, color, rect.center, 3)
            else:
                pygame.draw.rect(lienzo, color, rect, 1)

            if fuente is not None and tipo:
                etiqueta = fuente.render(tipo, True, color)
                lienzo.blit(etiqueta, (rect.x, max(0, rect.y - 12)))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Previsualiza un escenario TMX sin lanzar el juego")
    parser.add_argument("tmx", help="ruta al archivo .tmx")
    parser.add_argument("--salida", help="guardar como PNG en vez de abrir ventana")
    parser.add_argument("--sin-luz", action="store_true",
                        help="dibujar sin aplicar la iluminación")
    parser.add_argument("--con-etiquetas", action="store_true",
                        help="escribir el tipo junto a cada objeto")
    parser.add_argument("--hora", type=float,
                        help="hora del día a simular, de 0 a 24")
    args = parser.parse_args()

    ruta = Path(args.tmx)
    if not ruta.exists():
        print(f"No existe: {ruta}")
        return 1

    _preparar_pygame(headless=bool(args.salida))
    import pygame
    pygame.init()
    if pygame.display.get_surface() is None:
        # `StageLoader` construye un renderizador de pyscroll, que necesita un
        # modo de vídeo aunque no vayamos a usarlo.
        pygame.display.set_mode((640, 480))

    try:
        lienzo, stage, (ancho, alto) = construir_vista(
            ruta, con_luz=not args.sin_luz,
            con_etiquetas=args.con_etiquetas, hora=args.hora)
    except Exception as e:
        print(f"No se pudo dibujar {display_path(ruta, _RAIZ)}: "
              f"{type(e).__name__}: {e}")
        print("Ejecuta primero: python scripts/validate_tmx.py " + str(ruta))
        return 1

    print(f"{display_path(ruta, _RAIZ)}: {ancho}x{alto} px")
    print(f"  focos           : {len(getattr(stage, 'lights', []))}")
    print(f"  entidades       : {len(getattr(stage, 'entity_list', []))}")
    print(f"  puntos de control: {len(getattr(stage, 'checkpoints', []))}")
    print(f"  clima           : {getattr(stage, 'climate', '') or '(sin declarar)'}")
    print(f"  estación        : {getattr(stage, 'season', '') or '(sin declarar)'}")

    if args.salida:
        destino = Path(args.salida)
        pygame.image.save(lienzo, str(destino))
        print(f"\nGuardado en {destino}")
        return 0

    _mostrar(lienzo, ancho, alto, ruta)
    return 0


def _mostrar(lienzo, ancho: int, alto: int, ruta: Path) -> None:
    """Abre una ventana con la vista, escalada para que quepa en pantalla."""
    import pygame

    max_w, max_h = 1400, 800
    escala = min(1.0, max_w / ancho, max_h / alto)
    tam = (max(1, int(ancho * escala)), max(1, int(alto * escala)))
    pantalla = pygame.display.set_mode(tam)
    pygame.display.set_caption(f"Vista previa — {ruta.name}  (Esc para cerrar)")
    vista = pygame.transform.smoothscale(lienzo, tam) if escala < 1.0 else lienzo

    reloj = pygame.time.Clock()
    while True:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                return
            if evento.type == pygame.KEYDOWN and evento.key in (
                    pygame.K_ESCAPE, pygame.K_q):
                return
        pantalla.blit(vista, (0, 0))
        pygame.display.flip()
        reloj.tick(30)


if __name__ == "__main__":
    sys.exit(main())
