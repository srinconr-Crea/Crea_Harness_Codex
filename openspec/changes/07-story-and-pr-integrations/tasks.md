# Tasks

## 1. Dependencia y contratos

- [ ] 1.1 Confirmar 06-observability-and-agent-evals implementado y verificado; registrar commit/version/evidencia y comprobar que el incremento no comienza con dependencia pendiente.
- [ ] 1.2 Definir contratos de proveedores y fixture offline con cambio de revisión y payload externo no confiable. Documentar contratos/errores en el mismo grupo y comprobar ejemplos contra schemas.

## 2. Comportamiento y pruebas

- [ ] 2.1 Implementar lectura GitHub y selección MCP/CLI soportada; probar credenciales faltantes, repo incorrecto y sin efectos de lectura. Documentar el comportamiento entregado y conservar resultado real de su prueba/protocolo.
- [ ] 2.2 Implementar preview PR con título/cuerpo/candidato/evidencia y autorización explícita; no publicar con estado incompleto. Documentar el comportamiento entregado y conservar resultado real de su prueba/protocolo.
- [ ] 2.3 Implementar push/create draft PR y reconciliación de resultado ambiguo/duplicado usando dobles y repos sintético autorizado. Documentar el comportamiento entregado y conservar resultado real de su prueba/protocolo.
- [ ] 2.4 Integrar cierre OpenSpec y attach de PR verificando candidato después de cambios de specs/evidencia. Documentar el comportamiento entregado y conservar resultado real de su prueba/protocolo.
- [ ] 2.5 Ejecutar evals de proveedores y gate final con contexto malicioso, autorización faltante y PR existente. Documentar el comportamiento entregado y conservar resultado real de su prueba/protocolo.

## 3. Verificación del incremento

- [ ] 3.1 Trazar todos los escenarios delta y casos asignados de docs/planning/quality a tests/protocolos y evidencia; comprobar críticos, negativos y not_run/blocked sin falsos passed.
- [ ] 3.2 Ejecutar comprobaciones pertinentes del kit y smoke de recursos instalados; verificar que no cambian contratos v1, clientes ajenos o configuración global.
- [ ] 3.3 Ejecutar openspec validate 07-story-and-pr-integrations --strict y openspec-verify-change; entregar evidencia del criterio de salida (HU de fuente trazable a PR draft autorizado con evidencia; repetir o reanudar no duplica publicación.) y habilitar el siguiente incremento solo si se cumple.
