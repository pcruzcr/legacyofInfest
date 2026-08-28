"""
Fase ZONAS e IA — reaccionan a la posición ya resuelta y sigilo.

Extraído de `systems.py` monolítico por Fase, no por mecánica.
Zonas letales, lianas alcanzables, agua, efectos, conos de visión,
alerta, acosador y utilidades de rects sólidos comparten la ventana
ZONAS (600) e IA (200) porque todas leen la posición final del fotograma.
"""
from __future__ import annotations

import pygame

from src.framework.ecs.components import (
    Acosador,
    Alerta,
    ConoDeVision,
    Efectos,
    EsJugador,
    Liana,
    LianaSalto,
    Navegante,
    Salud,
    Solido,
    Tirolesa,
    Transform,
    ZonaDeAgua,
    ZonaLetalTemporizada,
)
from src.framework.ecs.world import World

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


def liana_salto_alcanzable(mundo: World, rect: pygame.Rect) -> LianaSalto | None:
    """La liana de salto más cercana en aire — radio generoso para salto entre lianas.

    Distinta a liana_alcanzable: aquí el agarre es en aire y con radio circular,
    no rect inflado. Permite engancharse saltando hacia la siguiente liana.
    """
    centro = pygame.Vector2(rect.center)
    mejor: LianaSalto | None = None
    mejor_dist = float("inf")
    for _, ls in mundo.cada(LianaSalto):
        # Punto de anclaje es top-center, el jugador debe llegar al rect de la cuerda
        # Usa distancia al rect inflado por radio_agarre
        zona = ls.rect.inflate(ls.radio_agarre * 2, ls.radio_agarre)
        # También permite agarre circular alrededor del anclaje
        anclaje = pygame.Vector2(ls.rect.centerx, ls.rect.top + 8)
        dist = (centro - anclaje).length()
        if zona.colliderect(rect) or dist < ls.radio_agarre * 1.5:
            if dist < mejor_dist:
                mejor_dist = dist
                mejor = ls
    return mejor


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
    """Los rectángulos que bloquean el paso **por todos lados**, este fotograma.

    Se recalcula cada fotograma en vez de mantener una lista mutable. Es un poco
    más de trabajo y elimina de un plumazo la clase entera de fallos de
    sincronización: un bloque rítmico que desaparece no tiene que acordarse de
    darse de baja en ninguna lista, porque no hay lista que actualizar.

    AUD-508 — antes recorría `mundo.cada(Solido)` con `for entidad, _ in ...`,
    tirando el propio componente y con él `atravesable_desde_abajo`. Una
    `MovingPlatform` con `atravesable="true"` en Tiled y **toda**
    `SinkingPlatform` al reaparecer (`sistema_plataformas_hundibles` pone
    `Solido(atravesable_desde_abajo=True)`) declaraban la intención y salían
    aquí como pared: `stage_scene.py` suma este resultado a `solidos`, no a
    `one_way_rects`, así que el jugador nunca podía saltar a través de ellas
    desde abajo aunque el dato dijera que sí. Ver `rects_atravesables_desde_abajo`.
    """
    salida: list[pygame.Rect] = []
    for entidad, solido in mundo.cada(Solido):
        if solido.atravesable_desde_abajo:
            continue
        t = mundo.obtener(entidad, Transform)
        if t is not None:
            salida.append(t.rect)
    return salida


def rects_atravesables_desde_abajo(mundo: World) -> list[pygame.Rect]:
    """Los `Solido` dinámicos que sí se cruzan saltando desde abajo (AUD-508).

    Contraparte de `rects_solidos`: el mismo recorrido, filtrado al revés.
    Quien llama a las dos debe sumar ésta a `one_way_rects`, no a `solidos`.
    """
    salida: list[pygame.Rect] = []
    for entidad, solido in mundo.cada(Solido):
        if not solido.atravesable_desde_abajo:
            continue
        t = mundo.obtener(entidad, Transform)
        if t is not None:
            salida.append(t.rect)
    return salida
