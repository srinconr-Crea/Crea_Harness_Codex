# Verify: habilitar-trabajo-multidesarrollador-kit

Resultado: **implementación verificada con advertencias y límites explícitos; preparada para Sync y Archive solicitados**. El gate final corresponde al candidato portable 0.1.9 congelado, no certifica el producto histórico, un repo de negocio o servicios remotos.

| Dimensión | Resultado |
| --- | --- |
| Completitud | 74 tareas registradas y contrastadas; 47 requisitos del delta con superficie de implementación; 90 escenarios revisados en coverage-map.json/coverage.md |
| Corrección | 242 casos JUnit coherentes (200 pruebas y42subcasos),0fallos/0omitidos,8criterios passed;9 pruebas suplementarias/3subcasos y3 de distribución. Módulos de regresión asociados a los47requisitos presentes en el JUnit final. La matriz distingue procedimientos revisados de ejecución real |
| Coherencia | D1-D14 contrastadas: candidato único, B/V/H/Q, roles secuenciales por checkout, opt-in informativo, catálogo único, entorno consistente, C persistente y composición explícita; no motor LLM/coordinador central |
| Integridad | 492 archivos ZIP↔árbol byte-idénticos;2176 archivos históricos preservados;0eliminaciones del kit heredado;27archivos añadidos/32modificados solo en staging019;4modelos/esfuerzos de perfiles conservados |

No hay hallazgos críticos abiertos del cambio. Los cinco hallazgos materiales de la revisión independiente se cerraron con pruebas rojas/verdes, sin modificar specs para aprobarlos. Se cerraron además lectura de contratos actuales, resolución de revisión de dependencias, check desconocido, categorías de conexión, anclas del diagnóstico y selector de historia pertinente. Evidencias: review-independent.md, green-diagnostic-anchors.xml, green-supplemental-final.xml y recibos finales. No se repitieron suites para «obtener verde»: los intentos posteriores obedecen a invalidación de fuente o del emisor del recibo y conservan los anteriores.

## Advertencias

- Batería general del mantenedor:742passed,1failed,7skipped,9subtests. Fallo preexistente reproducido en test_documented_fixtures_validate: binding declara hash del blob LF y checkout Windows contiene CRLF. Tests y fixtures intactos; maintainer-baseline-failure.json demuestra ambas representaciones. No se declara verde esa batería ni se altera otro contrato para ocultarla.
- Emisor pytest del mantenedor asigna ID a cada subcaso antes del XML para conservar contadores coherentes con pytest9.1.1. No reescribe recibos ni relaja reports.junit. Un padre no agrega automáticamente resultados de sus subcasos: CA05/CA08 incluyen IDs explícitos; exit0 y failed0 siguen obligatorios. Probe negativo conserva un fallo real.
- El auxiliar ejecutó intento4 favorable; límite de créditos interrumpió su informe. Principal completó intento5 directamente, con plan y herramientas revisados. No se atribuye ejecución/revisión independiente5 inexistente. La revisión independiente de código y su informe sí se conservan.

## Límites no acreditados

Piloto nativo de roles/hooks, autenticación/MFA real, dos personas reales, Azure/Databricks/Spark/runtime y efectos remotos: **not_run/no verificados**, fuera de la certificación local. Los flujos humanos se comprobaron por instrucciones y guardas/dobles; no se presentan como acciones efectuadas. Las pruebas de H y simulación textual no acreditan un árbol combinado ejecutado. El handoff de pruebas es posterior al proceso y no certifica intervalos nativos de rol.

El gate técnico declara allows_archive=false y allows_deploy=false: acredita pruebas, no autoridad de cierre. Sync/Archive los autoriza expresamente la petición humana del chat. Commit/push/PR, merge a quality y promoción a test conservan el proceso del equipo y no se ejecutaron.

## Sync y cierre previstos

Diff revisable en sync-preview.diff y sync-plan.json, obtenido solo de artifactPaths.specs.existingOutputPaths. Dos specs nuevas y cinco ampliadas:45requisitos añadidos,2modificados y42requisitos previos no mencionados preservados. Rules snapshot actual de OpenSpec leído una vez; requisitos observables SHALL/WHEN/THEN, rechazos y dry-run cubiertos. Se exige comparación posterior completa y validación antes de mover el expediente.

Rulings conservados en progress.md: staging nuevo sin worktree para preservar contexto local (no afirma aislamiento entre sesiones); SHA heredados aprobados explícitos; fixture en ruta corta por MAX_PATH (no piloto nativo); warning CRLF externo conservado (batería general no verde). No hay menores diferidos de la revisión independiente.

## Verificación posterior de Sync

7/7 specs del cambio pasan strict. Las31 specs del repositorio pasan validación normal. Strict global devuelve27passed/4advertencias heredadas por requisitos>500caracteres en desktop-integration, onboarding-preview, onboarding-recovery y role-tool-catalog; archivos intactos respecto a HEAD. Se mantienen fuera del cambio. Comparación semántica posterior:47bloques del delta coinciden,42requisitos no mencionados preservados y cero operaciones pendientes. Ver sync-comparison.json.
