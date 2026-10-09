# Tasks

## 1. Dependencia y contratos

- [x] 1.1 Confirmar los dos incrementos archivados implementado y verificado; registrar commit/version/evidencia y comprobar que el incremento no comienza con dependencia pendiente.
- [x] 1.2 Formalizar modelos/schemas PracticePack, TestCase y EvalCase y probar IDs duplicados, referencias rotas, versiones desconocidas y límites. Documentar contratos/errores en el mismo grupo y comprobar ejemplos contra schemas.

## 2. Comportamiento y pruebas

- [x] 2.1 Empaquetar recursos propios y snapshot oficial seleccionado con manifiesto SHA-256, licencia/NOTICE y sin ejecución de scripts upstream. Documentar el comportamiento entregado y conservar resultado real de su prueba/protocolo.
- [x] 2.2 Implementar resolución de práctica común más extensión cliente y verificar conflictos, excepciones y ausencia de ampliación de política. Documentar el comportamiento entregado y conservar resultado real de su prueba/protocolo.
- [x] 2.3 Convertir los casos de docs/planning/quality en fixtures validados; mantener status not_run y oráculos independientes. Documentar el comportamiento entregado y conservar resultado real de su prueba/protocolo.
- [x] 2.4 Ejecutar tests de recursos, correspondencia schemas/modelos y smoke del wheel instalado; documentar alcance sin certificar agentes. Documentar el comportamiento entregado y conservar resultado real de su prueba/protocolo.

## 3. Verificación del incremento

- [x] 3.1 Trazar todos los escenarios delta y casos asignados de docs/planning/quality a tests/protocolos y evidencia; comprobar críticos, negativos y not_run/blocked sin falsos passed.
- [x] 3.2 Ejecutar comprobaciones pertinentes del kit y smoke de recursos instalados; verificar que no cambian contratos v1, clientes ajenos o configuración global.
- [x] 3.3 Ejecutar openspec validate 01-quality-practices-and-eval-foundation --strict y openspec-verify-change; entregar evidencia del criterio de salida (Catálogos cargables, íntegros y trazables; ningún recurso activa herramientas o produce resultados ficticios.) y habilitar el siguiente incremento solo si se cumple.
