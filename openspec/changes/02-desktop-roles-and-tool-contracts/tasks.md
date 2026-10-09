# Tasks

## 1. Dependencia y contratos

- [x] 1.1 Confirmar 01-quality-practices-and-eval-foundation implementado y verificado; registrar commit/version/evidencia y comprobar que el incremento no comienza con dependencia pendiente.
- [x] 1.2 Definir roles y ToolRequirement con entradas/salidas acotadas, ownership de archivos y límites de delegación/concurrencia. Documentar contratos/errores en el mismo grupo y comprobar ejemplos contra schemas.

## 2. Comportamiento y pruebas

- [x] 2.1 Crear plantillas y Skills propias que referencien prácticas del 01; probar resolución de referencias y evitar activación global. Documentar el comportamiento entregado y conservar resultado real de su prueba/protocolo.
- [x] 2.2 Implementar preview/apply/recover de integración con hashes/backups, confinamiento Windows y pruebas de drift/AGENTS personalizado. Documentar el comportamiento entregado y conservar resultado real de su prueba/protocolo.
- [x] 2.3 Definir comprobación Desktop por rol, modelo/esfuerzo, Skill y herramienta; ejecutar desde la app objetivo sin sustituirla por CLI. Documentar el comportamiento entregado y conservar resultado real de su prueba/protocolo.
- [x] 2.4 Verificar sandbox/MCP efectivo y cobertura de hooks usando recursos sintéticos; registrar unsupported/not_checked y conflictos. Conservar el fallo observado de escritura en auditor/verifier; comprobar sesión de revisión independiente read-only solo si Desktop expone el ajuste, sin exigir su éxito para preparación supervisada. Documentar el comportamiento entregado y conservar resultado real de su prueba/protocolo.
- [x] 2.5 Ejecutar protocolo de eval manual del 01 para roles y conservar inputs/outputs originales, evidencia de descubrimiento/selección real y anotación humana de E03/E04. Registrar defectos/limitaciones aceptadas sin falsos passed; no declarar certificado a partir de aceptación supervisada. Documentar el comportamiento entregado y conservar resultado real de su prueba/protocolo.

- [x] 2.6 Implementar resultado de preparación supervisada separado de DesktopCertificate, aceptación explícita ligada a cliente/checkout/catálogo/candidato/evidencia y motivos por capacidad. Probar aceptación ausente/obsoleta, capacidad requerida fallida y que assess_certificate conserva rechazo de sandbox conflictivo.
- [x] 2.7 Implementar captura/comparación de contenido y rutas autorizadas del candidato antes/después de revisión supervisada. Probar candidato intacto, cambios, creaciones/eliminaciones y conservación de evidencia sin rollback; documentar que detecta drift pero no impide escritura.

## 3. Verificación del incremento

- [x] 3.1 Trazar todos los escenarios delta y casos asignados de docs/planning/quality a tests/protocolos y evidencia; comprobar críticos, negativos y not_run/blocked sin falsos passed.
- [x] 3.2 Ejecutar comprobaciones pertinentes del kit y smoke de recursos instalados; verificar que no cambian contratos v1, clientes ajenos o configuración global.

Evidencia local y límites: [desktop-integration.md](../../../docs/evidence/desktop-integration.md).
El usuario aprobó adaptar 02 a preparación supervisada. La evidencia Desktop
muestra selección de roles y escritura permitida de auditor/verifier; la
certificación estricta sigue fallida. El modo supervisado y comparación del candidato están implementados y probados.
La matriz conserva conflictos/not_checked y la anotación humana acepta el defecto
de E04 sin falsos passed. Verificación final completa: suite 262, adaptación 24, wheel con 15 checks y 8 schemas.
03 habilitado para onboarding preparado; fases con capacidades requeridas fallidas
siguen bloqueadas. El certificado estricto conserva false.
- [x] 3.3 Ejecutar openspec validate 02-desktop-roles-and-tool-contracts --strict y openspec-verify-change; entregar evidencia del criterio de salida (Preparación supervisada implementada y verificada, matriz de capacidades observadas y limitaciones aceptadas explícitamente, y evidencia de evals con anotación humana; la certificación estricta se informa por separado y no es requisito para preparar onboarding. Archivos presentes nunca equivalen a certificación.) y habilitar el siguiente incremento solo si se cumple.
