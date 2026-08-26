with open(r'C:\Users\pcruz\github\legacyofInfest\src\framework\ecs\components.py', 'r', encoding='utf-8') as f:
    content = f.read()

old = '''# Estos componentes encapsulan comportamientos reutilizables que antes
# vivían duplicados en cada clase de enemigo. Ahora se adjuntan a la
# entidad y los sistemas ECS los ejecutan, permitiendo composición.
'''

new = '''# Estos componentes encapsulan comportamientos reutilizables que antes
# vivían duplicados en cada clase de enemigo. Ahora se adjuntan a la
# entidad y los sistemas ECS los ejecutan, permitiendo composición.


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
'''

content = content.replace(
    '# Estos componentes encapsulan comportamientos reutilizables que antes\n# vivían duplicados en cada clase de enemigo. Ahora se adjuntan a la\n# entidad y los sistemas ECS los ejecutan, permitiendo composición.\n',
    new
)

with open(r'C:\Users\pcruz\github\legacyofInfest\src\framework\ecs\components.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Done')