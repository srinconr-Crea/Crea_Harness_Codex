# Integración local de pruebas — 0.1.4

Entregables: [kit](../artifacts/crea-manual-kit-0.1.4/),
[manual](../artifacts/crea-manual-kit-0.1.4/docs/configuracion-manual.md),
[ZIP](../artifacts/crea-manual-kit-0.1.4.zip),
[recibo final](../artifacts/crea-manual-kit-0.1.4.zip.validation.json).

Rama solicitada conservada; fuente 0.1.3 intacta. Cambios sin commit/push/PR.
Nueva distribución local, sin modificar repositorios cliente.

## Verificación

| Comprobación | Resultado |
|---|---|
| Tests helper/adaptadores/configuración/neutralidad | 58 passed |
| Git → plan → pytest/JUnit → resultados → gate | Passed, fixtures sintéticos locales |
| Schemas / roles / skills | 10 Draft2020-12 / 4 roles / 25 skills |
| Parseo estático | 27 Python / 5 TOML / 18 YAML |
| Verificador fuente 0.1.3 | 254 comprobaciones passed |
| Verificador 0.1.4 original | 310 comprobaciones + validación estricta, passed |
| Copia personalizada sintética | 36 comprobaciones + validación estricta, passed |
| Copia personalizada presentada como original | Rechazada, como corresponde |
| CLI documental en copia personalizada | plan/run/gate passed, cero checks de negocio y cero runtime |
| Skill suministrada | 19 archivos presentes: 16 idénticos y 3 adaptados documentados |
| Preservación fuente | 223 archivos del manifest fuente verificados |
| Skills conservadas/licencias | 182 archivos byte a byte |
| Auditoría árbol/ZIP | Cero coincidencias pendientes; 110 coincidencias neutrales revisadas por contexto/hash |
| ZIP | Inventario y bytes de 275 entradas comprobados, con SHA256 |

Revisión independiente cerró defectos de coverage malformado, sobrescritura de
evidencia/aliases y preflight previo al schema. Primero se reprodujeron mediante
regresiones; quedaron cubiertos por los 58 tests.

Evaluación de instrucciones con subagente, sin simular roles nativos: consumir
batería vigente, invalidar untracked/fixtures, bloquear runtime inactivo, rechazar
inyección en diff y permitir revisión legítima, conservar contador global y
separar tareas mixtas. Se precisó qué evento cuenta como ronda.

## Límites por fases

Implementados: selector/gate puro, Git completo, argv local revisado/timeout,
pytest/JUnit/cobertura, validación estricta offline y vigencia/integridad.
Runtime/Spark, SAST/Semgrep, mutation, evals de modelos, adopción entre planes y CI
permanecen inactivos y bloquean si son requeridos. Sus contratos/procedimientos no
se presentan como adaptadores ejecutados.

Pendientes: personalización real, descubrimiento/ejecución de los cuatro perfiles
nativos y piloto runtime autorizado. Local no acredita UC/ADLS/DBR ni permisos.
Sin despliegues, recursos remotos, publicación o instalaciones globales.

## Suite del motor histórico — separada del kit manual

Se inició la suite general del motor antecedente (676 casos recolectados), se
observaron dos fallos y se interrumpió antes de completarla: no se declara pasada.
Los dos fallos se reprodujeron individualmente:

- `tests/test_configuration.py::test_documented_fixtures_validate`: la huella
  declarada en un fixture no coincide con los bytes de la política.
- `tests/test_environment_setup.py::test_clone_materializes_only_frozen_child_scope`:
  el clon Git local sintético termina con código 128 en este entorno.

Pasaron `test_traversal_and_linked_ancestors` y
`test_two_clients_and_supported_custom_instructions_are_preserved`.
El motor y esos tests/fixtures no se modificaron. Los fallos requieren diagnóstico
separado y no se ocultan bajo los resultados verdes del kit.

Lista de identificadores y revisiones exactas de neutralidad fuera del repositorio
y distribución. El resumen entregado conserva categorías/conteos sin valores de
origen. Licencias y avisos obligatorios preservados.
