# Tasks

## 1. Dependencia y contratos

- [x] 1.1 Confirmar 01-quality-practices-and-eval-foundation implementado y verificado; registrar commit/version/evidencia y comprobar que el incremento no comienza con dependencia pendiente.
- [x] 1.2 Definir roles y ToolRequirement con entradas/salidas acotadas, ownership de archivos y límites de delegación/concurrencia. Documentar contratos/errores en el mismo grupo y comprobar ejemplos contra schemas.

## 2. Comportamiento y pruebas

- [x] 2.1 Crear plantillas y Skills propias que referencien prácticas del 01; probar resolución de referencias y evitar activación global. Documentar el comportamiento entregado y conservar resultado real de su prueba/protocolo.
- [x] 2.2 Implementar preview/apply/recover de integración con hashes/backups, confinamiento Windows y pruebas de drift/AGENTS personalizado. Documentar el comportamiento entregado y conservar resultado real de su prueba/protocolo.
- [ ] 2.3 Definir comprobación Desktop por rol, modelo/esfuerzo, Skill y herramienta; ejecutar desde la app objetivo sin sustituirla por CLI. Documentar el comportamiento entregado y conservar resultado real de su prueba/protocolo.
- [ ] 2.4 Verificar sandbox/MCP efectivo y cobertura de hooks usando recursos sintéticos; registrar unsupported/not_checked y conflictos. Documentar el comportamiento entregado y conservar resultado real de su prueba/protocolo.
- [ ] 2.5 Ejecutar protocolo de eval manual del 01 para roles y conservar evidencia de descubrimiento/selección real antes de declarar certificado. Documentar el comportamiento entregado y conservar resultado real de su prueba/protocolo.

## 3. Verificación del incremento

- [ ] 3.1 Trazar todos los escenarios delta y casos asignados de docs/planning/quality a tests/protocolos y evidencia; comprobar críticos, negativos y not_run/blocked sin falsos passed.
- [x] 3.2 Ejecutar comprobaciones pertinentes del kit y smoke de recursos instalados; verificar que no cambian contratos v1, clientes ajenos o configuración global.

Evidencia local y límites: [desktop-integration.md](../../../docs/evidence/desktop-integration.md).
El usuario dejó las pruebas Desktop pendientes. 2.3/2.4/2.5, la aceptación
completa de 3.1 y el criterio de salida de 3.3 siguen abiertos; 03 no habilitado.
- [ ] 3.3 Ejecutar openspec validate 02-desktop-roles-and-tool-contracts --strict y openspec-verify-change; entregar evidencia del criterio de salida (Configuración concreta revisable y evidencia en Desktop de cada capacidad habilitada; archivos presentes nunca equivalen a certificación.) y habilitar el siguiente incremento solo si se cumple.
