# Tasks

## 1. Dependencia y contratos

- [ ] 1.1 Confirmar 02-desktop-roles-and-tool-contracts implementado y verificado para preparación supervisada, con aceptación explícita de limitaciones y evidencia; no exigir certificación estricta completa para preparar onboarding ni habilitar fases con capacidad requerida fallida; registrar commit/version/evidencia y comprobar que el incremento no comienza con dependencia pendiente.
- [ ] 1.2 Crear plantillas rellenable y entrevista con required/optional/unknown y fuente de cada dato; probar usuario nuevo y repos preparado. Documentar contratos/errores en el mismo grupo y comprobar ejemplos contra schemas.

## 2. Comportamiento y pruebas

- [ ] 2.1 Definir nuevos contratos y validar separación cliente/checkout/conexiones, secretos y compatibilidad con contratos v1. Documentar el comportamiento entregado y conservar resultado real de su prueba/protocolo.
- [ ] 2.2 Implementar preview compuesto usando init e integración del 02, con autorización por etapa y sin efectos del dry-run. Documentar el comportamiento entregado y conservar resultado real de su prueba/protocolo.
- [ ] 2.3 Implementar aplicación/recuperación por etapa sin sobrescritura opaca; probar fallos antes/después del binding e integración. Documentar el comportamiento entregado y conservar resultado real de su prueba/protocolo.
- [ ] 2.4 Implementar informe prepared/preparación supervisada aceptada/certified/remote_not_checked, conservando conflictos y bloqueos por capacidad; probar sandbox conflictivo aceptado sin certified y rechazo de fase que lo requiera. Implementar generación del paquete de contexto sin copiar negocio al núcleo. Documentar el comportamiento entregado y conservar resultado real de su prueba/protocolo.
- [ ] 2.5 Probar dos clientes sintéticos, onboarding repetido, AGENTS personalizado, datos ambiguos y ausencia de herramientas. Documentar el comportamiento entregado y conservar resultado real de su prueba/protocolo.
- [ ] 2.6 Implementar preparación compuesta para AGENTS personalizado sin bypass de init v1; verificar escenario Custom AGENTS preserved, política bootstrap protegida y snapshots del preview.

## 3. Verificación del incremento

- [ ] 3.1 Trazar todos los escenarios delta y casos asignados de docs/planning/quality a tests/protocolos y evidencia; comprobar críticos, negativos y not_run/blocked sin falsos passed.
- [ ] 3.2 Ejecutar comprobaciones pertinentes del kit y smoke de recursos instalados; verificar que no cambian contratos v1, clientes ajenos o configuración global.
- [ ] 3.3 Ejecutar openspec validate 03-guided-client-onboarding --strict y openspec-verify-change; entregar evidencia del criterio de salida (Una persona nueva completa el flujo con plantilla o entrevista y recibe configuración trazable sin ampliar permisos por inferencia.) y habilitar el siguiente incremento solo si se cumple.
