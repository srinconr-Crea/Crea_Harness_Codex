# Tasks

## 1. Base y contratos para desarrollo local

- [x] 1.1 Registrar commit/version/evidencia de la base implementada de 07 y autorización del 2026-10-13 para desarrollo local anticipado; inventariar pendientes 06/07 y verificar que los gates de certificación, release y publicación permanecen bloqueados.
- [x] 1.2 Crear manifiesto de release/ownership y empaquetar wheel candidato, roles, prácticas, Skills y fuentes/licencias fijadas. Documentar contratos/errores y comprobar ejemplos contra schemas, distinguiendo candidato local de release certificado sin inventar certificados.

## 2. Código y pruebas locales

- [x] 2.1 Implementar bootstrap/launcher revisable y guía desde equipo Windows limpio sin asumir perfiles o confianza preexistentes; probar localmente detección, pasos revisables, ausencia de herramientas y pendientes explícitos. Conservar evidencia local sin declarar instalación real en segundo entorno.
- [x] 2.2 Implementar update preview/apply/recover y pruebas de personalizaciones, drift, reversión y ausencia de eliminación de estado. Documentar el comportamiento entregado y conservar resultado real de su prueba/protocolo.
- [x] 2.3 Preparar protocolos y fixtures de onboarding/HU alpha/beta, piloto Desktop NaturaPet e instalación en segundo entorno; verificar entradas, restricciones y trazabilidad, sin ejecutar efectos remotos ni marcar aceptación.
- [x] 2.4 Implementar estados de implementación/aceptación y gate final de release; comprobar mediante pruebas locales que dependencias not_run/blocked, evals simuladas y publicación manual de piloto conservan certified=false y release_allowed=false, aunque el código local esté completo.

## 3. Aceptación real diferida obligatoria antes de release

- [ ] 3.1 Cerrar los pendientes de 06/07 con 144 capturas/anotaciones reales y eval gate completo, sandbox compatible verificado y smoke de publicación/reanudación del harness sin duplicados; conservar evidencias y comprobar gates vigentes. No sustituirlos por pytest ni por el PR manual NaturaPet.
- [ ] 3.2 Ejecutar onboarding más HU completa en alpha/beta, con interrupciones y fallos de infraestructura documentados. Conservar resultado real del protocolo y comprobar aislamiento de estados/aprobaciones.
- [ ] 3.3 Ejecutar piloto Desktop NaturaPet mediante el flujo del harness con recursos sintéticos seleccionados y PR draft autorizado; preservar restricciones del cliente. Conservar evidencia real; el piloto manual previo es antecedente, no aceptación de este recorrido.
- [ ] 3.4 Completar reporte de aceptación y limitaciones, comprobar eval gate requerido y validar instalación en segundo entorno antes de release. Conservar resultados reales y verificar que ninguna evidencia pendiente se transforma en passed.

## 4. Verificación del incremento

- [x] 4.1 Trazar todos los escenarios delta y casos asignados de docs/planning/quality a tests/protocolos y evidencia; comprobar críticos, negativos y not_run/blocked sin falsos passed. Puede completarse la trazabilidad local conservando abiertos los protocolos de aceptación.
- [x] 4.2 Ejecutar comprobaciones pertinentes del kit y smoke local de recursos instalados en entorno aislado; verificar que no cambian contratos v1, clientes ajenos o configuración global. No sustituye instalación real en segundo entorno.
- [ ] 4.3 Ejecutar openspec validate 08-pilot-and-reproducible-distribution --strict y openspec-verify-change; entregar evidencia del cierre de 06/07 y criterio de salida (Usuario nuevo completa onboarding y HU en Desktop, dos clientes permanecen aislados y update/recover preserva personalizaciones.). Certificar release, archivar como aceptado y habilitar el siguiente incremento solo si se cumple; código completo con aceptación pendiente mantiene esta tarea abierta.
