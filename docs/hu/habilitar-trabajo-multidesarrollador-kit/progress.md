Plan: openspec/changes/habilitar-trabajo-multidesarrollador-kit/tasks.md

Fecha: 2026-11-10. Apply autorizado por el usuario; Verify, Sync y Archive solicitados. Sin autorización de publicación Git.

Ruling: trabajar sobre staging nuevo 0.1.9 en este checkout y conservar .git y archivos previos; el plan exige ese staging y contiene artefactos locales sin seguimiento que otro checkout no incluiría. No se crea una worktree ni se declara aislamiento entre sesiones.

Entorno existente: ../.integration-venv/Scripts/python.exe, Python 3.13 con PyYAML/jsonschema/pytest disponibles; no instalaciones.

Baseline: validar-kit 0.1.8 --original passed; 464 archivos originales.

Task 1.1: complete — rama/revisión/estado registrados en baseline.json.
Task 1.2: complete — hashes históricos capturados y recontrastados.
Task 1.3: complete — 465 archivos copiados exclusivamente desde manifest intacto, sin estado local.

Checkpoint implementación: creados entrega.py, entorno_local.py, preparar-desarrollador.py, compatibilidad.py, team_common.py y composicion.py en staging 0.1.9; schemas opcionales y content-v3 integrados con workflow/transiciones. Documentación y entrada C actualizadas; A/B/C independientes, composición cliente conserva recursos y omite prompt/LEEME.

Evidencia hasta ahora (JUnit externos en este expediente): baseline-tests.xml 66 passed; green-delivery-environment-corrected.xml 8 passed/7 subtests; green-preparation-both-environments.xml 5 passed; green-compatibility-local-git.xml 7 passed/2 subtests (A-F y transporte Git local); green-content-v3.xml 20 passed (incluye v2); green-team-transitions.xml 2 passed; green-composition.xml 3 passed; green-package019.xml 3 passed. Los XML red y green iniciales fallidos se conservan como historia, no se usan como prueba final.

Skills de creación: subagente /root/prep_skill_baseline confirmó ausencia de entrada C en 0.1.8 y descubrimiento correcto de AGENTS→skill→guía en 0.1.9 sin prompt. Prueba de instrucciones, no piloto nativo. Sus observaciones editoriales se atenderán en guía.

Ruling: se añade approved_inherited_commits opcional dentro de scope.git_delivery para fijar los SHA heredados aceptados expresamente; participa en contexto/digest. Evita interpretar texto libre como autorización de alcance ajeno. Sin nuevo permiso o publicación.

Pendientes inmediatos: corregir red-config-edge-cases (fallback solo null/ausente; formas Azure y remotos con slash; diagnosticar personal rastreado), pruebas adicionales de plan/run/gate v3 y entorno por intentos; persistir handoff/plan de validación; esperar full-kit-initial (session 7283) y full-maintainer-initial (session 93863). No asumir esas baterías pasadas. No Archive/Sync aún.


Checkpoint final de Developer: grupos 1–9 implementados y verificados mediante fixtures/código/docs; tasks actualizados. Plan canónico de validación preparado con ID 89182ef399a18d4a37eaffa316a9128f4b03c073018939b03cb2f3652b184666, fuente exacta 492 archivos en fixture-019.json. Tester independiente /root/tester_final ejecuta plan/run/gate (su sesión35569); no asumir resultado.

Review fresco /root/final_review detectó cinco hallazgos materiales; correcciones y pruebas rojas/verdes documentadas en review-independent.md. Green finales afectados: green-candidate-contract.xml 8 passed/2subtests; green-integration-v3-binding.xml 9 passed; green-simulation-offline-guards.xml 13passed/5subtests; green-semantic-bounds-render.xml 3passed; green-unknown-check-bounds.xml 4passed; green-team-boundaries.xml 6passed/6subtests; supplemental-edges.xml 5passed; two-checkout-bindings.xml 1passed. No se suman como tests únicos.

full-maintainer-initial.xml: 742passed, 1failed, 7skipped, 9subtests. Fallo tests/test_configuration.py::test_documented_fixtures_validate reproducido intacto, hashes declarados=blobs LF; checkout CRLF. Evidence maintainer-baseline-failure.json y reproduced-unchanged-maintainer-fixtures.xml. Advertencia heredada, fuera del kit nuevo; no editar fixtures ni contratos para ocultarla.

Ruling: usar fixture de validación en ../.test-data/v019-* para evitar MAX_PATH de Windows y no consumir repositorios anidados ajenos preservados. Los recibos identifican esa raíz, no la del mantenedor — evita atribución falsa de un gate al Git principal — coste: piloto nativo real sigue sin acreditar.

Ruling: mantener el fallo heredado CRLF documentado en vez de ampliar el cambio a fixtures de otra herramienta. Sus archivos y el test están intactos; candidato nuevo se verifica por separado — coste: no puede declararse verde la batería general del mantenedor.


Checkpoint 2026-11-10: cierre real en curso. Intento1: pytest198+37subtests pasados, gateblocked por JUNIT_COUNTER_MISMATCH, recibos intactos. Emisor local revisado scripts/pytest019_subcases.py produce IDs de subcaso antes de XML; probe negativo conserva6casos y1fallo, parser productivo sin cambios. Intentos2/3 preparados pero not_run supersedidos, sin sobreescritura. Corrección1: estados de lectura, anclas diagnósticas, emisor de validación. Corrección2: lectura de contratos OpenSpec limitada a specs de HU actual; historia ajena queda visible en Git pero no se carga.

Intento4 ejecutado por /root/tester_final: gatepassed,242casos, CA01-CA08passed; anterior a última corrección del selector. Su agente se interrumpió por créditos antes de redactar informe4/iniciar5. No se reintenta el agente. Principal ejecuta proceso final autorizado directamente como rol Tester con limitación declarada; no se inventa revisión independiente5. Intento5 sesión62520 en ejecución, ID88de0660db071f4eb95f6002bb12c57b84cd595581ad65e4823f8d50dd2c3a27. Candidato492archivos con hashZIP4f8eb72d26367f074f98113267a04a4509c9298cc0f570d89cfc68995e19b00c. Final-integrity.json prueba equivalenciaZIPárbol, baseline2176 y modelos4perfiles conservados. Final-distribution.xml3passed. Green-diagnostic-anchors.xml20passed/7subtests; green-supplemental-final.xml9passed/3subtests.

Matriz durable coverage-map.json/coverage.md:47requisitos/90escenarios, diferencia fixtures/contratos/procedimientos y no piloto. Mantener warning CRLF externo intacto. Pending: finalizar62520, inspeccionar recibos y crear handoffs Tester/Reviewer de cierre; Verify completo, Sync inteligente7specs, validación y Archive solicitado (sin commit/push). No declarar completado ni archivar antes de gatefinal favorable.


COMPLETE: intento5 gatepassed242casos (200pruebas+42subcasos),8criterios,fuente492/492intacta,recibos8/8íntegros.74/74tareas. Verify report y matriz47/90 completos con límites. Sync7specs verificado47bloques/42previospreservados;7strictpass,31normalpass,4warningsstrictajenosintactos. Archive solicitado completado en openspec/changes/archive/2026-11-10-habilitar-trabajo-multidesarrollador-kit;12archivos/metadata/tareas preservados porhash. ZIP final4f8eb72d26367f074f98113267a04a4509c9298cc0f570d89cfc68995e19b00c;baseline2176preservado. HEADc89sin cambios;sin commit/push/PR ni certificaciónnativa/remota.
