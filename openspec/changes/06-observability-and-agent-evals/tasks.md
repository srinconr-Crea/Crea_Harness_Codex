# Tasks

## 1. Dependencia y contratos

- [ ] 1.1 Confirmar 05-databricks-validation-and-evidence implementado y verificado; registrar commit/version/evidencia y comprobar que el incremento no comienza con dependencia pendiente.
- [ ] 1.2 Definir schemas de eventos/uso y probar null, scopes, deduplicación, redacción y ausencia de costo inventado. Documentar contratos/errores en el mismo grupo y comprobar ejemplos contra schemas.

## 2. Comportamiento y pruebas

- [ ] 2.1 Certificar fuentes Desktop soportadas; implementar adaptador o unavailable explícito y probar cobertura de eventos/hooks. Documentar el comportamiento entregado y conservar resultado real de su prueba/protocolo.
- [ ] 2.2 Implementar validación y runner de eval manual/automático soportado con fixtures del 01 y versiones congeladas. Documentar el comportamiento entregado y conservar resultado real de su prueba/protocolo.
- [ ] 2.3 Implementar scorers deterministas por check y protocolo de anotación/juez opcional calibrado; detectar findings falsos. Documentar el comportamiento entregado y conservar resultado real de su prueba/protocolo.
- [ ] 2.4 Ejecutar al menos tres repeticiones de cada caso requerido y producir matriz de roles/modelos/esfuerzo con dataset/runtime constantes. Documentar el comportamiento entregado y conservar resultado real de su prueba/protocolo.
- [ ] 2.5 Implementar gates de promoción y reporte comparativo; probar evaluación incompleta, regresión crítica y resultados de superficie incorrecta. Documentar el comportamiento entregado y conservar resultado real de su prueba/protocolo.
- [ ] 2.6 Seleccionar casos por milestone y reservar holdout para promoción; verificar que casos 07/08 pendientes no se computan como aprobados en gate 06.

## 3. Verificación del incremento

- [ ] 3.1 Trazar todos los escenarios delta y casos asignados de docs/planning/quality a tests/protocolos y evidencia; comprobar críticos, negativos y not_run/blocked sin falsos passed.
- [ ] 3.2 Ejecutar comprobaciones pertinentes del kit y smoke de recursos instalados; verificar que no cambian contratos v1, clientes ajenos o configuración global.
- [ ] 3.3 Ejecutar openspec validate 06-observability-and-agent-evals --strict y openspec-verify-change; entregar evidencia del criterio de salida (Evals ejecutados con trazabilidad y gate reproducible; tokens/costos desconocidos se mantienen null con motivo.) y habilitar el siguiente incremento solo si se cumple.
