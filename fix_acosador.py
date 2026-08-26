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


# ════════════════════════════════════════════════════════════════
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


# ════════════════════════════════════════════════════════════════
# AUD-634 — Componentes de comportamiento reutilizables (Behavior Components)''')

with open(r'C:\Users\pcruz\github\legacyofInfest\src\framework\ecs\components.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Done')