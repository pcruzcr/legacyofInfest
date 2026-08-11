"""
Los sistemas: todo el comportamiento de las mecánicas nuevas.

F5.3 a F5.9 — qué hay aquí y por qué está junto
================================================
Cada función de este fichero es un sistema: recibe el mundo y el `dt`, recorre
las entidades que tienen los componentes que le interesan, y les cambia los
datos. Ninguna sabe de `EnemyBase`, de `Player` ni de `StageScene`, y ésa es
exactamente la propiedad que hacía falta: **el viento empuja a lo que tenga
`Transform` y `Velocidad`**, sea el jugador, un enemigo, una caja o un
proyectil.

Están en un solo fichero, y no en uno por mecánica, por una razón concreta: el
orden entre ellos importa más que la separación. Un `Ctrl+F` sobre este fichero
enseña la secuencia completa de un fotograma; repartidos en nueve módulos habría
que abrirlos todos para saber quién corre antes que quién. El día que esto pase
de mil líneas se parte por fases, no por mecánicas.

Las mecánicas que implementa, con su fuente:

* **Viento** — Mega Man 2 (Air Man), Celeste (Golden Ridge), Hollow Knight
  (Kingdom's Edge).
* **Fricción y arrastre** — Mega Man 2 (cintas), Hollow Knight (la miel).
* **Zonas letales temporizadas** — MGS (láseres), Mega Man 2 (Quick Man),
  Celeste (Templo de los Espejos), Inside (ondas de choque).
* **Agua** — Sonic (Labyrinth), SMB3 (Water Land), Inside (bosque sumergido).
* **Plataformas móviles y cintas** — Mega Man 2, Sonic, Donkey Kong Country.
* **Bloques rítmicos** — Mega Man 2 (Wily 1), Celeste (cassette).
* **Plataformas hundibles** — Cuphead (Perilous Piers).
* **Conos de visión y alerta** — MGS (Tank Hangar), Inside (la granja).
* **Acosador invulnerable** — RE3 (Nemesis), Celeste (el conserje), Metroid
  Dread (E.M.M.I.).
"""
from __future__ import annotations

import pygame

from src.framework.ecs.components import (
    Acosador,
    Alerta,
    BloqueRitmico,
    ConoDeVision,
    Efectos,
    EsJugador,
    Liana,
    Navegante,
    PlataformaHundible,
    PlataformaMovil,
    Resorte,
    Salud,
    Solido,
    Tirolesa,
    Transform,
    Velocidad,
    ZonaDeAgua,
    ZonaDeFriccion,
    ZonaDeViento,
    ZonaLetalTemporizada,
)
from src.framework.ecs.world import EntityId, World

# ══════════════════════════════════════════════════════════════
# Fase FUERZAS — modifican la velocidad antes de integrarla
# ══════════════════════════════════════════════════════════════


def sistema_resortes(mundo: World, dt: float) -> None:
    """Rebota a quien cae sobre un resorte.

    AUD-131 — corre en la fase de FUERZAS, **antes** de que el jugador
    resuelva su colisión, para que el impulso ya esté puesto cuando se
    integra. Si corriera después, el jugador aterrizaría sobre el resorte, la
    colisión le pondría la velocidad vertical a cero, y el rebote se perdería
    en el mismo fotograma en que se disparó.

    Sólo rebota quien **baja**: `v.v.y > 0`. Tocar el resorte de lado o desde
    abajo no hace nada, que es lo que el jugador espera al verlo.
    """
    for _, muelle in mundo.cada(Resorte):
        if muelle._espera > 0.0:
            muelle._espera = max(0.0, muelle._espera - dt)
        for entidad in mundo.con(Transform, Velocidad):
            t = mundo.obtener(entidad, Transform)
            if t is None or not muelle.rect.colliderect(t.rect):
                continue
            v = mundo.obtener(entidad, Velocidad)
            if v is None or v.v.y <= 0.0 or not muelle.listo:
                continue
            v.v.y = muelle.impulso
            muelle._espera = muelle.rearme


def sistema_viento(mundo: World, dt: float) -> None:
    """Empuja a todo lo que esté dentro de una zona de viento.

    Es aceleración y no velocidad fija a propósito. Fijar la velocidad haría
    que el viento **anulara** el movimiento del jugador —dentro de la zona daría
    igual lo que pulses—, y eso no es un obstáculo: es una pausa. Acelerando, el
    jugador puede luchar contra el viento, y esa lucha es la mecánica.
    """
    for _, zona in mundo.cada(ZonaDeViento):
        zona._t += dt
        if not zona.soplando:
            continue
        for entidad in mundo.con(Transform, Velocidad):
            t = mundo.obtener(entidad, Transform)
            if t is None or not zona.rect.colliderect(t.rect):
                continue
            v = mundo.obtener(entidad, Velocidad)
            if v is not None:
                v.v += zona.fuerza * dt


def sistema_friccion(mundo: World, dt: float) -> None:
    """Cambia el agarre y arrastra. Hielo, miel y cintas transportadoras.

    El arrastre se aplica **a la posición** y no a la velocidad. Si se sumara a
    la velocidad, saltar desde una cinta conservaría todo su empuje y saldrías
    disparado; sumándolo a la posición, la cinta te lleva mientras la pisas y te
    suelta al saltar, que es lo que hace Mega Man 2.
    """
    for _, zona in mundo.cada(ZonaDeFriccion):
        for entidad in mundo.con(Transform, Velocidad):
            t = mundo.obtener(entidad, Transform)
            if t is None or not zona.rect.colliderect(t.rect):
                continue
            v = mundo.obtener(entidad, Velocidad)
            if v is None:
                continue
            if zona.multiplicador != 1.0:
                v.v.x *= zona.multiplicador
            if zona.arrastre:
                t.posicion.x += zona.arrastre * dt
                t.rect.x = int(t.posicion.x)


def sistema_corriente_de_agua(mundo: World, dt: float) -> None:
    """El agua frena y arrastra. La parte de nado la lleva `SwimmingState`."""
    for _, agua in mundo.cada(ZonaDeAgua):
        if agua.corriente.length_squared() == 0.0:
            continue
        for entidad in mundo.con(Transform, Velocidad):
            t = mundo.obtener(entidad, Transform)
            if t is None or not agua.rect.colliderect(t.rect):
                continue
            v = mundo.obtener(entidad, Velocidad)
            if v is not None:
                v.v += agua.corriente * dt


# ══════════════════════════════════════════════════════════════
# Fase ESCENARIO — las superficies se mueven
# ══════════════════════════════════════════════════════════════


def sistema_plataformas_moviles(mundo: World, dt: float) -> None:
    """Mueve las plataformas y **anota cuánto se movieron**.

    El `delta` no es un dato de conveniencia: es lo único que permite al sistema
    de arrastre saber cuánto llevar al pasajero. Calcularlo allí obligaría a
    recordar la posición anterior de cada plataforma, que es guardar el mismo
    dato dos veces.
    """
    for entidad, plat in mundo.cada(PlataformaMovil):
        t = mundo.obtener(entidad, Transform)
        if t is None:
            continue
        antes = pygame.Vector2(t.posicion)

        if plat._espera_restante > 0.0:
            plat._espera_restante -= dt
            plat.delta.update(0, 0)
            continue

        objetivo = plat.destino if plat._hacia_destino else plat.origen
        hacia = objetivo - t.posicion
        distancia = hacia.length()
        paso = plat.velocidad * dt
        if distancia <= paso or distancia == 0.0:
            t.posicion.update(objetivo)
            plat._hacia_destino = not plat._hacia_destino
            plat._espera_restante = plat.espera
        else:
            t.posicion += hacia.normalize() * paso

        t.rect.topleft = (int(t.posicion.x), int(t.posicion.y))
        plat.delta.update(t.posicion - antes)


def sistema_bloques_ritmicos(mundo: World, dt: float) -> None:
    """Aparecen y desaparecen a compás.

    Quitar y poner el componente `Solido` es todo lo que hace falta: el sistema
    de colisión consulta quién es sólido cada fotograma, así que un bloque que
    deja de serlo deja de sostener a quien tenga encima **en el mismo
    fotograma**, y el jugador cae. Con herencia habría que avisar a alguien; con
    componentes, la ausencia del dato es el aviso.
    """
    reloj = mundo.recurso("reloj_musical")
    for entidad, bloque in mundo.cada(BloqueRitmico):
        bloque._t += dt
        # AUD-137 (F6): con patrón, el bloque **pregunta a la música** en qué
        # pulso va en vez de contar sus propios segundos. Contando segundos,
        # el bloque y la canción llevan relojes distintos y a los cinco
        # minutos van medio compás desfasados: es la razón por la que hasta
        # ahora no se podía hacer un nivel rítmico de verdad.
        if bloque.sigue_la_musica and reloj is not None:
            # AUD-250: el `desfase` se pasa también aquí. Antes sólo contaba en
            # el modo por segundos, así que escribir un `patron` hacía que todos
            # los bloques con el mismo ritmo entraran y salieran a la vez — un
            # semáforo en lugar de un ritmo.
            presente = reloj.presente_en_patron(bloque.patron, bloque.desfase)
        else:
            presente = bloque.presente
        tiene = mundo.tiene(entidad, Solido)
        if presente and not tiene:
            mundo.poner(entidad, Solido())
        elif not presente and tiene:
            mundo.quitar(entidad, Solido)


def sistema_plataformas_hundibles(mundo: World, dt: float) -> None:
    """Se hunden al pisarlas y vuelven solas."""
    for entidad, hund in mundo.cada(PlataformaHundible):
        t = mundo.obtener(entidad, Transform)
        if t is None:
            continue

        if hund._ausente > 0.0:
            hund._ausente -= dt
            if hund._ausente <= 0.0:
                t.posicion.y = hund.y_original
                t.rect.y = int(hund.y_original)
                hund._cayendo = False
                hund._pisada = 0.0
                mundo.poner(entidad, Solido(atravesable_desde_abajo=True))
            continue

        if hund._cayendo:
            t.posicion.y += hund.velocidad_caida * dt
            t.rect.y = int(t.posicion.y)
            if t.posicion.y > hund.y_original + 120:
                mundo.quitar(entidad, Solido)
                hund._ausente = hund.reaparece_en
        elif hund._pisada > 0.0:
            hund._pisada -= dt
            if hund._pisada <= 0.0:
                hund._cayendo = True


def marcar_pisada(mundo: World, plataforma: EntityId) -> None:
    """Avisa de que alguien pisó una hundible. Lo llama el sistema de colisión.

    Es una función y no un componente `Pisado` porque el dato vive un solo
    fotograma. Un componente que se pone y se quita cada fotograma ensucia el
    censo y no aporta nada que no aporte una llamada.
    """
    hund = mundo.obtener(plataforma, PlataformaHundible)
    if hund is not None and not hund._cayendo and hund._ausente <= 0.0 and hund._pisada <= 0.0:
        hund._pisada = hund.retraso


# ══════════════════════════════════════════════════════════════
# Fase ARRASTRE — las plataformas llevan a su pasajero
# ══════════════════════════════════════════════════════════════

#: Margen en px para considerar que algo va «encima» de una plataforma.
#:
#: Cero no vale: tras resolver la colisión el pasajero queda apoyado, con su
#: borde inferior exactamente en el borde superior de la plataforma, y un
#: `colliderect` de rectángulos que sólo se tocan da **False**. Con un píxel de
#: margen el apoyo se detecta, y con más de tres se detectaría a quien pasa
#: saltando por encima.
MARGEN_PASAJERO = 2


def sistema_arrastre_de_plataformas(mundo: World, _dt: float) -> None:
    """Mueve con la plataforma a quien va encima.

    **Esto es lo que casi nadie implementa**, y el motivo por el que las
    plataformas móviles «no funcionan» en la mitad de los proyectos: sin
    arrastre, el jugador se queda clavado en el aire mientras la plataforma se
    va, y parece un fallo de colisión cuando es un sistema que falta.

    Corre entre el movimiento de la plataforma y la resolución de colisiones,
    y no después. Después, el pasajero pasaría un fotograma hundido en la
    plataforma y saldría expulsado al siguiente.
    """
    for entidad, plat in mundo.cada(PlataformaMovil):
        if plat.delta.length_squared() == 0.0:
            continue
        tp = mundo.obtener(entidad, Transform)
        if tp is None:
            continue
        sensor = pygame.Rect(
            tp.rect.x, tp.rect.y - MARGEN_PASAJERO, tp.rect.width, MARGEN_PASAJERO + 1,
        )
        for pasajero in mundo.con(Transform, Velocidad):
            if pasajero == entidad:
                continue
            t = mundo.obtener(pasajero, Transform)
            if t is None or not sensor.colliderect(t.rect):
                continue
            t.posicion += plat.delta
            t.rect.topleft = (int(t.posicion.x), int(t.posicion.y))


# ══════════════════════════════════════════════════════════════
# Fase ZONAS — reaccionan a la posición ya resuelta
# ══════════════════════════════════════════════════════════════


def sistema_zonas_letales(mundo: World, dt: float) -> None:
    """Láseres, ondas de choque y trampas con ciclo.

    Se comprueba **después** de resolver colisiones: si se hiciera antes, un
    jugador que va a chocar contra una pared que lo saca de la zona moriría por
    una posición en la que nunca llegó a estar.
    """
    for _, zona in mundo.cada(ZonaLetalTemporizada):
        zona._t += dt
        if not zona.activa:
            continue
        for entidad in mundo.con(Transform, Salud):
            t = mundo.obtener(entidad, Transform)
            if t is None or not zona.rect.colliderect(t.rect):
                continue
            s = mundo.obtener(entidad, Salud)
            if s is not None and not s.invulnerable:
                s.actual = max(0.0, s.actual - zona.dano)


def liana_alcanzable(mundo: World, rect: pygame.Rect) -> Liana | None:
    """La liana que el jugador puede agarrar ahora mismo, si hay alguna.

    F5.14 — el margen de agarre es generoso a propósito. Con la anchura exacta
    de la cuerda —dos o tres píxeles— agarrarse sería un acto de puntería, y
    saltar hacia una liana y fallar por un píxel se lee como que el juego no
    responde, no como que el jugador falló.
    """
    for _, liana in mundo.cada(Liana):
        zona = liana.rect.inflate(liana.ancho_de_agarre * 2, 0)
        if zona.colliderect(rect):
            return liana
    return None


def tirolesa_alcanzable(mundo: World, rect: pygame.Rect) -> Tirolesa | None:
    """El cable al que el jugador puede engancharse, si hay alguno.

    Se mide contra el **punto más cercano del segmento**, no contra su caja
    envolvente: una tirolesa muy diagonal tiene una caja enorme y engancharía
    desde metros por debajo, donde el cable no está.
    """
    centro = pygame.Vector2(rect.center)
    for _, cable in mundo.cada(Tirolesa):
        cerca = cable.punto_mas_cercano(centro)
        if (cerca - centro).length() > cable.radio_de_enganche:
            continue
        if cable.solo_de_bajada and cable.destino.y < cable.origen.y:
            # Declarada de bajada pero dibujada hacia arriba: se engancha por
            # el extremo alto, no por donde caiga el jugador.
            continue
        return cable
    return None


def en_agua(mundo: World, rect: pygame.Rect) -> ZonaDeAgua | None:
    """La zona de agua que contiene a este rectángulo, si hay alguna.

    F5.6 — es la consulta que le faltaba a `SwimmingState`, y con ella el estado
    deja de ser inalcanzable. Se expone como función y no como sistema porque la
    máquina de estados del jugador necesita **preguntar**, no que le empujen un
    cambio desde fuera: quien decide en qué estado está el jugador es su máquina
    de estados, y meter mano desde un sistema sería el mismo desorden que se
    quiso evitar.
    """
    for _, agua in mundo.cada(ZonaDeAgua):
        if agua.rect.colliderect(rect):
            return agua
    return None


# ══════════════════════════════════════════════════════════════
# Fase IA — sigilo
# ══════════════════════════════════════════════════════════════


def rect_del_jugador(mundo: World) -> pygame.Rect | None:
    """Dónde está el jugador, preguntándoselo al mundo.

    F5.11 — antes esto era un parámetro. Pasarlo obligaba a que los sistemas de
    sigilo tuvieran una firma distinta al resto, y con firma distinta no caben
    en el `Planificador`: la escena tenía que llamar a los once sistemas a mano
    y en el orden correcto. Buscarlo por su marca devuelve la uniformidad, y con
    ella el orden vuelve a estar declarado en un solo sitio.
    """
    for entidad in mundo.con(EsJugador, Transform):
        t = mundo.obtener(entidad, Transform)
        if t is not None:
            return t.rect
    return None


def _hay_linea_libre(mundo: World, desde: pygame.Vector2,
                     hasta: pygame.Vector2) -> bool:
    """¿No hay geometría entre esos dos puntos? — AUD-381.

    La geometría llega por recurso del mundo, que es el canal que el ECS ya
    tiene para esto (`poner_recurso`, igual que `reloj_musical`). El escenario
    la publica una vez al montar; el sistema no conoce ni al escenario ni al
    cargador.

    **Sin recurso publicado devuelve `True`**, y eso es lo correcto, no una
    concesión: un mundo que no ha publicado geometría no permite deducir que
    hay un muro, e inventárselo dejaría ciegos a los vigilantes de cualquier
    prueba o entrega que monte un mundo desnudo. Un `ConoDeVision` sin
    geometría se comporta exactamente como antes de este cambio.

    Lo mismo con un recurso que no sea una rejilla: una entrega puede publicar
    cualquier cosa con ese nombre, y la decisión es la del cargador con un
    clima mal escrito — el estudiante necesita ver su nivel para darse cuenta,
    no un fallo de arranque.
    """
    geometria = mundo.recurso("geometria")
    consulta = getattr(geometria, "hay_vision", None)
    if not callable(consulta):
        return True
    return bool(consulta(desde, hasta))


def sistema_efectos(mundo: World, dt: float) -> None:
    """Descuenta las duraciones y aplica el dano continuo — AUD-388.

    Dos trabajos y en este orden: primero cobra el veneno del intervalo que
    acaba de pasar, y despues descuenta. Al reves, un efecto de 0,1 s con un
    fotograma de 0,2 s expiraria sin haber hecho nada, y el jugador veria un
    veneno que no envenena.

    La vida se recorta a cero por abajo. Un efecto continuo no deberia poder
    matar por debajo de cero -las pruebas de muerte comparan con `<= 0`- y
    dejar el numero negativo hace que la barra de vida dibuje un ancho
    negativo, que es el defecto que AUD-149 arreglo en otro sitio.

    Recorre solo las entidades con `Efectos`, que son las pocas que tienen algo
    encima: una escena normal tiene decenas de entidades y ninguna envenenada.
    """
    from src.framework.combate import efectos as reglas

    for entidad, comp in mundo.cada(Efectos):
        if not comp.activos:
            continue

        por_segundo = reglas.dano_por_segundo(comp)
        if por_segundo > 0.0:
            salud = mundo.obtener(entidad, Salud)
            if salud is not None:
                salud.actual = max(0.0, salud.actual - por_segundo * dt)

        for activo in comp.activos:
            activo.restante -= dt
        comp.activos[:] = [a for a in comp.activos if a.restante > 0.0]


def sistema_conos_de_vision(mundo: World, dt: float) -> None:
    """¿Ve alguien al jugador?

    La detección es la misma álgebra que César Ubáu escribió para su cámara de
    seguridad en `stage2_2/camara_seguridad.py`, generalizada al framework:

        v = P - C                    vector cámara -> jugador
        |v| <= alcance               ¿está lo bastante cerca?
        cos θ = (v̂ · m̂)             ¿está dentro del cono?
        θ <= semiángulo

    Se compara el coseno y **no se calcula el ángulo**: `acos` es caro, y el
    coseno es monótono decreciente en [0°, 180°], así que comparar cosenos
    ordena igual que comparar ángulos. Es la optimización clásica del cono de
    visión y merece explicarse en clase porque el atajo no es evidente.
    """
    jugador = rect_del_jugador(mundo)
    if jugador is None:
        return
    import math

    centro_jugador = pygame.Vector2(jugador.center)
    for entidad, cono in mundo.cada(ConoDeVision):
        t = mundo.obtener(entidad, Transform)
        if t is None:
            continue

        if cono.barrido > 0.0:
            cono._fase += cono.velocidad_barrido * dt
            oscilacion = math.sin(math.radians(cono._fase)) * cono.barrido
        else:
            oscilacion = 0.0

        base = math.atan2(cono.mira.y, cono.mira.x)
        mira = pygame.Vector2(
            math.cos(base + math.radians(oscilacion)),
            math.sin(base + math.radians(oscilacion)),
        )

        ojo = pygame.Vector2(t.rect.center)
        v = centro_jugador - ojo
        distancia = v.length()
        if distancia > cono.alcance or distancia == 0.0:
            cono.ve_al_jugador = False
            continue
        dentro = (v / distancia).dot(mira) >= math.cos(
            math.radians(cono.semiangulo),
        )
        # AUD-381 — y que no haya una pared en medio. Sin esto la detección era
        # distancia y ángulo, así que un vigilante al otro lado de un muro veía
        # igual que si el muro no existiera: el mismo defecto que AUD-278
        # arregló para la luz, abierto todavía para la vista. Y cambia una
        # regla, no un píxel — el sigilo con muros no funcionaba.
        #
        # La pieza estaba escrita para esto: `RejillaEspacial` (AUD-276) se
        # justificaba diciendo «sin esto no se puede hacer la línea de visión
        # de un guardia», se probó, y el guardia se escribió después sin
        # llamarla.
        cono.ve_al_jugador = dentro and _hay_linea_libre(mundo, ojo, centro_jugador)


def sistema_alerta(mundo: World, dt: float) -> None:
    """Sube mientras te ven, baja despacio cuando te pierden, y busca después.

    La bajada es más lenta que la subida —0,35 contra 2,0 por segundo— y no es
    un capricho: si olvidaran al mismo ritmo, esconderse un instante bastaría y
    el sigilo se resolvería a base de intentarlo. La asimetría es lo que obliga
    a planear la ruta antes de moverse.

    AUD-286 — la búsqueda. Al perder de vista a alguien que **ya estaba en
    alerta**, el guardia se queda con `ultimo_visto` y arranca su cuenta atrás
    de búsqueda. Sin esto, romper la línea de visión un segundo devolvía el
    mundo al estado inicial y esconderse no costaba nada.
    """
    jugador = rect_del_jugador(mundo)
    for entidad, alerta in mundo.cada(Alerta):
        cono = mundo.obtener(entidad, ConoDeVision)
        viendo = cono is not None and cono.ve_al_jugador
        estaba_en_alerta = alerta.nivel >= alerta.umbral_alerta

        if viendo:
            if jugador is not None:
                alerta.ultimo_visto = pygame.Vector2(jugador.center)
            # Volver a verlo cancela la búsqueda: ya no hay nada que buscar.
            alerta.busqueda_restante = 0.0
        elif alerta._veia and estaba_en_alerta:
            # El flanco: el fotograma exacto en que lo pierde de vista. Se arma
            # aquí y una sola vez. Si la condición fuera sólo «no lo ve y estaba
            # en alerta», se rearmaría durante el segundo y medio que tarda el
            # nivel en bajar del umbral, y la búsqueda duraría 4,4 s.
            alerta.busqueda_restante = alerta.segundos_de_busqueda
        elif alerta.busqueda_restante > 0.0:
            alerta.busqueda_restante = max(0.0, alerta.busqueda_restante - dt)
        alerta._veia = viendo

        alerta.nivel += (alerta.subida_por_segundo if viendo else -alerta.bajada_por_segundo) * dt
        alerta.nivel = max(0.0, min(alerta.umbral_alerta * 1.5, alerta.nivel))


def sistema_acosador(mundo: World, dt: float) -> None:
    """Persigue sin descanso, no se puede matar, y desaparece si lo pierdes.

    Lo tercero es lo que lo hace soportable. Un perseguidor que nunca se va
    convierte el nivel en una carrera sin pausa; uno que se retira y vuelve
    produce la tensión de Nemesis, que es la de no saber cuándo. Y es más barato
    que simularlo fuera de pantalla.
    """
    jugador = rect_del_jugador(mundo)
    if jugador is None:
        return
    objetivo = pygame.Vector2(jugador.center)
    for entidad, acos in mundo.cada(Acosador):
        t = mundo.obtener(entidad, Transform)
        if t is None:
            continue

        # Invulnerable siempre. No es una fase: es lo que es.
        s = mundo.obtener(entidad, Salud)
        if s is not None:
            s.invulnerable = True

        if acos._fuera > 0.0:
            acos._fuera -= dt
            if acos._fuera <= 0.0:
                # Vuelve por el lado por el que el jugador mira menos: detrás.
                t.posicion.update(objetivo.x - acos.distancia_retirada * 0.5, objetivo.y)
                t.rect.topleft = (int(t.posicion.x), int(t.posicion.y))
            continue

        hacia = objetivo - pygame.Vector2(t.rect.center)
        distancia = hacia.length()
        if distancia > acos.distancia_retirada:
            acos._fuera = acos.reaparicion
            continue
        if distancia > 1.0:
            # AUD-389 — rodear en vez de empotrarse. `_paso_del_acosador`
            # devuelve la direccion: la del siguiente tramo de la ruta si hay
            # malla publicada, y la recta de siempre si no la hay.
            direccion = _paso_del_acosador(mundo, entidad, t, objetivo, dt)
            t.posicion += direccion * acos.velocidad * dt
            t.rect.topleft = (int(t.posicion.x), int(t.posicion.y))
            t.facing = 1 if direccion.x >= 0 else -1


def _paso_del_acosador(mundo: World, entidad, t, objetivo: pygame.Vector2,
                       dt: float) -> pygame.Vector2:
    """Hacia donde da el siguiente paso el perseguidor — AUD-389.

    **Sin malla publicada devuelve la recta de siempre**, y eso no es una
    concesion: un mundo que no ha publicado geometria no permite deducir donde
    estan los muros, y quedarse quieto seria peor que ir recto. Es la misma
    decision que la oclusion de AUD-381.

    Con malla, re-planifica como mucho cuatro veces por segundo y escalonado
    (ver `Navegante`), y entre re-planificaciones consume la ruta que ya tiene.
    Recalcular cada fotograma costaria un A* por enemigo y por fotograma, que
    es justo lo que la cadencia evita.
    """
    from src.framework.ai import navegacion

    recta = objetivo - pygame.Vector2(t.rect.center)
    if recta.length_squared() == 0.0:
        return pygame.Vector2(0, 0)
    recta = recta.normalize()

    malla = mundo.recurso("malla_navegacion")
    if not isinstance(malla, navegacion.MallaDeNavegacion):
        return recta

    nav = mundo.obtener(entidad, Navegante)
    if nav is None:
        nav = Navegante()
        mundo.poner(entidad, nav)

    nav.proximo -= dt
    if nav.proximo <= 0.0:
        nav.proximo = navegacion.CADENCIA
        nav.ruta = navegacion.a_estrella(
            malla, malla.celda_de(pygame.Vector2(t.rect.center)),
            malla.celda_de(objetivo),
        )

    # Se descartan los tramos ya alcanzados: sin esto el perseguidor se queda
    # empujando contra el centro de la celda en la que ya esta.
    centro = pygame.Vector2(t.rect.center)
    while nav.ruta and centro.distance_to(malla.centro_de(nav.ruta[0])) < malla.tile * 0.5:
        nav.ruta.pop(0)
    if not nav.ruta:
        return recta

    hacia_tramo = malla.centro_de(nav.ruta[0]) - centro
    if hacia_tramo.length_squared() == 0.0:
        return recta
    return hacia_tramo.normalize()


# ══════════════════════════════════════════════════════════════
# Utilidad para la escena
# ══════════════════════════════════════════════════════════════


def rects_solidos(mundo: World) -> list[pygame.Rect]:
    """Los rectángulos que bloquean el paso **este fotograma**.

    Se recalcula cada fotograma en vez de mantener una lista mutable. Es un poco
    más de trabajo y elimina de un plumazo la clase entera de fallos de
    sincronización: un bloque rítmico que desaparece no tiene que acordarse de
    darse de baja en ninguna lista, porque no hay lista que actualizar.
    """
    salida: list[pygame.Rect] = []
    for entidad, _ in mundo.cada(Solido):
        t = mundo.obtener(entidad, Transform)
        if t is not None:
            salida.append(t.rect)
    return salida
