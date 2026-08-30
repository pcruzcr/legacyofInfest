"""
generate_tmx_reference.py — Genera la tabla de tipos de objeto TMX desde el código.

Por qué existe (AUD-057)
------------------------
`docs/STAGE_CREATION.md` documentaba 8 tipos de enemigo. El motor registra 30.
Las 21 especies con nombre de `docs/18_ENEMY_ROSTER.md` —`WalkerInsect`,
`ShooterQuetzal`, `FlyingHalcon`…— estaban registradas y eran **inalcanzables
en la práctica**: nadie las iba a escribir en Tiled porque la guía de creación
de escenarios no decía que existieran.

Mantener esa tabla a mano garantiza que vuelva a desincronizarse la próxima vez
que alguien añada una especie. Este script la genera desde el registro real y
la escribe entre dos marcadores del documento, de modo que la lista publicada
no puede diferir de la que el cargador acepta.

Uso::

    python scripts/generate_tmx_reference.py           # reescribe el doc
    python scripts/generate_tmx_reference.py --check   # falla si está desfasado

El modo `--check` es el que corre en CI: no arregla nada, sólo avisa de que el
documento y el código han dejado de coincidir.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# El registro importa pygame, que sin esto intenta abrir una ventana real.
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

DOC = ROOT / "docs" / "STAGE_CREATION.md"
BEGIN = "<!-- BEGIN GENERATED: tipos de objeto -->"
END = "<!-- END GENERATED: tipos de objeto -->"


def build_table() -> str:
    """Tabla markdown con cada tipo aceptado en la capa `Objects`."""
    from src.framework.entities import bestiary_registry, entity_factory
    from src.framework.stage.stage_loader import StageLoader
    from src.framework.stage.tmx_diagnostics import BUILTIN_OBJECT_TYPES

    entity_factory.ensure_registered()
    registered = sorted(StageLoader._entity_registry)
    species = bestiary_registry.SPECIES

    lines = [
        BEGIN,
        "",
        "> Tabla generada por `scripts/generate_tmx_reference.py` desde el",
        "> registro real de entidades. No la edites a mano: añade la especie a",
        "> `bestiary_registry.SPECIES` y vuelve a ejecutar el script.",
        "",
        "### Tipos estructurales (capa `Objects`)",
        "",
        "| Type | Geometría | Propiedades |",
        "|---|---|---|",
    ]
    structural = {
        "PlayerSpawn": ("Punto", "— (la Y son los pies del jugador)"),
        "Checkpoint": ("Rectángulo", "`checkpoint_id` (int) **obligatoria**"),
        "NextTrigger": ("Rectángulo", "— (completa el escenario)"),
        "MessageTrigger": ("Rectángulo", "`text`, `duration`"),
        "MessageTrigger_Once": ("Rectángulo", "`text`, `duration` (una sola vez)"),
        "HazardZone": ("Rectángulo",
                       "`damage` (float, 0.25) · `sube` (px/s: la inundación) · "
                       "`sube_hasta` (y del mapa donde para) · "
                       "`arranca_con` (evento de un `EventTrigger`)"),
        "DeathPit": ("Rectángulo", "— (caer aquí mata)"),
        "CameraLock": ("Rectángulo", "`lock_x`, `lock_y` (bool)"),
        "Waypoint": ("Punto", "`owner_id` — ruta para la entidad con ese nombre"),
        "PushBlock": ("Rectángulo", "`velocidad` (px/s, 45) · `con_gravedad`"),
        "BreakableBlock": ("Rectángulo",
                           "`golpes` (int, 1) · `evento_al_romper`"),
        "Objective": ("Punto",
                      "`objective_id` **obligatoria** · `text` **obligatoria** · "
                      "`kind` (derrotar/recoger/bandera/hablar/llegar, «bandera») · "
                      "`target` (qué enemigo, objeto o bandera; vacío = cualquiera) · "
                      "`count` (int, 1) · `optional` (bool, false). "
                      "Sin geometría: un objetivo no ocurre en un sitio, ocurre "
                      "cuando pasa algo"),
        "Cutscene": ("Rectángulo o punto",
                     "`guion` **obligatoria** · `bloquea` · `saltable` · "
                     "`una_vez` · `arranca_con`. Punto = al empezar; "
                     "rectángulo = al entrar"),
        "Light": ("Punto o rectángulo (se usa el **centro**)",
                  "`radius` (px, 80) · `color` (nombre de la paleta o "
                  "`#rrggbb`) · `intensity` (0-1, 0.8) · `flicker` (bool) · "
                  "`flicker_speed` (Hz, 4.0) · `flicker_amount` (0-1, 0.15)"),
        "AmbientLightZone": ("Rectángulo",
                             "`valor` (brillo 0-1 dentro de la zona, 1.0 = sin "
                             "cambio) · `fundido` (px de transición del borde, "
                             "64). Mientras el jugador esté dentro, la luz "
                             "ambiental base vale `valor`; en la banda de "
                             "`fundido` interpola hacia el brillo del mapa "
                             "(AUD-598)"),
        "MusicZone": ("Rectángulo",
                      "`track` (nombre de pista sin extensión; cadena vacía = "
                      "silencio deliberado) · `fundido_ms` (entrada con "
                      "fundido, 800). Mientras el jugador esté dentro, la "
                      "sección manda sobre la intensidad de combate; al salir "
                      "vuelve la base del mapa (AUD-600)"),
        "CameraZoomZone": ("Rectángulo",
                           "`factor` (>1 acerca, <1 aleja; saturado 0.4-2.5, "
                           "0.75) · `segundos` (duración del tween, 1.5). "
                           "Dentro del rectángulo la cámara tiende al factor; "
                           "fuera vuelve a 1.0. La UI nunca escala (AUD-601)"),
        "ArenaZone": ("Rectángulo",
                      "— (sin propiedades: la geometría ES la arena). "
                      "Declara el cuadrilátero real del combate de jefe; sin "
                      "ninguna, el motor usa el mapa entero. Gana la primera "
                      "que contenga al jefe (AUD-605)"),
        # ── F4.1 — objetos con los que el jugador interactúa ──────
        "Pickup": ("Rectángulo o punto",
                   "`item_id` **obligatoria** (vale el nombre del objeto en "
                   "Tiled, o `key_id`) · `automatico` (bool, sí: se coge al "
                   "tocarlo) · `mensaje`"),
        "Key": ("Rectángulo o punto",
                "Alias de `Pickup`, mismas propiedades. Nombrarlo `Key` sólo "
                "hace el mapa legible en Tiled"),
        "Door": ("Rectángulo **obligatorio**",
                 "`key_id` (llave que la abre) · `consume_llave` (bool, no) · "
                 "`mensaje` (al intentar pasar sin llave) · `evento` (se emite "
                 "al abrir) · `abre_con` (evento que la abre sola) · "
                 "`cierra_en` (segundos: puerta cronometrada)"),
        "LockedDoor": ("Rectángulo **obligatorio**",
                       "Alias de `Door`, mismas propiedades"),
        "Cage": ("Rectángulo **obligatorio**",
                 "Igual que `Door` pero se dibuja como jaula"),
        "Chest": ("Rectángulo",
                  "`contenido` (o `item_id`: lo que entrega) · `key_id` (llave "
                  "que hace falta) · `mensaje` · `evento` (al abrir). Se abre "
                  "con el botón de interactuar y entrega una sola vez"),
        "EventTrigger": ("Rectángulo",
                         "`evento` **obligatoria** (vale el nombre del objeto) "
                         "· `automatico` (bool, sí: al entrar; no: hay que "
                         "pulsar) · `una_vez` (bool, sí) · `key_id`"),
        # ── F5.3-F5.6 — las once mecánicas de componente ECS ──────
        "WindZone": ("Rectángulo",
                     "`fuerza_x`, `fuerza_y` (px/s², 0) · `periodo` (s: con "
                     "valor, el viento sopla a rachas)"),
        "FrictionZone": ("Rectángulo",
                         "`multiplicador` (1.0; por debajo de 1 resbala) · "
                         "`arrastre` (px/s, 0)"),
        "Conveyor": ("Rectángulo",
                     "Igual que `FrictionZone`, pero `arrastre` vale 60 px/s "
                     "por defecto: una cinta sin arrastre no es una cinta"),
        "LaserZone": ("Rectángulo",
                      "`dano` (99: mata) · `encendido` (s, 1.0) · `apagado` "
                      "(s, 1.0) · `desfase` (s, 0: desincroniza dos láseres)"),
        "ShockwaveZone": ("Rectángulo",
                          "Alias de `LaserZone`, mismas propiedades"),
        "WaterZone": ("Rectángulo",
                      "`corriente_x`, `corriente_y` (px/s, 0). Dentro del agua "
                      "el jugador pasa al estado de nado"),
        "MovingPlatform": ("Rectángulo",
                           "`destino_dx`, `destino_dy` (px **relativos** a "
                           "donde la dibujaste) · `velocidad` (px/s, 40) · "
                           "`espera` (s en cada extremo, 0.5) · `atravesable` "
                           "(bool, no)"),
        "RhythmBlock": ("Rectángulo",
                        "`visible_seg` (1.0) · `oculto_seg` (1.0) · `desfase` "
                        "(s, 0) · `patron` (p. ej. `\"x.x.\"`: con patrón manda "
                        "la música y los segundos dejan de contar)"),
        "SinkingPlatform": ("Rectángulo",
                            "`retraso` (s antes de ceder, 0.4) · "
                            "`velocidad_caida` (px/s, 90) · `reaparece_en` "
                            "(s, 3.0)"),
        "ScrollZone": ("Rectángulo (el **disparador**, no la zona de muerte)",
                       "`velocidad_x` (px/s, 40) · `velocidad_y` (px/s, 0) · "
                       "`margen_de_gracia` (px que se puede rebasar el borde "
                       "antes de morir, 24) · `parar_en_x` (la cámara se "
                       "detiene ahí; sin ella, hasta el final del mapa). "
                       "Al pisarlo la cámara arranca sola y **el borde "
                       "izquierdo mata**: SMB3 Airship, Cuphead, Ori"),
        "Slope": ("Rectángulo (el **triángulo entero**, no la línea)",
                  "`sube` (`derecha` por defecto, o `izquierda`: dónde está el "
                  "lado alto). Suelo inclinado de verdad — la hipotenusa va de "
                  "esquina a esquina. **No se apila con bloques escalonados**: "
                  "eso es una escalera que frena al jugador en cada peldaño. "
                  "Sonic, DKC, Celeste (AUD-297)"),
        "WarpZone": ("Rectángulo (el disparador)",
                     "`destino_x` / `destino_y` (**obligatorias**: adónde van "
                     "los **pies** del jugador, en píxeles de mundo) · "
                     "`automatico` (al tocar, true) · `una_vez` (false) · "
                     "`key_id` · `enfriamiento` (s antes de poder repetirlo, "
                     "0.5) · `mensaje`. Teletransporta **dentro del mismo "
                     "mapa**, que es lo que `NextTrigger` no hace: Zelda, "
                     "Metroid, Hollow Knight. Sin destino no se carga y el "
                     "cargador avisa"),
        "BossSpawn": ("Punto (dónde entra el jefe)",
                      "`boss` (**obligatoria**: el nombre registrado del jefe, "
                      "p. ej. `BossVenado`). Produce la misma entidad que "
                      "escribir ese nombre como `type`; sin `boss`, o con uno "
                      "que no esté registrado, el cargador avisa. Lo pide "
                      "`17_BOSS_SPEC.md` §8.2 en todo mapa de jefe"),
        "PressurePlate": ("Rectángulo (el **botón** del suelo)",
                           "`evento` (**obligatoria**: la puerta con `abre_con` "
                           "igual se abre mientras la placa esté pisada) · "
                           "`requiere` (`bloque` por defecto, o `jugador`/`ambos`/ "
                           "`cualquiera`) · `mantener` (bool, true: al quitar el "
                           "peso la puerta se cierra; false la deja enclavada) · "
                           "`una_vez` (bool, false) · `mensaje`. Se activa con un "
                           "`PushBlock` encima y usa la misma lista de sólidos que "
                           "los bloques (no duplica composición)"),
        "PlacaDePresion": ("Rectángulo", "Alias de `PressurePlate`, mismas propiedades"),
        "PlacaPresion": ("Rectángulo", "Alias de `PressurePlate`, mismas propiedades"),
        "Boton": ("Rectángulo", "Alias de `PressurePlate`, mismas propiedades"),
        "Spring": ("Rectángulo (rebota en todo su ancho)",
                   "`impulso` (px/s, -520; negativo es hacia arriba) · "
                   "`rearme` (s, 0.15)"),
        "Guard": ("Punto",
                  "`mira_x`, `mira_y` (dirección, 1/0) · `alcance` (px, 160) · "
                  "`semiangulo` (grados, 30) · `barrido` (grados, 0: el cono "
                  "oscila) · `velocidad_barrido` (grados/s, 45)"),
        "Stalker": ("Punto",
                    "`velocidad` (px/s, 55) · `distancia_retirada` (px, 480) · "
                    "`reaparicion` (s, 6.0)"),
        "Vine": ("Rectángulo (alto = lo que se trepa)",
                 "`ancho_de_agarre` (px, 10) · `velocidad` (px/s de trepada, "
                 "70)"),
        "VineSwing": ("Rectángulo (pareja de lianas para saltar)",
                      "`largo` (px, 48) · `amplitud` (px, 28) · `periodo` "
                      "(s, 1.6) · `radio_agarre` (px, 20)"),
        "LianaSalto": ("Rectángulo", "Alias de `VineSwing`, mismas propiedades"),
        "RopeSwing": ("Rectángulo", "Alias de `VineSwing`, mismas propiedades"),
        "Zipline": ("Rectángulo (la esquina es el enganche)",
                    "`destino_dx` (px, 96), `destino_dy` (px, 64) "
                    "**relativos** · `velocidad` (px/s, 190) · "
                    "`radio_de_enganche` (px, 14) · `solo_de_bajada` "
                    "(bool, sí)"),
    }
    # AUD-182: antes esto era `structural.get(name, ("—", "—"))`, así que todo
    # tipo sin fila escrita a mano salía publicado como «— | —»: 22 de los 35.
    # El estudiante leía que `Conveyor` existe y no tenía forma de saber qué
    # propiedades acepta, ni de sospechar que las tenía. Y el `--check` del CI
    # no lo veía, porque compara el documento contra esta misma tabla: un gate
    # que verifica que el doc coincida con una tabla incompleta.
    #
    # Ahora falta un tipo es un error duro. `tests/test_referencia_tmx.py`
    # comprueba lo mismo antes de llegar aquí, para que el fallo salga como
    # prueba y no como excepción de un script.
    sin_documentar = [n for n in BUILTIN_OBJECT_TYPES if n not in structural]
    if sin_documentar:
        raise SystemExit(
            "Estos tipos de objeto los acepta el cargador pero nadie los ha "
            "documentado, así que saldrían en la guía como «—»:\n  "
            + "\n  ".join(sin_documentar)
            + "\n\nAñádelos a `structural` en scripts/generate_tmx_reference.py "
            "con su geometría y sus propiedades reales.",
        )
    for name in BUILTIN_OBJECT_TYPES:
        geometry, props = structural[name]
        lines.append(f"| `{name}` | {geometry} | {props} |")

    lines += [
        "",
        "### Arquetipos de enemigo (capa `Objects`, objetos punto)",
        "",
        "| Type | Ajustable con propiedades |",
        "|---|---|",
    ]
    archetype_props = {
        "Walker": "`patrol_length`, `facing`, `patrol_speed`, `alert_speed`, `damage_on_contact`",
        "Flying": "`flight_mode`, `flight_speed`, `sine_amplitude`, `sine_frequency`",
        # AUD-305 — `admite_bash` sólo aquí: es el único arquetipo cuyos
        # proyectiles pasan por `EnemyShooter._fire`, que es quien la hereda.
        # Ponerla en `Archer` o `Caster` la publicaría sin que hiciera nada.
        "Shooter": ("`fire_rate`, `projectile_speed`, `projectile_damage`, "
                    "`patrol_length`, `admite_bash` (bool, no: deja que el "
                    "jugador se impulse golpeando sus disparos)"),
        "Charger": "`charge_speed`, `patrol_speed`, `alert_speed`",
        "Archer": "`fire_rate`, `projectile_speed`",
        "Brute": "`patrol_speed`, `alert_speed`, `max_health`",
        "Caster": "`fire_rate`, `projectile_damage`",
        "Assassin": "`patrol_speed`, `alert_speed`",
    }
    for name, props in archetype_props.items():
        if name in registered:
            lines.append(f"| `{name}` | {props} |")

    lines += [
        "",
        "### Especies con nombre (capa `Objects`, objetos punto)",
        "",
        "Cada una es un arquetipo con sus valores ya puestos, tomados de",
        "`docs/18_ENEMY_ROSTER.md`. Puedes sobreescribir cualquiera con una",
        "propiedad del objeto en Tiled.",
        "",
        "| Type | Nombre | Zona | Vida |",
        "|---|---|---|---|",
    ]
    for species_id in sorted(species):
        spec = species[species_id]
        health = spec.params.get("max_health", "—")
        lines.append(
            f"| `{species_id}` | {spec.display_name} | {spec.zone} | {health} |",
        )

    lines += [
        "",
        "### Capa `Collision` (vocabulario distinto)",
        "",
        "| Type | Comportamiento |",
        "|---|---|",
        "| *(ninguno)* o `Solid` | Colisión AABB completa |",
        "| `Platform` | Plataforma atravesable desde abajo |",
        "",
        f"Total aceptado en `Objects`: **{len(registered) + len(BUILTIN_OBJECT_TYPES)}** tipos.",
        "",
        END,
    ]
    return "\n".join(lines)


def splice(document: str, table: str) -> str:
    """Sustituye el bloque generado, o lo añade si aún no existe."""
    if BEGIN in document and END in document:
        head = document[: document.index(BEGIN)]
        tail = document[document.index(END) + len(END):]
        return head + table + tail
    return document.rstrip() + "\n\n---\n\n## Referencia de tipos de objeto\n\n" + table + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check", action="store_true",
        help="No escribe; devuelve 1 si el documento está desfasado.",
    )
    args = parser.parse_args()

    document = DOC.read_text(encoding="utf-8")
    updated = splice(document, build_table())

    if args.check:
        if updated != document:
            print(
                f"{DOC.relative_to(ROOT)} está desfasado respecto al registro de "
                f"entidades.\nEjecuta: python scripts/generate_tmx_reference.py",
                file=sys.stderr,
            )
            return 1
        print(f"{DOC.relative_to(ROOT)}: al día")
        return 0

    if updated == document:
        print(f"{DOC.relative_to(ROOT)}: sin cambios")
        return 0

    DOC.write_text(updated, encoding="utf-8")
    print(f"{DOC.relative_to(ROOT)}: tabla de tipos actualizada")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
