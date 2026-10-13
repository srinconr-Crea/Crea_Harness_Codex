# Piloto NaturaPet HU-BRONZE-001-Codex-Local

Fecha: 2026-10-13. Trabajo autorizado por el usuario para probar una HU acotada y registrar qué falta antes de 08.

## Entrega comprobada

- [PR draft NaturaPet #12](https://github.com/srinconr-Crea/Naturapet_DLH/pull/12), rama `feature/hu-bronze-001-normalize-table-name`, base `develop`.
- Base cliente `c5efcf154c7e56101e6dd6c3ea830f6512e6b184`; commit remoto final `cfffe55e8eb393a178d5cd509ef1e2c0a1bf2886`, comprobado mediante `git ls-remote`.
- Único código modificado: cuerpo de `normalize_table_name` en `src/common/schema.py`. Once casos parametrizados nuevos, sin dependencias nuevas.
- OpenSpec `bronze-ingestion` sincronizado y cambio archivado con 6/6 tareas completas. Diez main specs pasan validación strict. Los otros diez requisitos Bronze, fuentes y Purpose se preservaron.
- Revisión independiente sin hallazgos y comprobación de límites adicionales.
- [Evidencia versionada del candidato](https://github.com/srinconr-Crea/Naturapet_DLH/blob/cfffe55e8eb393a178d5cd509ef1e2c0a1bf2886/openspec/changes/archive/2026-10-13-hu-bronze-001-normalize-table-name/verification.json) con hashes de ZIP y fuentes, IDs y resultados. La correlación run/attempt/hash y la igualdad de las fuentes ejecutadas con las fuentes finales se verificaron antes del push.

## Ejecución remota real

El usuario seleccionó `CREA_DEV` y autorizó buscar el Job sandbox. Se identificó `611081415041874`, `[dev srinconr] demo_harness_sandbox`, identidad `dac4cb01-380f-4af5-b594-132d6d693beb`, distinta de la App `8910cd3e-32f6-4c75-b16f-b5ff3ea258d2`.

El runner desplegado se exportó y coincidió con el SHA-256 `cb54ddacc52b3efb5dfd4c0b935d313f1412101cbbbdbfa32829dc79d226ffcd`. Usa Python aislado, pytest y entorno sin credenciales de App; el ZIP se extrae a un temporal. Solo se escribieron artefactos en el volumen administrado `demo_harness_sandbox`; no se ejecutaron recursos ni se escribieron datos NaturaPet.

| Ejecución | Evidencia observada |
| --- | --- |
| [196791846417982](https://adb-7405606739630987.7.azuredatabricks.net/?o=7405606739630987#job/611081415041874/run/196791846417982), fuente original | 6 failed, 5 passed; control negativo esperado |
| [618095537049869](https://adb-7405606739630987.7.azuredatabricks.net/?o=7405606739630987#job/611081415041874/run/618095537049869), candidato focalizado | 11 passed |
| [233846238020350](https://adb-7405606739630987.7.azuredatabricks.net/?o=7405606739630987#job/611081415041874/run/233846238020350), candidato suite completa | 25 passed |

El Job terminó SUCCESS en los tres casos porque el runner pudo escribir los resultados; la prueba negativa conserva `passed=false`, categoría `implementation`, código `pytest_failed`. La suite usa cadenas y mocks; no demuestra ejecución Spark ni ingesta real. Localmente también se observaron seis fallos originales y 25 éxitos después.

## Autorización y límites para 08

El usuario autorizó explícitamente: «Sí, publicar PR draft de piloto y conservar los bloqueos», tras revisar el resultado y la diferencia con la publicación certificada. El PR se creó mediante Git/Codex y el conector GitHub; fue adjuntado a este chat. No se usó `harness pr publish` ni se alteró su gate. Merge y despliegue siguen siendo humanos.

Este Job pertenece al sandbox del MVP Databricks y usa `spark_python_task` con parámetros ZIP/pytest. El adaptador remoto de Local-Harness exige otro contrato (notebook y fixture). Su éxito no certifica ese adaptador ni resuelve silenciosamente la aceptación pendiente de 06.

| Pendiente vigente | Estado después de la HU |
| --- | --- |
| 126 evaluaciones reales de 06 y 18 de 07 | 144 siguen `not_run`; pytest no es una captura de agentes Luna/medium |
| Smoke 07 en repo sintético real con gates | Pendiente; el PR cliente se publicó mediante excepción de piloto |
| HU fuente → binding/aprobación → PR y reconciliación sin duplicados | Pendiente en Local-Harness; esta HU fue suministrada por chat |
| Inicio de 08 con dependencias verificadas | Bloqueado; no se modifican las tareas de 08 |

Se mantienen `local_harness_certified=false`, `next_increment_enabled=false` y el gate de publicación de Local-Harness bloqueado. La HU y su PR están entregados; falta ejecutar y evaluar los protocolos reales con el modelo requerido, verificar el sandbox compatible de Local-Harness y completar su publicación/reanudación antes de habilitar 08. Los históricos de 06/07 permanecen intactos.
