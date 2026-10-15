# Tasks

## 1. Almacén local y contratos

- [x] 1.1 Añadir ActivityEvent, UsageObservation, LedgerQuery y LedgerReport versionados reutilizando validadores de observabilidad; verificar identidad/ámbito, unidades, nullable tokens/costos, límites de payload y redacción antes de persistir.
- [x] 1.2 Implementar activity.sqlite3 externa con metadata de identidad, esquema versionado, operaciones/eventos/consumos/cobertura y migración explícita respaldada; probar reapertura, aislamiento de dos clientes, esquema incompatible y hu.sqlite3 intacta.
- [x] 1.3 Añadir inicialización como etapa autorizada del setup de 09 y comando explícito para clientes preparados existentes; verificar base antes de primera HU, importación única de journal de setup y preview sin crear bases.
- [x] 1.4 Implementar transacciones/deduplicación, espera acotada y estados pendientes de persistencia; probar proceso interrumpido, DB busy/disco no disponible, identidad errónea y rechazo de iniciar mutación nueva sin registro de inicio.
- [x] 1.5 Documentar esquema, ámbito setup/HU y recuperación local; validar ejemplos y comprobar que contienen eventos atribuibles sin conversación, stdout crudo ni secretos.

## 2. Actividad automática e informes

- [x] 2.1 Instrumentar ejecutores propios de setup/HU/validación con operation_id, inicio/resultado y duración monotónica; verificar éxito/fallo real del adaptador, rol/HU desconocidos nulos y consultas/previews que no inflan métricas.
- [x] 2.2 Instrumentar adaptadores de historia/PR y distribución con contexto explícito de cliente cuando corresponda, preservando journals previos; probar efectos con dobles, pending tras fallo de persistencia final y operaciones globales no atribuidas a todas las HU.
- [x] 2.3 Implementar activity status/report con filtros y apertura read-only; probar agregado deduplicado, duraciones incompletas, DB ausente sin creación, cobertura y hu.sqlite3 como autoridad del ciclo.
- [x] 2.4 Implementar import/export con destinos exclusivos y procedencia; probar import repetido, evento extranjero rechazado, scopes superpuestos, unidades/monedas incompatibles y export sin sobrescribir ni revelar secretos.
- [x] 2.5 Documentar consulta desde chat/CLI y significado de métricas; ejecutar ejemplos sobre la base de una HU sintética y verificar que tiempos/comandos no se etiquetan como consumo LLM.

## 3. Entrada conversacional y coordinación

- [x] 3.1 Implementar work preview/start/status como fachada de HU existente, con generación de contratos desde entradas tipadas y binding de 09; probar historia textual, decisiones faltantes, cliente no preparado y ausencia de JSON manual obligatorio.
- [x] 3.2 Actualizar harness-hu y bloque AGENTS para resolver runtime, comprobar capacidades y conducir aprobación/implementación/validación/revisión; verificar recursos instalados, formato de agentes vigente y plan con alcance positivo respetado.
- [x] 3.3 Integrar evidencia real de roles nativos y modo supervisado explícito cuando admisible; probar delegación ausente, modelos no disponibles y aislamiento fallido sin fabricar independencia ni sustituir perfiles silenciosamente.
- [ ] 3.4 Implementar work resume con lectura/reconciliación de estado y aprobación vigente; probar nuevo chat, drift de binding/política/candidato, pending y no duplicación de efectos, preservando límite de correcciones y escritor único.
- [x] 3.5 Documentar recorrido de HU y estados local/remoto/publicación; validar transcript de prueba que respeta preview sin mutaciones, gates stale/not_run y ausencia de PR/deploy implícitos.

## 4. Fuentes condicionales de consumo y hooks

- [x] 4.1 Persistir consumo importado soportado con fuente/asociación/unidades y fallback Desktop null/unavailable; probar fuente atribuible, fuente ausente, cuota global, estimación por texto y dato API que no se convierte en facturación Desktop.
- [x] 4.2 Añadir diagnóstico de capacidades del host contra eventos/payloads oficiales y empaquetar adaptador opt-in de hooks soportados; probar host incompatible, scripts ausentes, definición no confiada y cobertura parcial con actividad propia operativa.
- [x] 4.3 Integrar eventos de hooks autorizados con asociación explícita y deduplicación; probar tool event compatible, asociación ambigua/cliente extranjero rechazada y superposición con operación propia sin duplicar conteos.
- [x] 4.4 Documentar habilitación/confianza manual, fuentes admitidas y limitaciones de consumo; entregar matriz observable del host y verificar que ausencia de hooks/tokens cumple fallback documentado sin scraping de bases/transcripts internos.

## 5. Aceptación integral y límites preservados

- [x] 5.1 Ejecutar pruebas nuevas y suites relevantes de HU, observabilidad, setup/CLI/Desktop; entregar resultados y comprobar que no cambian estados/aprobaciones ni evidencia histórica de 06–08.
- [x] 5.2 Verificar smoke del wheel instalado: setup inicializa SQLite, HU registra actividad, interrupción/reanudación deduplica y report/export funcionan; comparar snapshots de preview y consultas sin escrituras.
- [ ] 5.3 Ejecutar protocolo real en segunda máquina con 09: instalar → invocar setup → preparar dos clientes → invocar HU local → interrumpir/reanudar desde otro chat → consultar actividad/cobertura; adjuntar evidencia real y marcar pasos no observados not_run/blocked.
- [x] 5.4 Ejecutar piloto NaturaPet seleccionado externamente con insumos sintéticos, rutas autorizadas y HU local acotada, sin deploy/merge ni escritura remota implícita; comprobar SQLite útil aunque tokens/costos sigan null y distinguir estado local de requisitos remotos pendientes.
- [x] 5.5 Consolidar evidencia de aceptación y limitaciones en documentación del producto, conservando las 144 evaluaciones y gates remotos/release pendientes; verificar que ninguna captura simulada, archivo de cambio o éxito local habilita certified/release/publicación.

## Evidencia y pendiente material

Ver `docs/evidence/conversational-activity-verification.md` y su registro JSON.
3.4 tiene implementación y pruebas de persistencia/reconciliación completas;
su invocación desde otro chat humano real permanece `not_run`.
5.3 permanece `not_run`: el usuario indicó que no dispone de segunda máquina,
autorizó avanzar con el piloto local seleccionado y reiteró sync/archive/push.
La reanudación comprobada en proceso nuevo no acredita otro chat real.
El archivo administrativo conserva estas dos tareas de aceptación incompletas y los gates pendientes.
