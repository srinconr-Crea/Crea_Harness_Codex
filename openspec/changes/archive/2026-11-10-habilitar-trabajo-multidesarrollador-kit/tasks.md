# Tasks

Las casillas completadas se sustentan en el expediente docs/hu/habilitar-trabajo-multidesarrollador-kit; los intentos fallidos se conservan como historia. Una casilla de implementaciÃ³n no acredita un piloto nativo. Los grupos son incrementos internos de un Ãºnico cambio y candidato, no cambios OpenSpec separados. Los paths de kit apuntan al staging 0.1.9 futuro. Cada grupo incorpora sus pruebas/documentaciÃ³n; Tester conserva ejecuciÃ³n y recibos independientes. No instalar herramientas, autenticar, publicar o acceder a servicios reales como efecto de completar estas tareas locales.

## 1. Principal y Planner: baseline y alcance congelado

- [x] 1.1 Confirmar rama/revisiÃ³n, estado previo y ausencia de colisiÃ³n de 0.1.9; verificar mediante registro de Git y lista explÃ­cita de archivos ajenos conservados, sin reset/stash o publicaciÃ³n.
- [x] 1.2 Capturar baseline por bytes de 0.1.3-0.1.8, ZIP/hashes/manifests y fuente personalizada real; verificar hashes antes de crear el staging y una prueba negativa que detecte una alteraciÃ³n sintÃ©tica.
- [x] 1.3 Preparar exclusivamente el staging nuevo 0.1.9 desde la fuente 0.1.8 verificada; verificar comparaciÃ³n de origen, preservaciÃ³n de personalizaciones y cero modificaciones a Ã¡rboles histÃ³ricos.
- [x] 1.4 Concretar criterios, rutas read/write/approved, reglas aplicables, snapshots y contratos Planner de esta HU; verificar handoff canÃ³nico sin IDs de agentes inventados ni resultados futuros de Tester.
- [x] 1.5 Definir catÃ¡logo/fixtures de validaciÃ³n de este incremento reutilizando el mecanismo existente; verificar que required_checks contiene IDs reales y no comandos duplicados, sin activar adaptadores inactivos.
- [x] 1.6 Registrar decisiones D1-D14 y orden 2â†’5â†’6â†’7, 3â†’4, 8â†’9 y 10â†’11; verificar que A/B/C y la migraciÃ³n usan un solo candidato y no autorizan merge/deploy o nuevas escrituras remotas.

## 2. Developer: origen y destino de entrega

- [x] 2.1 AÃ±adir pr_target_branch opcional y perfil de equipo al schema/config del staging; verificar tests de ausencia, null, sprintâ†’quality, valores invÃ¡lidos y fallback legacy sin nuevas exigencias retroactivas.
- [x] 2.2 Implementar resoluciÃ³n comÃºn en entrega.py de repo/remoto/refs/SHA; verificar fixtures de remoto incorrecto, nombres ambiguos, espacios, ramas con slash y refspec que no actualiza tracking ref.
- [x] 2.3 Incorporar comprobaciÃ³n de base/destino/protegidas y reservas quality/test del perfil de equipo antes de escritura/publicaciÃ³n; verificar rechazo de rama actual o ref de push distintas de la feature aprobada sin modificar el checkout.
- [x] 2.4 AÃ±adir procedencia opcional scope.git_delivery conservando B y V; verificar schema, reanudaciÃ³n de HU propia, colisiÃ³n de rama ajena y rechazo de base no ancestral sin sustituirla por quality.
- [x] 2.5 Mostrar alcance heredado y efectivo hacia destino; verificar fixture donde sprint incluye commits ajenos ausentes de quality y el verificador no los atribuye a la HU ni amplÃ­a publication_paths.
- [x] 2.6 Contrastar destino efectivo con evidence.delivery y autorizaciÃ³n/digest en transiciones; verificar cambio de destino posterior a aprobaciÃ³n, permiso solo archive, solo push y permiso completo vigente sin confirmaciones repetidas.
- [x] 2.7 Adaptar orquestador, AGENTS, entrega-git y plantilla PR; verificar recorrido documentado desde base a feature y PR quality conservando GitHub manual, Azure Services CLI y Server manual.
- [x] 2.8 AÃ±adir regresiones de Ã­ndice completo, todos los commits publicables y SHA remoto, preservando verify_commit; verificar mediante dobles/fixtures que no hay force-push, merge, borrado automÃ¡tico o comandos de proveedor adicionales.

## 3. Developer: entorno personal y plan/run/gate

- [x] 3.1 AÃ±adir entorno-local.schema.json y resolver entorno_local.py con allowlist Python/perfil; verificar rechazo de secretos, claves desconocidas, rutas relativas de ejecutable, enlaces/junctions y overrides de polÃ­tica/ramas/modelos.
- [x] 3.2 AÃ±adir execution.local_environment_path opcional y exclusividad con python_executable; verificar legacy absoluto, binding ausente, ambas fuentes activas y plantilla sin setup sin instalaciones implÃ­citas.
- [x] 3.3 Integrar resoluciÃ³n Ãºnica en load/make_plan/resolved_settings/current/run/gate y attempts; verificar que reconstruir el mismo plan produce idÃ©ntica configuraciÃ³n efectiva, digest fuente y resoluciÃ³n.
- [x] 3.4 Mantener fingerprint de intÃ©rprete/ubicaciÃ³n/paquetes y consumo de campos pertinentes; verificar invalidaciÃ³n tras cambio efectivo de Python/dependencias y ausencia de invalidaciÃ³n por alias remoto no consumido en pruebas Python locales.
- [x] 3.5 AÃ±adir fixtures de dos mÃ¡quinas/rutas con la misma policy/execution versionadas; verificar plan/run/gate propios y rechazo de recibos trasplantados entre entornos o planes, sin editar configuraciÃ³n compartida.
- [x] 3.6 Integrar validaciÃ³n estructural y consumidores CLI/helpers con identificaciÃ³n offline de versiÃ³n/contratos; verificar que opciÃ³n nueva no se declara soportada solo por schema permisivo y que configuraciÃ³n ausente/desactivada conserva la vÃ­a legacy.
- [x] 3.7 Documentar resoluciÃ³n, revisiÃ³n del entorno, lÃ­mites histÃ³ricos y rollback; verificar ejemplos de Windows con intÃ©rprete explÃ­cito sin Activate o cambio de ExecutionPolicy y sin catÃ¡logo duplicado.

## 4. Developer: preparaciÃ³n C del desarrollador

- [x] 4.1 Crear skill crea-preparar-desarrollador, registro, guÃ­a local y entrada en AGENTS; verificar descubrimiento/referencias en un clon que no contiene el prompt de distribuciÃ³n.
- [x] 4.2 Implementar diagnÃ³stico offline de raÃ­z/revisiÃ³n/remoto/setup/catÃ¡logo/OpenSpec/recursos/herramientas; verificar estados ready/partial/blocked y dependencia ausente con salida estructurada en vez de instalaciÃ³n o traceback no manejado.
- [x] 4.3 Implementar operaciÃ³n bind limitada y exportaciÃ³n exclusiva de diagnÃ³stico; verificar diff explÃ­cito, binding equivalente sin cambio de bytes, rechazo de colisiones/enlaces/escapes y sanitizaciÃ³n de resultados.
- [x] 4.4 AÃ±adir comprobaciÃ³n online explÃ­cita mediante operaciones de lectura permitidas y destino concreto; verificar con dobles acceso correcto/denegado/red/no realizado y que lectura no se informa como permiso de push/PR.
- [x] 4.5 Documentar instalaciones por alcance y autenticaciÃ³n personal/MFA/confianza; verificar que faltantes sin autorizaciÃ³n quedan pendientes y no hay login, cambios globales o instalaciÃ³n automÃ¡tica desde inspect.
- [x] 4.6 Preservar OpenSpec/skills/modelos/perfiles/reglas/catÃ¡logo/configuraciÃ³n; verificar hashes de esos archivos antes/despuÃ©s de dos ejecuciones C y de fallos de preparaciÃ³n.
- [x] 4.7 Conservar integraciÃ³n Azure y Databricks por aplicabilidad y perfil elegido; verificar con dobles que C no lee Boards sin HU, consulta pipelines, crea PR, ejecuta jobs o activa hooks/runtime/MCP.
- [x] 4.8 Documentar y probar rutas con espacios, wrappers cmd e intÃ©rpretes explÃ­citos; verificar funcionamiento sin Activate, cambio de ExecutionPolicy ni reutilizaciÃ³n de credenciales de otra persona.

## 5. Developer: snapshots y simulaciÃ³n Git aislada

- [x] 5.1 Definir schema de snapshot, versionado y rutas exactas por HU/intento; verificar representaciÃ³n de SHA/null, fecha, versiÃ³n, cobertura y resultados verified/missing/access_denied/connection_error/unverified.
- [x] 5.2 Implementar adquisiciÃ³n explÃ­cita del destino por principal en entrega.py; verificar mediante remotos locales y dobles refs exactas, fetch auxiliar acotado y contraste con respuesta remota, sin actualizar ramas de trabajo.
- [x] 5.3 Distinguir rama ausente de fallo/ambigÃ¼edad/cachÃ©; verificar F en sus variantes y cambio durante adquisiciÃ³n sin fallback a otra rama, login, instalaciÃ³n o reintentos automÃ¡ticos indefinidos.
- [x] 5.4 Implementar simulate con almacenamiento temporal aislado y ayuda explÃ­cita; verificar que refs/index/worktree usuario conservan bytes, no se ejecutan drivers/cÃ³digo no revisados y no hay merge/rebase como fallback.
- [x] 5.5 AÃ±adir fixtures de conflictos modify/delete/rename, historias mÃºltiples/shallow/no relacionadas y capacidad Git ausente; verificar resultado textual y lÃ­mites sin forzar ancestros o permitir unrelated histories.
- [x] 5.6 Documentar separaciÃ³n snapshot/inspect/simulate y propiedad de temporales; verificar guardas de rutas absolutas, enlaces/junctions, exportaciÃ³n exclusiva y ausencia de artefactos temporales en el alcance de publicaciÃ³n.

## 6. Developer: impacto, semÃ¡ntica e informe de compatibilidad

- [x] 6.1 Implementar delivery.compatibility opt-in deshabilitado en plantilla, inspector puro y schema de informe con B/V/H/Q, outcome/coverage/freshness y dimensiones; verificar ausencia/desactivaciÃ³n legacy, stdout sin escritura/red/suites y errores estructurados sin fabricar compatible.
- [x] 6.2 Reutilizar inventario Git para separar HU/destino/herencia y ambas rutas de renombres/bajas; verificar fixtures con HEAD/index/worktree/untracked y rechazo de usar Q divergente como base de collect.
- [x] 6.3 AÃ±adir recorrido inverso de consumidores sobre el mapa existente; verificar ciclos, orden estable, motivos/direcciÃ³n, relaciones cambiadas entre revisiones y preservaciÃ³n de components_for legacy.
- [x] 6.4 Vincular specs/reglas/documentos pertinentes y revisiÃ³n semÃ¡ntica referenciada; verificar casos C/D, mismo archivo sin contradicciÃ³n y conflicto conocido con cobertura parcial, sin inferir significado de un hash.
- [x] 6.5 Proponer checks por inputs/criterios/consumidores del catÃ¡logo Ãºnico; verificar caso B, check desconocido, prueba sin archivo modificado y required runtime inactivo sin materializar suites o modificar policy.
- [x] 6.6 Completar fixtures A y ausencia de mapa: verificar independencia sustentada sin bloqueo por divergencia y cobertura limitada honesta sin activar context_management o suponer independencia por desconocimiento.
- [x] 6.7 Aplicar lÃ­mites y exclusiones a ambas revisiones; verificar que no se lee historia ajena o secretos y que rutas excluidas permanecen visibles al control Git, con diagnÃ³stico parcial ante budget o fuente ausente.
- [x] 6.8 Documentar outcome/cobertura/vigencia, escenarios A-F y acciones al equipo; verificar recomendaciones concretas y que ninguna prueba sobre H se presenta como ejecuciÃ³n del Ã¡rbol combinado.

## 7. Developer: handoffs, equivalencia y vigencia de entrega

- [x] 7.1 AÃ±adir evidence.compatibility opcional y validaciÃ³n de referencias/anclas/hashes; verificar preservaciÃ³n de informes previos, intento nuevo y rechazo de informe alterado, prestado de otra HU o candidato.
- [x] 7.2 Implementar content-v3 opt-in para planes nuevos con regla exacta de derivados observacionales; verificar que content-v2/planes legacy mantienen semÃ¡ntica y no adoptan automÃ¡ticamente la nueva proyecciÃ³n.
- [x] 7.3 Mantener equivalencia de contenido probado/publicado y entradas Git consumidas; verificar informe previsto sin invalidaciÃ³n tÃ©cnica, publicaciÃ³n de bytes distintos rechazada y cambio funcional escondido en informe detectado.
- [x] 7.4 Separar observaciÃ³n derivada de nueva obligaciÃ³n funcional; verificar que agregar un requisito/check aceptado reconcilia el plan y no se esconde en metadata ni usa recibos entre planes.
- [x] 7.5 Consumir compatibilidad en transiciones, con TARGET_COMPATIBILITY_CURRENT inicialmente sin promociÃ³n; verificar cÃ³digos/modos 0/2/3/4 y que aviso/error no crea veto global o passed y gates previos siguen vigentes.
- [x] 7.6 Integrar refresco final por principal antes de PR/formulario; verificar E con Q1â†’Q2 independiente, dependiente, force-update y cambio posterior a creaciÃ³n, sin prometer atomicidad o seguimiento continuo.
- [x] 7.7 Preservar autorizaciones y max_fix_rounds cuando no cambian entradas/acciones/paquete; verificar reanudaciÃ³n tras decisiÃ³n humana y nuevo candidato manual con V ancestral explÃ­cita, sin resetear rondas o relajar verify_commit.
- [x] 7.8 Actualizar orquestador, perfiles pertinentes y guÃ­as de handoff/transiciones; verificar un escritor por checkout, ausencia de subdelegaciÃ³n y ausencia de coordinador/lock global entre desarrolladores.

## 8. Developer: composiciÃ³n de cliente y exclusiones

- [x] 8.1 Crear kit-composition.json/schema con grupos cliente/distribuciÃ³n/local y motivos; verificar cobertura de cada entrada empaquetada, dependencia cerrada y rechazo de grupos/rutas ambiguos.
- [x] 8.2 Adaptar copia A y validaciÃ³n cliente para prescindir del prompt/LEEME; verificar clon sintÃ©tico con AGENTS, entrada C, schemas, recursos, licencias y referencias locales completas sin depender de harness_local.
- [x] 8.3 Conservar manifest como procedencia, VALIDACION Ãºtil y tests/crea separado; verificar original solo en paquete intacto, personalizado sin original y no inclusiÃ³n automÃ¡tica de tests internos en catÃ¡logo de negocio.
- [x] 8.4 Incorporar y combinar .gitignore/exclusiones de contexto desde A; verificar git check-ignore para binding/diagnÃ³stico/temporales y no exclusiÃ³n de AGENTS, skills, perfiles, schemas, specs, catÃ¡logo o evidencia obligatoria.
- [x] 8.5 Verificar diferencias entre copia/contexto/ignore/publicaciÃ³n con un fixture rastreado y untracked; demostrar que .gitignore no retira lo rastreado, el contexto no oculta cambios y git add usa solo rutas aprobadas.
- [x] 8.6 Documentar migraciÃ³n B por archivo ya rastreado, consumidores e inventario; verificar que no se elimina prompt/tests/evidencia ni se ejecuta git rm por adoptar nuevas exclusiones.

## 9. Developer: documentaciÃ³n vigente y distribuciÃ³n nueva

- [x] 9.1 Crear fe de erratas 0.1.8 en el mantenedor y corregir encabezados del staging nuevo; verificar que LEEME/configuraciÃ³n/VALIDACION/pruebas distinguen versiÃ³n vigente, introducciÃ³n y evidencia histÃ³rica sin alterar 0.1.8.
- [x] 9.2 Reescribir B para origen detectadoâ†’0.1.9 y aÃ±adir C independiente; verificar comparaciÃ³n de tres vÃ­as con baseline ausente, campos de A preservados y prohibiciÃ³n de repetir setup o modificar modelos desde C.
- [x] 9.3 Alinear README, inventario, extensiones, catÃ¡logo de skills, guÃ­as de adopciÃ³n/reversiÃ³n y contenido PR; verificar enlaces, ausencia de referencias operativas obsoletas y conservaciÃ³n de source_version/upstream/cifras histÃ³ricas correctas.
- [x] 9.4 Implementar empaquetador 019 dirigido al staging nuevo, baseline, manifest y equivalencia ZIP/Ã¡rbol; verificar rechazo de targets histÃ³ricos, links, archivos locales y salidas fuera de alcance sin ejecutar empaquetadores antiguos.
- [x] 9.5 AÃ±adir pruebas de distribuciÃ³n y adopciÃ³n 019; verificar cliente nuevo, cliente 0.1.8 con opcionales ausentes/activos, preservaciÃ³n de personalizaciones y rollback conjunto sin reescribir HU/recibos.

## 10. Principal y Tester: ejecuciÃ³n final y evidencia independiente

- [x] 10.1 Principal reconciliar Git completo, criterios, inventario, alcance y catÃ¡logo finales antes de Tester; verificar plan canÃ³nico con outputs nuevos y sin cambios funcionales ocultos como evidencia.
- [x] 10.2 Tester ejecutar la selecciÃ³n de entrega/entorno/preparaciÃ³n con herramientas ya autorizadas; verificar recibos primarios, IDs reales, assertions, ambiente, huellas y ausencia de cambios a producciÃ³n durante su fase.
- [x] 10.3 Tester ejecutar casos A-F y variantes Git/semÃ¡nticas/configuraciÃ³n con fixtures locales y dobles; verificar esperado por caso en resultados y diferenciar simulaciÃ³n de piloto real.
- [x] 10.4 Tester ejecutar regresiones pertinentes de test_contract, test_transiciones, test_content_v2, test_contexto/adoption, test_testing_adapters/lifecycle y test_kit_validation del candidato; verificar bloqueos previos, TTL, inclusiÃ³n real y no adopciÃ³n cruzada.
- [x] 10.5 Tester verificar ausencia de efectos de inspect/plan/gate y preparaciÃ³n repetida, ademÃ¡s de lÃ­mites de snapshot/simulate explÃ­citos; registrar procesos/archivos/red observados sin afirmar aislamiento tÃ©cnico por instrucciones solamente.
- [x] 10.6 Tester validar original, composiciÃ³n instalada y personalizaciÃ³n con contexto/lifecycle presentes y ausentes; verificar schemas/JSON/TOML/referencias e inventario de tests sin ejecutar suites cliente desde validaciÃ³n estructural.
- [x] 10.7 Tester ejecutar controles de integridad Ã¡rbol/ZIP y preservaciÃ³n de baseline 0.1.3-0.1.8; verificar hashes/manifests y distinguir checks de empaquetado de resultados funcionales.
- [x] 10.8 Tester conservar intentos y handoff ready_for_review o diagnÃ³stico real; verificar recibos completos, limitaciones/not_run de piloto nativo/hooks/remoto y contador global de correcciones sin reescribir resultados.

## 11. Reviewer y Principal: revisiÃ³n transversal y preparaciÃ³n de cierre

- [x] 11.1 Reviewer revisar independientemente cÃ³digo, contratos y casos A-F contra esta propuesta; verificar matriz de cobertura completa y gates vigentes sin relanzar suites salvo invalidaciÃ³n o regla justificada enviada a Tester.
- [x] 11.2 Reviewer ejecutar Verify de OpenSpec y contrastar specs/cÃ³digo/docs, compatibilidad legacy, licencias/upstream y lÃ­mites Azure/Databricks; verificar resultados y registrar hallazgos sin editar contratos para aprobar.
- [x] 11.3 Reviewer preparar Sync solo tras revisiÃ³n/pruebas favorables y presentar su diff; verificar que cambios funcionales/documentales seleccionados reconcilian el plan y que el mapa de Archive futuro es exacto, sin ejecutar Archive todavÃ­a.
- [x] 11.4 Principal presentar alcance final, candidato, evidencia, pendientes y decisiones de cierre aplicables; verificar que no se declara release/piloto/PR creado ni se ejecuta commit/push/PR por el mero fin de implementaciÃ³n.

## Workflow follow-up

- Una nueva peticiÃ³n humana de Apply inicia implementaciÃ³n; Propose termina con estos artefactos y su validaciÃ³n de planificaciÃ³n.
- Tras implementaciÃ³n y revisiÃ³n favorables, solicitar o consumir la aprobaciÃ³n humana concreta de Archive y del alcance de publicaciÃ³n. Archive conserva el expediente; no es una casilla de implementaciÃ³n que se pueda cumplir antes del cierre.
- Commit/push y PR requieren sus autorizaciones vigentes y controles de entrega. Azure Services conserva CLI aprobada y verificaciÃ³n posterior; GitHub/Server conservan formulario manual. No activar auto-complete, merge, deploy o promociÃ³n a test.
- IntegraciÃ³n en quality, revisiÃ³n humana y paso a test permanecen en el proceso del equipo. Una prueba real con dos desarrolladores, si se solicita, tendrÃ¡ autorizaciÃ³n/evidencia propia y no se deduce de los fixtures locales.
