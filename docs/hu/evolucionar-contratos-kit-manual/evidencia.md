# Evidencia de implementación — kit manual 0.1.5

HU/cambio: evolucionar-contratos-kit-manual. Fecha: 2026-10-26.
Repositorio de desarrollo: la raíz no se convirtió en un proyecto consumidor ni se creó
un docs/proyecto.json ficticio. El contrato distribuible vive en el staging versionado.

## Resultado y candidato

Implementación local verificada de las cuatro capacidades propuestas; 31 tareas cerradas
al completar revisión, Sync y presentación. Código y pruebas ejecutados desde la sesión
principal; revisión independiente real por /root/revision_implementacion_015. No se afirma
la ejecución de planner/developer/tester/reviewer nativos por existir sus perfiles.

Candidato: [ZIP 0.1.5](../../../artifacts/crea-manual-kit-0.1.5.zip).
SHA-256: `d9fcf8c4866a4287ae8cd233b920ee0a48ff13359c55874b371071c900493492`. Fuente mantenida:
`artifacts/crea-manual-kit-0.1.5/`. Distribuciones 0.1.3 y 0.1.4 preservadas:
504 archivos contrastados antes/después, cero cambios; 497
entradas de manifests y 182 archivos upstream/licencias verificados.
Ver [paquete](paquete.json) y [verificación estructurada](verificacion.json).

## Evidencia y verificación

- Kit: [97 pruebas passed](pruebas/kit-final.log), con Git/procesos pytest/JUnit reales en fixtures.
- Empaquetador: [3 pruebas passed](pruebas/empaquetador.log); guardas de destino, preservación y ZIP alterado.
- Estructura/original: passed, 4 perfiles, 25 skills, 11 schemas, 6 instancias y manifest íntegro.
- Neutralidad textual: cero hallazgos sin resolver; ejemplos/fuentes públicas revisados mediante claves
  ligadas a categoría/ruta/línea y hash completo. Inputs sensibles quedan externos al kit.
- Revisión: [6 Important corregidos](revision.json), 0 Critical y 0 Minor; regresiones RED→GREEN.
  [Mapa de las cuatro capacidades](mapa-verificacion.json).
- Sync: [4 especificaciones nuevas](sync.json), 21 requisitos y 58 escenarios. Validación general:
  25 passed, 0 failed; cuatro advertencias de longitud en specs históricas sin modificar.
  Las cuatro nuevas pasan validación estricta, al igual que el cambio.

El núcleo de identidad/proyección se verificó antes de integrar roles. Gate/transiciones
no ejecutan suites; corregir solo una referencia a recibo válido conserva plan y gate.
El candidato técnico, el intervalo de cada rol y el expediente publicado se comprueban
por separado, sin atribuir autoría que Git no demuestra.

## Pruebas históricas adicionales

El barrido global adicional se interrumpió tras registrar tres fallos; no se declara una suite
global verde. [Reproducción focalizada](pruebas/historico-fallos.log): 3 failed en 9.61s,
en fixtures documentadas, clonación y control positivo de filtro Git. Se conservó también
el [avance parcial](pruebas/historico-parcial.log). No se cambiaron esos módulos/fixtures del
motor histórico para hacerlos pasar ni se trasladaron sus capacidades o certificados al kit.
Estos fallos están fuera del alcance funcional de esta entrega manual y quedan pendientes.

## Objetos y entrega

Objeto `manual-kit-015`, tipo distribución/configuración/documentación, operación nueva
entrega desde 0.1.4; capas/capacidades de datos no aplican. Implementación: código,
schemas, perfiles, plantillas y ZIP acreditados por manifest y pruebas. Despliegue/publicación
remotos: no realizados. Verificación: código/configuración/paquete locales; no objeto desplegado.
Criterios y reglas: requisitos de las cuatro specs y prácticas Crea preservadas/adaptadas.
No se convierte este inventario en linaje de datos ni duplica los requisitos.

## Decisiones de implementación y límites

- Staging 0.1.5 separado dentro de la rama de pruebas actual, sin crear worktree ni modificar
  una rama principal. Coste del enfoque: los cambios locales deben revisarse explícitamente.
- HEAD/rama/índice funcionales declarados por check; otros estados son no soportados por
  la equivalencia. No se supone independencia por omitir la declaración.
- `publication_paths` finales separadas del alcance funcional: metadatos previstos no fuerzan
  otra identidad, pero cada byte publicado y commit del rango se contrasta. Una lista final
  incorrecta impide entrega, no amplía permisos nativos.
- `task_checkboxes` solo mediante transformación declarada y casillas numeradas: mantiene
  texto funcional. Si un check consume ese estado, la equivalencia se rechaza.
- Constituciones de capa necesitan decisiones reales y están inactivas de fábrica. Modo
  informativo inicial; promoción de condiciones exige decisión/configuración expresa.
- GitHub conserva PR manual y contenido preparado; pruebas locales no certifican proveedores,
  agentes nativos ni Spark/Databricks. Pilotos reales siguen not_run cuando no se ejecutaron.

## Autorización y cierre

La persona solicitó explícitamente Apply → Sync → Archive para este cambio en la conversación.
Esa autorización cubre el archivo local del incremento implementado y verificado. No autoriza
commit/push/PR; no se realizó merge, deploy, instalación global o modificación remota.
La decisión del responsable sobre reglas particulares, excepciones y condiciones a promover
se toma al adoptar el kit en cada proyecto; no se inventó para cerrar esta entrega genérica.

Expediente archivado y contrastado byte a byte (8 archivos; 31/31 tareas):
`openspec/changes/archive/2026-10-26-evolucionar-contratos-kit-manual/`.
El archivo administrativo no acredita despliegue ni certificación nativa. Siguiente paso:
revisión del candidato/adopción explícita por proyecto, sin publicación automática.

## Autorización posterior de publicación Git

Después del cierre local, la persona solicitó expresamente crear la rama
`Crea_Harness_Codex_MVP_Cons` y hacer push. Esa nueva solicitud autoriza commit y push del
incremento presentado a origin, repositorio srinconr-Crea/Crea_Harness_Codex. No incluye PR,
merge ni despliegue. Los campos de entrega anteriores describen el instante previo a esta
publicación. SHA de commit, resultado de push y verificación remota se entregan en la respuesta
final para evitar insertar un commit en su propio contenido.

Se conserva la convención .gitattributes de versiones anteriores para los bytes del kit 0.1.5
y los logs de esta HU. El staging usa exclusivamente paths del incremento y del manifiesto;
no se publican scratch, inputs externos de auditoría ni estado local de pruebas.
