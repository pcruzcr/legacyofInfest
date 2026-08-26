with open(r'C:\Users\pcruz\github\legacyofInfest\src\framework\ecs\components.py', 'r', encoding='utf-8') as f:
    content = f.read()

old = '''_fuera: float = 0.0


# ═════════════════════════════════════════════════════════════════
# AUD-634 — Componentes de comportamiento reutilizables (Behavior Components)'''

new = '''_fuera: float = 0.0


@dataclass(slots=True)
class Acosador:
    """Persigue y **no se puede matar**. Nemesis, SA-X, E.M.M.I., el conserje.

    `Salud.invulnerable` ya existiría para esto, pero un acosador necesita algo
    más: reaparecer. Retirarlo cuando el jugador lo pierde y devolverlo después
    es lo que produce la sensación de que sigue ahí fuera, y es más barato que
    simularlo fuera de pantalla.
    """

    velocidad: float = 55.0
    #: Distancia a la que se retira si lo pierde de vista.
    distancia_retirada: float = 480.0
    #: Segundos hasta volver a aparecer.
    reaparicion: float = 6.0
    _fuera: float = 0.0


# ═════════════════════════════════════════════════════════════════
# AUD-634 — Componentes de comportamiento reutilizables (Behavior Components)

@dataclass(slots=True)
class RideableComponent:
    """Componente para montar un buddy — AUD-637.
    
    Se adjunta a la entidad del buddy. El sistema de montura lo lee
    para saber que esta entidad es montable y qué parámetros tiene.
    """
    
    buddy_id: str
    # Tipo de montura: "ground" (caminar), "flying" (volar), "water" (nadar)
    mount_type: str = "ground"
    # Velocidad de movimiento cuando está montado
    mount_speed: float = 120.0
    # Velocidad de salto si es ground
    jump_speed: float = -380.0
    # Si puede volar (para flying)
    can_fly: bool = False
    # Offset visual del jugador sobre el buddy
    rider_offset: pygame.Vector2 = field(default_factory=lambda: pygame.Vector2(0, -20))
    # Offset del hitbox del rider cuando está montado
    rider_hitbox_offset: pygame.Vector2 = field(default_factory=lambda: pygame.Vector2(0, -10))


# ════════════════════════════════════════════════════════════════════
# AUD-634 — Componentes de comportamiento reutilizables (Behavior Components)'''

content = content.replace(
    '_fuera: float = 0.0\n\n# ═════════════════════════════════════════════════════════════════\n# AUD-634 — Componentes de comportamiento reutilizables (Behavior Components)',
    '''_fuera: float = 0.0


@dataclass(slots=True)
class Acosador:
    """Persigue y **no se puede matar**. Nemesis, SA-X, E.M.M.I., el conserje.

    `Salud.invulnerable` ya existiría para esto, pero un acosador necesita algo
    más: reaparecer. Retirarlo cuando el jugador lo pierde y devolverlo después
    es lo que produce la sensación de que sigue ahí fuera, y es más barato que
    simularlo fuera de pantalla.
    """

    velocidad: float = 55.0
    #: Distancia a la que se retira si lo pierde de vista.
    distancia_retirada: float = 480.0
    #: Segundos hasta volver a aparecer.
    reaparicion: float = 6.0
    _fuera: float = 0.0


# ════════════════════════════════════════════════════════════════════
# AUD-634 — Componentes de comportamiento reutilizables (Behavior Components)

@dataclass(slots=True)
class RideableComponent:
    """Componente para montar un buddy — AUD-637.
    
    Se adjunta a la entidad del buddy. El sistema de montura lo lee
    para saber que esta entidad es montable y qué parámetros tiene.
    """
    
    buddy_id: str
    # Tipo de montura: "ground" (caminar), "flying" (volar), "water" (nadar)
    mount_type: str = "ground"
    # Velocidad de movimiento cuando está montado
    mount_speed: float = 120.0
    # Velocidad de salto si es ground
    jump_speed: float = -380.0
    # Si puede volar (para flying)
    can_fly: bool = False
    # Offset visual del jugador sobre el buddy
    rider_offset: pygame.Vector2 = field(default_factory=lambda: pygame.Vector2(0, -20))
    # Offset del hitbox del rider cuando está montado
    rider_hitbox_offset: pygame.Vector2 = field(default_factory=lambda: pygame.Vector2(0, -10))


# ════════════════════════════════════════════════════════════════════════
# AUD-634 — Componentes de comportamiento reutilizables (Behavior Components)''')

content = content.replace(
    '_fuera: float = 0.0\n\n# ═════════════════════════════════════════════════════════════════\n# AUD-634 — Componentes de comportamiento reutilizables (Behavior Components)',
    new
)

with open(r'C:\Users\pcruz\github\legacyofInfest\src\framework\ecs\components.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Done')