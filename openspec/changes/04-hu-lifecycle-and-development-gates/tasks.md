# Tasks

## 1. Dependencia y contratos

- [ ] 1.1 Confirmar 03-guided-client-onboarding implementado y verificado; registrar commit/version/evidencia y comprobar que el incremento no comienza con dependencia pendiente.
- [ ] 1.2 Crear contratos y migraciones del estado por HU con aislamiento alpha/beta y recuperación de intento interrumpido. Documentar contratos/errores en el mismo grupo y comprobar ejemplos contra schemas.

## 2. Comportamiento y pruebas

- [ ] 2.1 Implementar transiciones/gates y probar aprobación obsoleta, cliente/checkout incorrectos y candidato modificado. Documentar el comportamiento entregado y conservar resultado real de su prueba/protocolo.
- [ ] 2.2 Completar Skill de HU y contratos de entrega entre roles; analizar cambios pequeños sin fanout obligatorio. Documentar el comportamiento entregado y conservar resultado real de su prueba/protocolo.
- [ ] 2.3 Implementar manifiestos, asignación de un escritor, límites de retries/delegaciones y worktrees cuando se permita. Documentar el comportamiento entregado y conservar resultado real de su prueba/protocolo.
- [ ] 2.4 Persistir contexto/fuentes/decisiones y revalidar al reanudar; probar pérdida de proceso y ausencia de duplicación. Documentar el comportamiento entregado y conservar resultado real de su prueba/protocolo.
- [ ] 2.5 Verificar con HU sintética hasta ready_to_publish usando evidencia simulada claramente marcada, sin tratarla como validación real ni crear PR. Documentar el comportamiento entregado y conservar resultado real de su prueba/protocolo.

## 3. Verificación del incremento

- [ ] 3.1 Trazar todos los escenarios delta y casos asignados de docs/planning/quality a tests/protocolos y evidencia; comprobar críticos, negativos y not_run/blocked sin falsos passed.
- [ ] 3.2 Ejecutar comprobaciones pertinentes del kit y smoke de recursos instalados; verificar que no cambian contratos v1, clientes ajenos o configuración global.
- [ ] 3.3 Ejecutar openspec validate 04-hu-lifecycle-and-development-gates --strict y openspec-verify-change; entregar evidencia del criterio de salida (Cada transición queda registrada y los gates rechazan alcance, aprobación o evidencia incorrectos; no se publican cambios todavía.) y habilitar el siguiente incremento solo si se cumple.
