# Verificación de HU conversacional y actividad local

Fecha: 15 de octubre de 2026. Cambio: `10-conversational-hu-and-activity-ledger`.
La implementación local añade `work preview/start/status/resume`, SQLite externa
por binding, actividad de adaptadores propios y hooks opcionales. Las pruebas
remotas, Desktop independiente y otra máquina conservan sus estados pendientes.

## Verificación automatizada

La suite completa pasó **676/676**, sin fallos ni omisiones: 48 archivos en
cuatro procesos independientes, sin duplicados, en 973.37 s de tiempo total.
Los grupos terminaron con 130, 248, 155 y 143 aprobadas. Las pruebas dirigidas
de las últimas correcciones pasaron **7/7** en
38.35 s. Se observaron fallos RED antes de corregir la aprobación de una HU
con base cambiada y la selección de un servicio reutilizado. Este último recarga
política/binding antes de comparar setup y escoger ledger, conservando el rechazo
de cambios de identidad y evitando la primera mutación sin inicio registrado.

Una ejecución secuencial se detuvo después de 536 aprobadas porque el fixture de
setup no inicializaba el nuevo ledger; el fixture ahora representa la preparación
actual. Otra ejecución expuso `PermissionError: WinError 5` en el reemplazo atómico
de un journal. Se reprodujo con una denegación transitoria y otra persistente:
el reemplazo reintenta hasta seis veces, con 250 ms máximos de espera total,
solo para errores Windows 5/32/33. Conserva el mismo temporal y el parent fijado;
si persiste la denegación, propaga el error y mantiene el journal anterior.
No se atribuye el error a antivirus u otro proceso sin evidencia de ese origen.
Los fallos detectados durante desarrollo se reprodujeron antes de corregirlos;
las ejecuciones parciales y supersedidas no se cuentan como aceptación.

Las pruebas nuevas cubren identidad, esquema/migración, locks, deduplicación,
fallos de persistencia antes/después del efecto, resultados reales del adaptador,
recuperación desde journals, lecturas sin escritura, consumo/importación,
hooks no confiados y rechazo de atribución ajena. Los efectos remotos usan dobles;
ningún resultado de esos dobles acredita un PR o despliegue real.

## Smoke del wheel instalado

Se instaló el wheel mediante pip offline en `.test-data/smoke10-runtime`.
`scripts/verify_activity_journey.py` se ejecutó con ese Python usando `-I -B`;
la ruta de paquete observada pertenece a su `Lib/site-packages/harness_local`.
SHA256 del wheel probado:
`fcdc94f0da5cc3998f71a4874a259413cb70e8a82c883dff64713f25524afb44`.
La comparación de cada archivo de ambos paquetes dentro del wheel con `src/`
pasó. El kit final contiene ese mismo wheel, con sus 18 huellas verificadas y
Preview del instalador sin conflictos. Manifest SHA256:
`c99ae6f0ff6f7c25f5285c8dcec62a92262b51492c43f86c05a903e0183953cb`;
ZIP SHA256: `5188f03af3142ef61523f8a29ebc5f61741aa8c525d4e3c7a5ca1b921cd3340e`.

| Observación | Resultado |
|---|---|
| Setup preview y work preview | Snapshots idénticos; sin creación de las bases |
| Setup apply autorizado | Preparado; activity.sqlite3 existe antes de la primera HU |
| Work start repetido | Idempotente; conserva HU e intento |
| Implementación local | Dos archivos dentro del alcance positivo aprobado |
| Unittest real | 3 casos aprobados: vacío, decimales y cantidades con signo |
| Interrupción abrupta | Proceso termina con código 17 después del inicio durable |
| Resume | CLI en proceso nuevo recupera la HU persistida |
| Report y export | Lectura sin cambio de SQLite; export exclusivo |
| HU filtrada | 10 inicios, 9 resultados, 1 operación interrumpida pendiente |
| Consumo Desktop | tokens/costo null; supported_attributable_source_unavailable |
| Estado local final | validating, aprobación vigente |

Se dejó deliberadamente pendiente la operación cuyo proceso murió: no se inventa
resultado ni duración. Resume desde proceso nuevo es evidencia de persistencia;
la invocación desde otro chat real continúa `not_run`.

Artefactos locales: `.test-data/journey-smoke10-reviewed/journey-result.json`
(SHA256 `23e53a5163687fe40351e077e5496d4d5dbe62abe358b8e8b0a3c7bd54c85439`)
y `activity-report.json`
(SHA256 `2a709104fb0ce990736aa28d6a1f4230c2904794e5fed18a84a44faffb0033c5`).
Son evidencias locales ignoradas por Git; el protocolo reproducible sí se entrega.

El instalador nativo también terminó `prepared` con recursos instalados en
`.test-data/v10`, descubrimiento de Skill pendiente y `certified=false`.
Esa instalación precede las últimas correcciones de HU y persistencia;
la aceptación del código final corresponde al wheel y recorridos anteriores.

## Piloto NaturaPet seleccionado por el usuario

Checkout: `C:\Users\Stiveen Rincon Ruge\Documents\Databricks\Demos\MVP-Agents\Local v1\Naturapet_DLH`.
Rama local: `codex/10-activity-ledger-pilot`, creada desde `develop`.
Descriptor y preparación tienen commits locales; los dos archivos sintéticos de
`harness_pilot/` permanecen como candidato de la HU `LOCAL-PILOT` en validación.
La política, el binding y las bases se encuentran fuera del checkout, en
`Local v1/ledger-pilot-10`.

El wheel instalado anterior a las últimas correcciones de HU/persistencia ejecutó
setup → aprobación → implementación → tres
unittests → interrupción → resume en proceso nuevo → report/export. Resultado:
**passed**, 10 inicios/9 resultados de HU y una operación interrumpida pendiente.
Candidato: `27f323561f415d5d91c2ae493d6f4b33b4eac85620be1934b3a3fe3d7765c76a`.
Los insumos son sintéticos; el núcleo no contiene configuración del cliente.
No se realizó push, merge, PR ni despliegue del repositorio NaturaPet.

Artefacto: `.test-data/10-naturapet-journey.json`, SHA256
`ce99449e1ca9eba9b131a3dcf74542364a78e020616766b4a26e11adaefaca90`.
El reporte completo permanece en `Local v1/ledger-pilot-10/activity-report.json`.
Tras instalar el wheel final se volvió a consultar ese piloto: aprobación vigente,
estado `validating`, próxima acción `reconcile_pending` y una operación pendiente.
Los hashes de ambas bases SQLite fueron idénticos antes y después de consultar.

## Matriz de capacidades observadas

| Capacidad | Estado observado |
|---|---|
| Comandos propios con binding explícito | enabled; SQLite y recuperación ejercitadas |
| Contratos y eventos importados | Pruebas locales; submitted_events_only |
| Delegación nativa en esta conversación | Probe real de Skill; no acredita roles/revisión de la HU piloto |
| HU piloto supervisada | supervised_single_agent; cero delegaciones |
| Revisión independiente de la HU | blocked_independence_not_observed |
| Hooks del host confiados y recibidos | not_run; adaptador opt-in probado con payloads documentados |
| Tokens/costo Desktop atribuibles | unavailable/null |
| Otra máquina Windows con dos clientes | not_run; usuario indicó que no dispone de otra |
| Otro chat real | not_run; probado proceso nuevo únicamente |
| Validación remota/publicación | not_checked/blocked por gates previos |

La Skill se contrastó con un probe de agente antes/después de sus instrucciones:
el recorrido actualizado evita exigir JSON manual, declara modo supervisado y
no fabrica revisión independiente ni facturación. Los booleanos de capacidades
recibidos por la fachada son declaraciones; no prueban ejecución nativa.

## Límites preservados

Las tareas 3.4 y 5.3 conservan aceptación incompleta. La implementación de resume
y sus pruebas de persistencia/reconciliación están completas; la invocación desde
otro chat humano real no fue observada. El usuario indicó que no tiene segunda máquina,
autorizó avanzar en la ruta local seleccionada y reiteró sync/archive/push.
El archivo es administrativo y conserva esta excepción visible.
OpenSpec confirmó **22 de 24 tareas completas**. El cambio fue archivado en
`openspec/changes/archive/2026-10-15-10-conversational-hu-and-activity-ledger`,
con 3.4 y 5.3 abiertas. La validación estricta del cambio y de las 21 specs
principales pasó; la comparación de las dos specs sincronizadas con sus deltas
no dejó diferencias de requisitos o escenarios.
Las 144 evaluaciones manuales históricas siguen `not_run`; no se modificaron
sus evidencias de 06–08. `certified=false`, `release_allowed=false` y
`publication_allowed=false` se mantienen. Pruebas locales, archivo o push no
satisfacen los gates pendientes.

Las dos specs principales reproducen los ocho requisitos y escenarios de los
deltas (3 de entrada conversacional y 5 del ledger). Consulte la
[guía del producto](../activity-ledger.md) para uso y recuperación.
El [registro de resultados](conversational-activity-results.json) conserva un
resumen de las salidas observadas sin rutas personales ni contenido de sesiones.
