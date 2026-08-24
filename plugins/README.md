# Plugins

Extensiones del motor que **no tocan el núcleo** (AUD-296).

Un plugin es un `.py` en este directorio con una función `registrar(gestor)`:

```python
def registrar(gestor):
    def mi_overlay(superficie, escena, **_):
        ...  # pinta encima de todo
    gestor.enganchar("escenario_dibujado", mi_overlay)
```

Se cargan solos al arrancar. Los ficheros que empiezan por `_` no, para que un
plugin pueda tener módulos auxiliares.

## Los ganchos

| Nombre | Cuándo | Recibe |
|---|---|---|
| `juego_arrancado` | una vez, con el motor montado | `app` |
| `escenario_cargado` | al entrar en un nivel, ya cargado | `escena`, `stage` |
| `escenario_actualizado` | una vez por fotograma, tras el juego | `escena`, `dt` |
| `escenario_dibujado` | encima de todo lo demás | `superficie`, `escena` |

**Acepta siempre `**_`.** Los ganchos se llaman con argumentos por nombre, y
esa regla es lo que permite añadir datos a un gancho sin romper los plugins ya
escritos.

## Si tu plugin falla

Se registra con su traza y se sigue jugando. Al **segundo** fallo del mismo
gancho se desengancha: esto corre por fotograma, y sesenta trazas por segundo
entierran el registro donde estaría la causa. Mira el fichero de registro, que
está junto a las partidas.

La lista de ganchos es corta a propósito: cada uno es una promesa de
estabilidad hacia veintiséis personas, y una API grande que hay que mantener
compatible es peor regalo que una pequeña.
