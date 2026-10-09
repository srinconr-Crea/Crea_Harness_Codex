# Tasks

## 1. Dependencia y contratos

- [ ] 1.1 Confirmar 07-story-and-pr-integrations implementado y verificado; registrar commit/version/evidencia y comprobar que el incremento no comienza con dependencia pendiente.
- [ ] 1.2 Crear manifiesto de release/ownership y empaquetar wheel, roles, prácticas, Skills y fuentes/licencias fijadas. Documentar contratos/errores en el mismo grupo y comprobar ejemplos contra schemas.

## 2. Comportamiento y pruebas

- [ ] 2.1 Implementar bootstrap/launcher revisable y guía desde equipo Windows limpio sin asumir perfiles o confianza preexistentes. Documentar el comportamiento entregado y conservar resultado real de su prueba/protocolo.
- [ ] 2.2 Implementar update preview/apply/recover y pruebas de personalizaciones, drift, reversión y ausencia de eliminación de estado. Documentar el comportamiento entregado y conservar resultado real de su prueba/protocolo.
- [ ] 2.3 Ejecutar onboarding más HU completa en alpha/beta, con interrupciones y fallos de infraestructura documentados. Documentar el comportamiento entregado y conservar resultado real de su prueba/protocolo.
- [ ] 2.4 Ejecutar piloto Desktop NaturaPet con recursos sintéticos seleccionados y PR draft autorizado; preservar restricciones del cliente. Documentar el comportamiento entregado y conservar resultado real de su prueba/protocolo.
- [ ] 2.5 Publicar reporte de aceptación y limitaciones, ejecutar eval gate completo y validar instalación en segundo entorno antes de release. Documentar el comportamiento entregado y conservar resultado real de su prueba/protocolo.

## 3. Verificación del incremento

- [ ] 3.1 Trazar todos los escenarios delta y casos asignados de docs/planning/quality a tests/protocolos y evidencia; comprobar críticos, negativos y not_run/blocked sin falsos passed.
- [ ] 3.2 Ejecutar comprobaciones pertinentes del kit y smoke de recursos instalados; verificar que no cambian contratos v1, clientes ajenos o configuración global.
- [ ] 3.3 Ejecutar openspec validate 08-pilot-and-reproducible-distribution --strict y openspec-verify-change; entregar evidencia del criterio de salida (Usuario nuevo completa onboarding y HU en Desktop, dos clientes permanecen aislados y update/recover preserva personalizaciones.) y habilitar el siguiente incremento solo si se cumple.
