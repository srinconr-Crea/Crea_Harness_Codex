# Tasks

## 1. Dependencia y contratos

- [x] 1.1 Confirmar infraestructura local de 06-observability-and-agent-evals implementada/verificada (439 pruebas, smoke instalado, specs sincronizadas; ec84193/54faea5); registrar evidencia y la excepción autorizada el 2026-10-13 para implementar 07 localmente. Conservar 2.4/3.3 de 06 y las 126 evals Luna/medium pendientes; comprobar que la habilitación de desarrollo no abre promoción/publicación ni 08.
- [x] 1.2 Definir contratos de proveedores y fixture offline con cambio de revisión y payload externo no confiable. Documentar contratos/errores en el mismo grupo y comprobar ejemplos contra schemas.

## 2. Comportamiento y pruebas

- [x] 2.1 Implementar lectura GitHub y selección MCP/CLI soportada; probar credenciales faltantes, repo incorrecto y sin efectos de lectura. Documentar el comportamiento entregado y conservar resultado real de su prueba/protocolo.
- [x] 2.2 Implementar preview PR con título/cuerpo/candidato/evidencia y autorización explícita; probar que evals de 06 not_run/blocked permiten preview sin efectos pero bloquean publicación aun con autorización. Documentar el comportamiento entregado y conservar resultado real de su prueba/protocolo.
- [ ] 2.3 Implementar el adaptador de push/create draft PR y reconciliación de resultado ambiguo/duplicado; probarlo con dobles. Conservar smoke de escritura en repo sintético real blocked hasta pasar gates del candidato/evals y recibir autorización específica de destino/acción; un doble no satisface ese smoke. Documentar y conservar evidencia real; no marcar esta tarea completa mientras la comprobación remota requerida esté pendiente.
- [x] 2.4 Integrar cierre OpenSpec y attach de PR verificando candidato después de cambios de specs/evidencia. Documentar el comportamiento entregado y conservar resultado real de su prueba/protocolo.
- [ ] 2.5 Ejecutar evals de proveedores y gate final con contexto malicioso, autorización faltante y PR existente. Documentar el comportamiento entregado y conservar resultado real de su prueba/protocolo.

## 3. Verificación del incremento

- [x] 3.1 Trazar todos los escenarios delta y casos asignados de docs/planning/quality a tests/protocolos y evidencia; comprobar críticos, negativos y not_run/blocked sin falsos passed.
- [x] 3.2 Ejecutar comprobaciones pertinentes del kit y smoke de recursos instalados; verificar que no cambian contratos v1, clientes ajenos o configuración global.
- [ ] 3.3 Ejecutar openspec validate 07-story-and-pr-integrations --strict y openspec-verify-change; entregar evidencia del criterio de salida (HU de fuente trazable a PR draft autorizado con evidencia; repetir o reanudar no duplica publicación.) y habilitar el siguiente incremento solo si se cumple.

## Excepción de dependencia aprobada 2026-10-13

Implementación local de 07 habilitada por decisión expresa del usuario sobre la
infraestructura probada de 06. Se entregan siete tareas con 507 pruebas aprobadas,
smoke instalado y specs sincronizadas. 2.3/2.5/3.3 permanecen pendientes por el
smoke de escritura real y las capturas/anotaciones de agentes; los dobles no
satisfacen ese criterio. La excepción no convierte evaluaciones not_run en
passed ni modifica evidencia histórica de 06. El usuario autorizó el 2026-10-13
archivar con esos pendientes documentados, conservando publicación y 08 bloqueados.
Ver docs/evidence/story-pr-verification.md y su JSON para evidencia observada.
