# Comprehensive Project Audit Checklist

## Fase 1: Mapeo y Contexto Inicial
- [ ] Revisar todos los documentos de especificación (docs/00-52, README, etc.)
- [ ] Catalogar todas las fuentes de verdad del proyecto
- [ ] Identificar discrepancias obvias entre documentación y estructura actual

## Fase 2: Auditoría de Consistencia Documentación vs Implementación
- [ ] Verificar que cada característica documentada está implementada en src/
- [ ] Verificar que cada implementación en src/ está documentada
- [ ] Detectar features documentados pero no implementados
- [ ] Detectar features implementados pero no documentados
- [ ] Detectar implementaciones obsoletas o duplicadas

## Fase 3: Auditoría de Código (src/)
- [ ] Revisar src/engine/ - núcleo del motor
- [ ] Revisar src/framework/ - framework base
- [ ] Revisar src/stages/ - niveles/escenarios
- [ ] Revisar src/__init__.py

## Fase 4: Auditoría de Scripts (scripts/)
- [ ] Revisar cada script de utilidad
- [ ] Verificar que los paths referenciados existen
- [ ] Verificar consistencia de importaciones

## Fase 5: Auditoría de Assets
- [ ] Verificar assets referenciados vs assets existentes
- [ ] Validar estructura de directorios de assets

## Fase 6: Auditoría de Tests
- [ ] Revisar tests/ y su cobertura
- [ ] Verificar que los tests reflejan la implementación actual
- [ ] Identificar tests obsoletos o rotos

## Fase 7: Auditoría de Configuración
- [ ] Revisar pyproject.toml, requirements.txt, requirements.lock
- [ ] Revisar build.spec, build_nuitka.bat
- [ ] Revisar .flake8, .gitignore, .gitattributes

## Fase 8: Auditoría de Localización (locale/)
- [ ] Revisar en.json y es.json para consistencia

## Fase 9: Auditoría de Documentación Educativa
- [ ] Revisar docs/entregable01/02/03, docs/eval/, docs/labs/, etc.
- [ ] Verificar coherencia con Syllabus y Academic Rubrics

## Fase 10: Reporte Final y Correcciones
- [ ] Compilar todas las inconsistencias encontradas
- [ ] Implementar correcciones para cada inconsistencia verificable
- [ ] Actualizar documentación, tests y código según sea necesario
- [ ] Verificación final de que no se introdujeron regresiones
