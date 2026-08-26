# ADR-006: Pre-commit hook con ruff, mypy y check_translations

**Estado:** Aceptado (2026-08-26)

**Contexto:** La suite tiene >6000 pruebas que tardan ~17 minutos. Un error de
lint o de tipo no se detecta hasta CI, que es demasiado tarde para prevenir
regresiones en un repositorio donde múltiples agentes y estudiantes commitean.

**Decisión:** `.pre-commit-config.yaml` ejecuta ruff check --fix, mypy sobre
mypy_scope.txt y check_translations --ci antes de cada commit.

**Consecuencias:** Los errores de estilo y tipo se detectan en <30 segundos
en local. El coste por commit es despreciable frente a esperar CI completo.
