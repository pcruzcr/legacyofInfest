"""
Module: test_gameplay_integration
System: tests
Academic Unit: N/A

El juego jugándose: escena real, entidades reales, fotogramas reales.

Por qué existe (AUD-060)
------------------------
Estas pruebas nacen de un fallo que ninguna de las 1060 anteriores detectó, y
que yo mismo introduje: **ningún enemigo del juego se actualizaba**.

Al reescribir `CollisionSystem` durante la auditoría convertí
`update_enemies()` en un no-op, con un docstring que afirmaba «el movimiento lo
integra `EnemyBase.update`, aquí no hay nada que sincronizar». La primera mitad
era cierta. La segunda era falsa, porque **nadie más llamaba a
`EnemyBase.update`**. Razoné sobre lo que el método debía hacer en lugar de
comprobar quién dependía de él.

El resultado: enemigos y jefe inmóviles e invulnerables —sus fotogramas de
invencibilidad tampoco corrían, así que sólo aceptaban un golpe cada nunca—,
mientras la máquina de 13 estados, la escuadra, el predictor de scikit-learn y
el kit de encuentro de jefe se probaban todos aislados y pasaban.

Ese es exactamente el hueco: cada pieza demostrada por separado y **nadie
comprobando que estuvieran conectadas**. Las pruebas de humo de escena existían
pero sólo exigían «no lanza excepciones», y una estatua tampoco lanza
excepciones.

Estas pruebas afirman lo contrario: que las cosas *se mueven*, *golpean* y
*terminan*. Son lentas comparadas con una prueba unitaria y valen cada
milisegundo, porque miden lo único que el jugador percibe.
"""
from __future__ import annotations

import pygame
import pytest

from src.engine.core.events import Events
from src.framework.entities.boss_base import BossBase
from src.framework.entities.enemy_base import EnemyBase

DT = 1.0 / 60.0


@pytest.fixture
def app(_pygame_init):
    """Una App real: el mismo cableado que usa `main.py`."""
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((800, 600))
    from src.engine.core.app import App

    return App()


@pytest.fixture
def surface():
    return pygame.Surface((800, 600))


def _run(app, scene, surface, frames: int) -> None:
    for _ in range(frames):
        app.scene_manager.update(DT)
        app.scene_manager.current.draw(surface)
        app.event_bus.dispatch()


def _skip_intro(app, scene, surface, limit: int = 300) -> int:
    """Avanza hasta que la cinemática de apertura devuelve el control.

    `Stage0.update` actualiza la cinemática y **retorna**, saltándose el resto
    del fotograma: es lo correcto —durante una cinemática el juego no debe
    seguir jugándose— pero significa que medir el primer segundo de la escena
    mide la cinemática, no el juego. Sin esto, una prueba de «los enemigos se
    mueven» falla por una razón que no tiene nada que ver con los enemigos.
    """
    for frame in range(limit):
        cutscene = getattr(scene, "_cutscene", None)
        if cutscene is None or not cutscene.active:
            return frame
        app.scene_manager.update(DT)
        app.scene_manager.current.draw(surface)
    raise AssertionError(
        f"la cinemática de apertura sigue activa tras {limit} fotogramas",
    )


class TestEnemiesActuallyLive:
    """Lo mínimo que un enemigo tiene que hacer: existir en movimiento."""

    def test_every_enemy_in_stage0_moves(self, app, surface) -> None:
        """Los nueve enemigos de stage0 estuvieron inmóviles y nadie lo vio.

        No se comprueba «alguno se mueve»: con uno bastaría para pasar mientras
        ocho siguen siendo estatuas. Se exige que **todos** cambien de posición
        en tres segundos, que es lo que hacen enemigos vivos.
        """
        from src.stages.stage0.stage0 import Stage0

        scene = Stage0(app.context)
        app.scene_manager.push(scene)
        _skip_intro(app, scene, surface)
        enemies = [e for e in scene._stage_data.entity_list
                   if isinstance(e, EnemyBase)]
        assert enemies, "stage0 debería tener enemigos"

        # AUD-116: antes se comparaba la posición final con la inicial. Un
        # enemigo que patrulla 80 px a 60 px/s tarda 2,67 s en el viaje de ida
        # y vuelta, así que a los 3 s puede estar **exactamente** donde
        # empezó. La prueba fallaba o pasaba según el período de la patrulla,
        # no según si el enemigo estaba vivo, y al regenerar stage 0 acusó de
        # estatuas a dos Walkers que se movían perfectamente.
        #
        # Ahora se muestrea durante toda la ventana: se mueve quien ocupó
        # alguna posición distinta en algún momento.
        inicial = {id(e): e.rect.topleft for e in enemies}
        visto_moverse: set[int] = set()
        for _ in range(180):
            _run(app, scene, surface, 1)
            for e in enemies:
                if e.rect.topleft != inicial[id(e)]:
                    visto_moverse.add(id(e))

        still = [type(e).__name__ for e in enemies if id(e) not in visto_moverse]
        assert not still, f"enemigos que no se movieron en 3 s: {still}"

    def test_enemies_receive_the_player_reference_every_frame(
        self, app, surface,
    ) -> None:
        """Sin referencia al jugador no hay detección, y sin detección no hay IA.

        Se comprueba después de correr fotogramas, no en el arranque: la
        referencia se fijaba una vez al cargar y bastaba con que la escena
        respawneara al jugador para dejar a todos los enemigos apuntando a un
        rect que ya no se actualiza.
        """
        from src.stages.stage0.stage0 import Stage0

        scene = Stage0(app.context)
        app.scene_manager.push(scene)
        _skip_intro(app, scene, surface)
        _run(app, scene, surface, 30)

        for enemy in scene._stage_data.entity_list:
            if isinstance(enemy, EnemyBase):
                assert enemy._player_ref is scene._player.rect

    def test_invincibility_frames_tick_down_inside_a_scene(
        self, app, surface,
    ) -> None:
        """La consecuencia menos visible de no actualizar: un enemigo golpeado
        una vez quedaba invulnerable para siempre, porque su contador de
        invencibilidad sólo baja dentro de `update`."""
        from src.stages.stage0.stage0 import Stage0

        scene = Stage0(app.context)
        app.scene_manager.push(scene)
        _skip_intro(app, scene, surface)
        enemy = next(e for e in scene._stage_data.entity_list
                     if isinstance(e, EnemyBase))

        enemy.apply_hit(0.5, (enemy.rect.centerx + 30, enemy.rect.centery))
        assert enemy._invincibility_timer > 0
        _run(app, scene, surface, 60)
        assert enemy._invincibility_timer <= 0, (
            "los fotogramas de invencibilidad no bajan: el enemigo aceptaría "
            "un solo golpe en toda la partida"
        )

    def test_an_enemy_can_be_killed_over_several_hits(self, app, surface) -> None:
        """El bucle completo: golpear, esperar las i-frames, volver a golpear."""
        from src.stages.stage0.stage0 import Stage0

        scene = Stage0(app.context)
        app.scene_manager.push(scene)
        _skip_intro(app, scene, surface)
        enemy = next(e for e in scene._stage_data.entity_list
                     if isinstance(e, EnemyBase))

        for _ in range(60):
            enemy.apply_hit(0.5, (enemy.rect.centerx + 30, enemy.rect.centery))
            _run(app, scene, surface, 40)
            if not enemy.is_alive:
                break
        assert not enemy.is_alive, (
            f"el enemigo sobrevivió a 60 rondas de golpes; vida="
            f"{enemy.current_health}"
        )


class TestCombatHurtsBothWays:
    """El combate tiene dos direcciones, y sólo se había verificado una.

    AUD-062: al restaurar `enemy.update(dt)` recuperé el movimiento y volví a
    dar por bueno el combate entero. Faltaba la otra llamada que se perdió con
    `update_enemies`: `_check_player_contact`, que es donde cada enemigo
    resuelve el daño por contacto **y sus proyectiles**. Sin ella, ningún
    enemigo podía tocar al jugador: las flechas del Archer, las bolas del
    Caster, las lianas y esporas del Venado, su pisotón y su barrido no
    existían para el jugador.

    Que una prueba de «los enemigos se mueven» pase no dice nada sobre si
    pueden hacer daño. Son dos afirmaciones distintas y hacen falta las dos.
    """

    def _stage(self, app, surface):
        from src.stages.stage0.stage0 import Stage0

        scene = Stage0(app.context)
        app.scene_manager.push(scene)
        _skip_intro(app, scene, surface)
        return scene

    @staticmethod
    def _place_beside_player(enemy, player) -> None:
        """Coloca al enemigo encima del jugador, no al revés.

        Mover al jugador no funciona: su física lo reposiciona en el mismo
        fotograma —gravedad, resolución de colisiones— y la prueba acaba
        midiendo dos cuerpos que nunca llegaron a tocarse. Es el error que me
        hizo creer un rato que el contacto seguía roto después de arreglarlo.
        """
        enemy.position.x = float(player.rect.centerx)
        enemy.position.y = float(player.rect.y)
        enemy.rect.x = int(enemy.position.x)
        enemy.rect.y = int(enemy.position.y)

    def test_touching_an_enemy_hurts_the_player(self, app, surface) -> None:
        scene = self._stage(app, surface)
        player = scene._player
        enemy = next(e for e in scene._stage_data.entity_list
                     if isinstance(e, EnemyBase))

        before = player.current_health
        for _ in range(120):
            self._place_beside_player(enemy, player)
            app.scene_manager.update(DT)
            app.scene_manager.current.draw(surface)
            if player.current_health < before:
                break

        assert player.current_health < before, (
            "el jugador puede quedarse dentro de un enemigo sin recibir daño"
        )

    def test_contact_damage_respects_its_cooldown(self, app, surface) -> None:
        """Sin enfriamiento, tocar a un enemigo mataría en un puñado de frames.

        Se comprueba que el daño exista **y** que esté limitado: las dos mitades
        importan, y una prueba que sólo mire «recibió daño» aceptaría un
        enemigo que drena la vida entera en medio segundo.
        """
        scene = self._stage(app, surface)
        player = scene._player
        enemy = next(e for e in scene._stage_data.entity_list
                     if isinstance(e, EnemyBase))

        before = player.current_health
        for _ in range(120):  # 2 segundos pegados
            self._place_beside_player(enemy, player)
            app.scene_manager.update(DT)
            app.scene_manager.current.draw(surface)

        lost = before - player.current_health
        assert lost > 0, "el contacto no hizo daño"
        assert lost < before, (
            f"2 s de contacto quitaron {lost} de {before} de vida: el "
            f"enfriamiento de contacto no está limitando nada"
        )

    def test_the_player_attack_damages_an_enemy(self, app, surface) -> None:
        """El ataque del jugador por el camino real: pulsar el botón.

        No se llama a `enemy.apply_hit` a mano —eso probaría el método, no el
        juego—: se pulsa la acción de ataque con el mismo stub de entrada que
        usa el bot de playtest, el jugador entra en su estado de ataque, y
        `CollisionSystem.process_attack` resuelve el impacto. Es la cadena
        completa que ocurre cuando alguien juega.
        """
        from src.engine.input.action_map import Action
        from tests.playtest.bot import _StubInput

        scene = self._stage(app, surface)
        player = scene._player
        enemy = next(e for e in scene._stage_data.entity_list
                     if isinstance(e, EnemyBase))

        stub = _StubInput()
        app.context.input_manager = stub

        before = enemy.current_health
        for frame in range(240):
            # Se recoloca cada fotograma: el enemigo patrulla y se iría.
            enemy.position.x = float(player.rect.centerx + 6)
            enemy.position.y = float(player.rect.y)
            enemy.rect.x = int(enemy.position.x)
            enemy.rect.y = int(enemy.position.y)
            # Pulsar y soltar: el ataque se dispara en el flanco, así que
            # mantener el botón no encadena golpes.
            stub.set_actions({Action.SHORT_ATTACK} if frame % 20 < 2 else set())
            app.scene_manager.update(DT)
            app.scene_manager.current.draw(surface)
            if enemy.current_health < before:
                break

        assert enemy.current_health < before, (
            "atacar a un enemigo pegado al jugador no le quita vida: el "
            "ataque no llega por el camino real"
        )

    def test_the_boss_can_hurt_the_player(self, app, surface) -> None:
        """El Venado era completamente inofensivo (AUD-062).

        Sus proyectiles, su pisotón y su barrido se resuelven en
        `_check_player_contact`. Sin esa llamada podías quedarte quieto delante
        de él indefinidamente.
        """
        from src.stages.boss_venado.boss_venado_scene import BossVenadoScene

        scene = BossVenadoScene(app.context)
        app.scene_manager.push(scene)
        boss = next(e for e in scene._stage_data.entity_list
                    if isinstance(e, BossBase))
        player = scene._player

        before = player.current_health
        for _ in range(900):  # 15 s debajo del jefe
            # Se mueve al JUGADOR bajo el jefe, no al revés. Desde AUD-071 la
            # altura del Venado se recalcula cada fotograma respecto al suelo,
            # así que forzar su posición no sirve: el propio movimiento la
            # deshace en el mismo frame. Una versión anterior de esta prueba lo
            # hacía y medía dos cuerpos que nunca llegaban a tocarse.
            player.position.x = float(boss.rect.centerx)
            player.rect.x = int(player.position.x)
            app.scene_manager.update(DT)
            app.scene_manager.current.draw(surface)
            if player.current_health < before:
                break

        assert player.current_health < before, (
            "el jefe no puede hacer daño: el combate es un simulacro"
        )


class TestTheBossFightIsPlayable:
    """El único combate de jefe que existe hoy. Si no funciona, no hay juego."""

    @pytest.fixture
    def boss_scene(self, app):
        from src.stages.boss_venado.boss_venado_scene import BossVenadoScene

        scene = BossVenadoScene(app.context)
        app.scene_manager.push(scene)
        boss = next(e for e in scene._stage_data.entity_list
                    if isinstance(e, BossBase))
        return scene, boss

    def test_the_boss_moves(self, app, surface, boss_scene) -> None:
        scene, boss = boss_scene
        start = boss.rect.topleft
        _run(app, scene, surface, 180)
        assert boss.rect.topleft != start, "el jefe es una estatua"

    def test_the_boss_attacks(self, app, surface, boss_scene) -> None:
        """Un jefe que no ataca no es un combate, es un saco de golpes.

        AUD-107 — dos cosas cambiaron al sustituir el jefe de referencia por la
        entrega del estudiante, y ninguna era un fallo suyo:

        1. Esta prueba espiaba `on_attack_fired`, el gancho del planificador
           del framework. Su Venado no lo usa: declara los patrones en
           `BossPhase` y los despacha él. La prueba medía **cómo** ataca en vez
           de **si** ataca, y daba cero sobre un jefe que ataca de sobra.
        2. Su Venado sólo pelea en su terreno sagrado. El jugador aparece al
           principio del mapa y aquí nadie lo movía, así que el jefe esperaba
           quince segundos, correctamente.

        Ahora se entra en la arena y se observan efectos.
        """
        from src.stages.boss_venado.boss_venado import ARENA_CX

        scene, boss = boss_scene
        if getattr(scene, "_player", None) is not None:
            scene._player.rect.centerx = int(ARENA_CX)
            scene._player.position.x = float(scene._player.rect.x)

        vistos: set[str] = set()
        for _ in range(900):  # 15 segundos
            app.scene_manager.update(DT)
            app.scene_manager.current.draw(surface)
            if boss._telegraph:
                vistos.add(boss._telegraph)
            if boss._stomp_rect is not None:
                vistos.add("STOMP_ACTIVO")
            if boss._charge_active:
                vistos.add("CHARGE_ACTIVO")
            for p in boss._projectiles:
                vistos.add(f"PROYECTIL_{p['type']}")

        assert vistos, "el jefe no lanzó ni un ataque en 15 s"
        assert len(vistos) >= 2, f"sólo usó un ataque: {sorted(vistos)}"

    def test_the_boss_stays_inside_the_arena(self, app, surface, boss_scene) -> None:
        """Una embestida sin límite lo sacaba del mapa (AUD-061).

        Fuera del mapa el jugador no puede alcanzarlo, así que el combate deja
        de poder ganarse sin que nada avise: el jugador da vueltas por una
        arena vacía buscando a un jefe que está en x negativa.
        """
        scene, boss = boss_scene
        width, _height = scene._stage_data.map_pixel_size

        for i in range(1200):
            if i % 50 == 0:
                boss.apply_hit(0.25, (boss.rect.centerx + 40, boss.rect.centery))
            app.scene_manager.update(DT)
            app.scene_manager.current.draw(surface)
            if not boss.is_alive:
                break
            assert 0 <= boss.rect.x, f"el jefe salió por la izquierda: x={boss.rect.x}"
            assert boss.rect.right <= width, (
                f"el jefe salió por la derecha: right={boss.rect.right} > {width}"
            )

    def test_the_boss_fights_within_reach_of_the_player(
        self, app, surface, boss_scene,
    ) -> None:
        """El Venado peleaba pegado al techo (AUD-071).

        Medido antes del arreglo: el suelo de la arena está en y=304 y el jefe
        oscilaba entre y=52 y y=135 — el jugador no podía alcanzarlo saltando y
        el combate era inganable, que es lo que se reportó jugando.

        Su movimiento vertical se anclaba al punto de aparición del TMX y, en
        fase 2, a la mitad de la altura del mapa. Ahora se mide desde el suelo,
        así que funciona en cualquier arena que dibuje un estudiante.
        """
        scene, boss = boss_scene
        floor = max(r.top for r in scene._stage_data.collision_rects)

        heights = []
        for _ in range(600):
            app.scene_manager.update(DT)
            app.scene_manager.current.draw(surface)
            heights.append(floor - boss.rect.bottom)

        highest = max(heights)
        assert highest < 160, (
            f"el jefe llegó a {highest} px sobre el suelo: fuera del alcance "
            f"de un salto"
        )
        assert min(heights) > -20, "el jefe se hunde en el suelo"

    def test_the_boss_uses_the_whole_arena(self, app, surface, boss_scene) -> None:
        """Declaraba ARENA_W = 320 en un mapa de 640: peleaba en media arena.

        La mitad del escenario quedaba decorativa, y el jugador podía quedarse
        en la otra mitad sin que nada le obligara a moverse.

        AUD-107 — se medía contra el **mapa entero**, y eso dejó de tener
        sentido. La arena de referencia era un rectángulo de 640 px y el mapa
        no era otra cosa. La entrega que la sustituye es un nivel largo con un
        corredor de aproximación y la arena al final (2480 → 3264): pedirle al
        jefe que recorra el 40 % del mapa sería pedirle que salga de su arena.

        Lo que hay que comprobar es que no se quede en una esquina de **su
        arena**, que es lo que la prueba quería decir desde el principio.
        """
        from src.stages.boss_venado.boss_venado import ARENA_X0, ARENA_X1

        scene, boss = boss_scene
        ancho_arena = ARENA_X1 - ARENA_X0
        if getattr(scene, "_player", None) is not None:
            scene._player.rect.centerx = int((ARENA_X0 + ARENA_X1) / 2)
            scene._player.position.x = float(scene._player.rect.x)

        seen = []
        for _ in range(1200):
            app.scene_manager.update(DT)
            app.scene_manager.current.draw(surface)
            seen.append(boss.rect.centerx)
        used = max(seen) - min(seen)
        assert used > ancho_arena * 0.25, (
            f"el jefe sólo recorrió {used}px de una arena de {ancho_arena:.0f}px"
        )

    def test_defeating_the_boss_completes_the_stage(
        self, app, surface, boss_scene,
    ) -> None:
        """El final del juego tal y como está hoy: matar al Venado y salir.

        El manejador se guarda en una variable a propósito: el bus mantiene
        referencias débiles, así que una lambda temporal se recolecta antes de
        recibir nada. (El bus lo avisa por el log; conviene no ignorarlo.)
        """
        scene, boss = boss_scene
        completed: list[dict] = []

        def on_complete(**payload: object) -> None:
            completed.append(dict(payload))

        app.event_bus.subscribe(Events.STAGE_COMPLETE, on_complete)

        boss.current_health = 0.5
        boss._invincibility_timer = 0.0
        boss.apply_hit(0.5, (boss.rect.centerx + 40, boss.rect.centery))

        _run(app, scene, surface, 700)

        assert completed, "derrotar al jefe no completó el escenario"
        assert app.scene_manager.current is not scene, (
            "el juego se quedó en la arena tras ganar"
        )


class TestTheStageChain:
    """Que el juego se pueda terminar de principio a fin."""

    def test_stage0_leads_to_the_boss_and_the_boss_to_the_credits(
        self, app, surface,
    ) -> None:
        from src.engine.core.stage_registry import discover_stages

        stages = discover_stages()
        assert len(stages) >= 2, f"sólo se descubrieron {len(stages)} escenarios"

        app.scene_manager.set_stage_queue(stages)
        app.scene_manager.push(stages[0](app.context))
        assert type(app.scene_manager.current) is stages[0]

        app.event_bus.emit(Events.STAGE_COMPLETE, stage_id="stage0")
        app.event_bus.dispatch()
        assert type(app.scene_manager.current) is stages[1], (
            "completar stage0 no lleva al jefe"
        )

        _run(app, app.scene_manager.current, surface, 60)

        app.event_bus.emit(Events.STAGE_COMPLETE, stage_id="boss_venado")
        app.event_bus.dispatch()
        assert type(app.scene_manager.current) is not stages[1], (
            "completar el jefe no lleva a ninguna parte"
        )
        _run(app, app.scene_manager.current, surface, 60)


class TestNoOpsAnnounceThemselves:
    """Un método que no hace nada tiene que decirlo (AUD-063).

    `CollisionSystem.update_enemies` fue durante toda la auditoría un no-op
    silencioso con un docstring que afirmaba que no había nada que sincronizar.
    Su nombre prometía trabajo, su cuerpo no hacía ninguno, y quien leyera la
    llamada no tenía forma de notarlo. Costó dos bugs de gravedad máxima:
    enemigos inmóviles (AUD-060) e incapaces de dañar (AUD-062).

    Estas pruebas fijan la política: si se conserva por compatibilidad, avisa.
    """

    def _collision(self, _pygame_init):
        import pygame
        if pygame.display.get_surface() is None:
            pygame.display.set_mode((800, 600))
        from src.framework.stage.collision_system import CollisionSystem

        return CollisionSystem()

    def test_step_warns_instead_of_pretending(self, _pygame_init) -> None:
        collision = self._collision(_pygame_init)
        with pytest.warns(DeprecationWarning, match="no hace nada"):
            collision.step(DT)

    def test_update_enemies_warns_instead_of_pretending(self, _pygame_init) -> None:
        """Éste es el que hizo daño real. Que nadie vuelva a creerle."""
        collision = self._collision(_pygame_init)
        with pytest.warns(DeprecationWarning, match="ya no actualiza"):
            collision.update_enemies(DT, None, None)

    def test_the_scene_does_not_call_the_deprecated_helpers(self) -> None:
        """La escena tiene que hacer el trabajo, no delegarlo en un no-op."""
        import pathlib

        source = pathlib.Path("src/framework/scenes/stage_scene.py").read_text(
            encoding="utf-8",
        )
        code = "\n".join(
            line for line in source.splitlines()
            if not line.strip().startswith("#")
        )
        assert "_collision.update_enemies(" not in code
        assert "_collision.step(" not in code


class TestThePlayerIsVisible:
    """El protagonista tiene que verse (AUD-067).

    Lo reportó el usuario jugando: «el personaje no se ve, se ve el movimiento
    y un dash pero no se ve más». Tenía razón — `Player.draw` no se llamaba
    **nunca**.

    Al reescribir `DrawingSystem` durante la auditoría, el bucle de dibujo pasó
    a recorrer `stage.entity_list`, que contiene sólo enemigos. El jugador
    quedó fuera. `ctx.player` siguió usándose únicamente en el overlay de
    depuración, que pinta un rectángulo cian: por eso con F1 «se veía» algo y
    sin F1 no había nadie.

    Ninguna de las 1097 pruebas lo detectó. Las de humo comprobaban que la
    escena dibujara «algo» distinto del fondo, y el escenario, los enemigos y
    el HUD ya lo garantizaban. Un juego sin protagonista visible también pinta
    píxeles.
    """

    def _stage(self, app, surface):
        from src.stages.stage0.stage0 import Stage0

        scene = Stage0(app.context)
        app.scene_manager.push(scene)
        _skip_intro(app, scene, surface)
        return scene

    def test_the_player_is_actually_drawn(self, app, surface) -> None:
        """Se compara el fotograma con y sin el jugador.

        Contar «píxeles distintos del fondo» no sirve: el escenario y el HUD ya
        los ponen. Lo único que demuestra que el personaje está en pantalla es
        que quitarlo cambie la imagen.
        """
        scene = self._stage(app, surface)
        player = scene._player

        with_player = pygame.Surface((800, 600))
        scene.draw(with_player)

        original_draw = type(player).draw
        type(player).draw = lambda self, *a, **k: None
        try:
            without_player = pygame.Surface((800, 600))
            scene.draw(without_player)
        finally:
            type(player).draw = original_draw

        changed = sum(
            1
            for x in range(0, 800, 2)
            for y in range(0, 600, 2)
            if with_player.get_at((x, y)) != without_player.get_at((x, y))
        )
        assert changed > 20, (
            f"quitar al jugador sólo cambia {changed} píxeles: el protagonista "
            f"no se está dibujando"
        )

    def test_the_player_is_visible_without_the_debug_overlay(
        self, app, surface,
    ) -> None:
        """El rectángulo cian de depuración no cuenta como ver al personaje.

        Es lo que confundió el diagnóstico: con F1 aparecía una silueta y
        parecía que el jugador estaba ahí.
        """
        scene = self._stage(app, surface)
        assert not getattr(scene, "_debug", False), (
            "la escena arranca con depuración activada; la prueba no mediría "
            "el juego real"
        )
        calls: list[int] = []
        original = type(scene._player).draw

        def counting(self, *args, **kwargs):
            calls.append(1)
            return original(self, *args, **kwargs)

        type(scene._player).draw = counting
        try:
            scene.draw(surface)
        finally:
            type(scene._player).draw = original

        assert calls, "Player.draw no se llamó en un fotograma normal"

    def test_entities_are_drawn_back_to_front(self, app, surface) -> None:
        """El orden por profundidad también se perdió en aquella reescritura.

        Sin él, quien se dibuja encima lo decide el orden en que el TMX listó
        los objetos: un enemigo del fondo podía taparle la cara al jugador.
        """
        scene = self._stage(app, surface)
        drawn: list[int] = []

        from src.framework.entities.enemy_base import EnemyBase

        targets = [scene._player] + [
            e for e in scene._stage_data.entity_list if isinstance(e, EnemyBase)
        ]
        originals = {}
        for entity in targets:
            cls = type(entity)
            if cls in originals:
                continue
            originals[cls] = cls.draw

            def make(original):
                def recording(self, *args, **kwargs):
                    drawn.append(self.rect.centery)
                    return original(self, *args, **kwargs)
                return recording

            cls.draw = make(originals[cls])
        try:
            scene.draw(surface)
        finally:
            for cls, original in originals.items():
                cls.draw = original

        assert drawn == sorted(drawn), (
            f"las entidades no se dibujan de atrás hacia delante: {drawn}"
        )


class TestStage0SurvivesTheWholeMap:
    """Recorrer el escenario entero, no sólo los primeros metros (AUD-066).

    El usuario lo encontró jugando:

        AttributeError: 'Stage0' object has no attribute '_context'
        en _check_zone_progression, línea 172

    `self._context` no existe —`BaseScene` expone `self.context`— y esa línea
    sólo se ejecuta al pasar del tile 85 de 100. El juego crasheaba a tres
    cuartos del escenario, y ninguna prueba llegaba tan lejos: todas medían el
    arranque.

    Un escenario se prueba de principio a fin o no se prueba.
    """

    def test_crossing_every_zone_trigger_does_not_crash(self, app, surface) -> None:
        """Teletransporta al jugador por cada umbral de zona y sigue jugando.

        Se mueve al jugador en vez de simular el recorrido completo: caminar
        cien tiles tarda medio minuto de tiempo real y la prueba se saltaría en
        cuanto molestara. Lo que importa es ejecutar el código de cada umbral.
        """
        from src.stages.stage0.stage0 import Stage0

        scene = Stage0(app.context)
        app.scene_manager.push(scene)
        _skip_intro(app, scene, surface)
        player = scene._player
        tile = scene.TILE

        # Los tres umbrales que `_check_zone_progression` comprueba, más allá
        # del último para asegurar que no queda ninguno sin ejecutar.
        for tile_x in (17, 53, 86, 95):
            player.position.x = float(tile_x * tile)
            player.rect.x = int(player.position.x)
            for _ in range(30):
                app.scene_manager.update(DT)
                app.scene_manager.current.draw(surface)
                app.event_bus.dispatch()

        assert scene._zone_entered == {1, 2, 3}, (
            f"no se activaron todas las zonas: {scene._zone_entered}"
        )

    def test_the_storm_zone_actually_changes_the_weather(
        self, app, surface,
    ) -> None:
        """La línea que crasheaba era la que anuncia la tormenta.

        Comprobar que no lanza no basta: si alguien «arregla» el crash
        borrando la línea, la tormenta desaparece y la prueba seguiría en
        verde.
        """
        from src.stages.stage0.stage0 import Stage0

        scene = Stage0(app.context)
        app.scene_manager.push(scene)
        _skip_intro(app, scene, surface)

        before = getattr(scene._weather, "_climate", None)
        scene._player.position.x = float(86 * scene.TILE)
        scene._player.rect.x = int(scene._player.position.x)
        _run(app, scene, surface, 30)

        after = getattr(scene._weather, "_climate", None)
        assert after == "storm", f"el clima no cambió a tormenta: {before} -> {after}"


class TestThePlayerMovesAtAHumanSpeed:
    """La velocidad del jugador tiene que ser jugable (AUD-070).

    Reportado jugando: «el player cuando avanzamos sale volando o sale rápido,
    no hace lo que tiene que hacer».

    Medido: `walk_speed` devolvía **1890 px/s** — 31 píxeles por fotograma a 60
    fps, con lo que el personaje cruzaba un mapa de 1600 px en menos de un
    segundo.

    La causa es una unidad mal leída al conectar dos piezas. El inventario
    guarda el bono de velocidad en **porcentaje** —`swift_feather` declara
    `speed_bonus=10.0` y se describe a sí mismo como «Move 10% faster»— y el
    jugador lo aplicaba como fracción: `90 * (1 + 10)`.

    Es el defecto recurrente de esta auditoría visto desde el otro lado. Al
    cablear `get_total_speed_bonus()`, que hasta entonces no tenía ningún
    consumidor, nadie miró en qué unidad estaba lo que devolvía. Conectar dos
    piezas obliga a mirar las dos.
    """

    def test_walk_speed_stays_within_a_playable_range(self, app, surface) -> None:
        """Un límite superior generoso, pero que 1890 no cruza ni de lejos.

        No se fija un valor exacto: la velocidad es una decisión de diseño y
        puede ajustarse. Lo que no puede es salirse en un orden de magnitud.
        """
        from src.stages.stage0.stage0 import Stage0

        scene = Stage0(app.context)
        app.scene_manager.push(scene)
        _skip_intro(app, scene, surface)

        speed = scene._player.walk_speed
        per_frame = speed / 60.0
        assert 40.0 <= speed <= 400.0, (
            f"walk_speed = {speed} px/s ({per_frame:.1f} px por fotograma). "
            f"Fuera de ese rango el personaje es incontrolable o no avanza."
        )
        assert per_frame < 8.0, (
            f"a {per_frame:.1f} px por fotograma el jugador atraviesa paredes "
            f"de 16 px sin llegar a tocarlas"
        )

    def test_relic_speed_bonuses_are_percentages(self, _pygame_init) -> None:
        """El bono declarado como «10% más rápido» debe dar un 10%.

        Se comprueba la conversión directamente y no a través del juego: es una
        cuestión de unidades, y una prueba de integración diría «va rápido» sin
        distinguir un 10% de un 1000%.
        """
        import pygame

        from src.framework.entities.player import Player

        base = Player(pygame.Vector2(0, 0)).walk_speed

        class _OneSwiftFeather:
            def get_total_hp_bonus(self) -> float:
                return 0.0

            def get_total_speed_bonus(self) -> float:
                return 10.0  # como lo declara `swift_feather`

            def get_total_damage_bonus(self) -> float:
                return 0.0

        player = Player(pygame.Vector2(0, 0))
        player.apply_relic_bonuses(_OneSwiftFeather())

        assert player.walk_speed == pytest.approx(base * 1.10), (
            f"una reliquia de «+10%» dejó la velocidad en {player.walk_speed} "
            f"partiendo de {base}"
        )

    def test_the_player_can_traverse_the_opening_of_stage0(
        self, app, surface,
    ) -> None:
        """Avanzar de verdad, saltando los escalones, como haría una persona.

        El primer obstáculo de stage0 es un escalón de 16 px a los doce píxeles
        de la salida: caminar sin saltar se detiene ahí, y eso es diseño de
        nivel, no un fallo. Esta prueba salta, que es lo que el nivel pide.
        """
        from src.engine.input.action_map import Action
        from src.stages.stage0.stage0 import Stage0
        from tests.playtest.bot import _StubInput

        scene = Stage0(app.context)
        app.scene_manager.push(scene)
        _skip_intro(app, scene, surface)

        stub = _StubInput()
        app.context.input_manager = stub
        player = scene._player
        start = player.position.x

        for frame in range(300):
            actions = {Action.MOVE_RIGHT}
            if frame % 45 < 3:
                actions.add(Action.JUMP)
            stub.set_actions(actions)
            app.scene_manager.update(DT)
            app.scene_manager.current.draw(surface)

        travelled = player.position.x - start
        assert travelled > 150, (
            f"en cinco segundos avanzando y saltando sólo recorrió {travelled:.0f} px"
        )
