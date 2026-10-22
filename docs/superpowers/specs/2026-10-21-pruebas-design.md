# Integración local de pruebas Crea 0.1.4

La petición autoriza adaptar el kit del repositorio en la rama existente, conservar
todo en local y actualizar configuracion-manual.md. El prompt adjunto es la
especificación de adaptación; no autoriza operar proyectos o servicios de ejemplo.

Fuente inmutable: artifacts/crea-manual-kit-0.1.3. Staging/entregable:
artifacts/crea-manual-kit-0.1.4. Copiar íntegra la skill suministrada, conservar
upstream/licencias y registrar cualquier adaptación de la skill Crea.

Arquitectura: contract.py sigue siendo selector/gate puro; módulos separados en
scripts/crea/testing/ obtienen Git real, validan Draft2020-12, ejecutan argv local
revisado y convierten JUnit/coverage en resultados trazables. Una CLI coordina
plan/run/gate mediante acciones separadas. Planificar nunca ejecuta suites.
Catálogo único docs/pruebas/policy.json; required_checks contiene solo referencias
a IDs de ese catálogo. Sin comandos alternativos en proyecto.json.

Git conserva base/HEAD/index/worktree/untracked, renames, deletes y conflictos;
excluye únicamente outputs de evidencia declarados de una HU, con recibo de
exclusiones. Planes incluyen huella del inventario Git. Gate vuelve a obtenerlo.
No se admite evidencia ajena o alterada, cero tests ni skips requeridos.

Flujo cliente: Planner → nueva solicitud humana de apply → Developer
ready_for_test → Tester ready_for_review → Reviewer verify/sync → aprobación
humana archive/publicación. Un rol activo; sin subdelegación; contador global.
OpenSpec conserva sus operaciones y pausas; tareas separadas por rol.

Entregar fases locales coherentes y verificadas. Runtime remoto, Spark, SAST,
mutation, evals de modelos, CI y adopción entre planes permanecen inactivos con
causa explícita y bloqueo si una regla los requiere. Incluir procedimientos,
catálogos y contratos, sin fingir adaptadores completos. Evals deterministas de
guardas locales sí se prueban. No instalar herramientas globales ni operar remoto.

Aceptación: pruebas locales reales de Git/procesos/reportes/esquemas/vigencia,
verificador original/personalizado, checks upstream intactos, auditoría de
neutralidad sobre árbol y ZIP con identificadores externos y revisión semántica,
manifest SHA256 regenerado e informe con límites y piloto Codex/runtime pendiente.
