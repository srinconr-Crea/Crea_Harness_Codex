# Tasks

## 1. Dependencia y contratos

- [ ] 1.1 Confirmar 04-hu-lifecycle-and-development-gates implementado y verificado; registrar commit/version/evidencia y comprobar que el incremento no comienza con dependencia pendiente.
- [ ] 1.2 Implementar selección de pruebas por tecnología/impacto con ejemplos del catálogo y reglas required/advisory. Documentar contratos/errores en el mismo grupo y comprobar ejemplos contra schemas.

## 2. Comportamiento y pruebas

- [ ] 2.1 Crear workers aislados y pruebas Python/PySpark sintéticas con selección explícita de runtime y tolerancias de resultados. Documentar el comportamiento entregado y conservar resultado real de su prueba/protocolo.
- [ ] 2.2 Implementar adaptadores SQL/notebook/Delta/job autorizados y preflight de identidad, recursos y limpieza acotada. Documentar el comportamiento entregado y conservar resultado real de su prueba/protocolo.
- [ ] 2.3 Implementar reconciliación idempotente, polling limitado y fallos timeout/hash/identidad cruzada usando dobles de servicio. Documentar el comportamiento entregado y conservar resultado real de su prueba/protocolo.
- [ ] 2.4 Vincular evidencia al candidato y probar missing/not_run/stale/failed como bloqueos de gates exigidos. Documentar el comportamiento entregado y conservar resultado real de su prueba/protocolo.
- [ ] 2.5 Ejecutar smoke remoto sintético solo con entorno seleccionado autorizado; registrar blocked si falta acceso, sin sustituirlo por mocks. Documentar el comportamiento entregado y conservar resultado real de su prueba/protocolo.

## 3. Verificación del incremento

- [ ] 3.1 Trazar todos los escenarios delta y casos asignados de docs/planning/quality a tests/protocolos y evidencia; comprobar críticos, negativos y not_run/blocked sin falsos passed.
- [ ] 3.2 Ejecutar comprobaciones pertinentes del kit y smoke de recursos instalados; verificar que no cambian contratos v1, clientes ajenos o configuración global.
- [ ] 3.3 Ejecutar openspec validate 05-databricks-validation-and-evidence --strict y openspec-verify-change; entregar evidencia del criterio de salida (Evidencia determinista y remota genuina donde se exige, ligada al candidato; sin credenciales o runtime disponibles se registra bloqueo.) y habilitar el siguiente incremento solo si se cumple.
