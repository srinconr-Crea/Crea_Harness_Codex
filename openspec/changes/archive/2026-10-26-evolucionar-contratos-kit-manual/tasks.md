# Tasks

Todas las tareas están pendientes y describen una futura implementación. Esta propuesta no autoriza Apply, ejecutar el plan, instalar herramientas o publicar. K0/K1 y los contratos están definidos en `design.md`. Las verificaciones indicadas son criterios de terminación futuros, no resultados obtenidos.

## 1. Base de desarrollo y preservación

- [x] 1.1 Principal: tras nueva solicitud humana de Apply, preparar K1 independiente desde K0, sin cambiar árboles/ZIP/manifiestos 0.1.3 y 0.1.4; verificar con comparación de hashes e inventario completo antes/después y confirmar que el destino no sustituye una versión existente.
- [x] 1.2 Developer: adaptar en K1 la detección de versión y estructura en `testing/kit_validation.py`, LEEME y documentación de configuración; comprobar que reconoce K1 y que ninguna prueba de K1 requiere instalar `harness_local` o importar módulos históricos.

## 2. Reglas y configuración compatible

- [x] 2.1 Developer: añadir README/comunes y plantillas sustantivas Bronze/Silver/Gold con estado explícito, reglas justificadas SQL/Spark y especialidades jobs/pipelines pendientes; verificar por revisión que cada obligación activa tiene ID, condición, fundamento, evidencia, comprobación y excepción, sin valores de cliente ni documentos vacíos.
- [x] 2.2 Developer: ampliar `docs/proyecto.json` y su schema con reglas/transiciones opcionales y defaults inactivos/informativos; añadir casos que acepten configuración 0.1.4 intacta y rechacen rutas inválidas, IDs/condiciones desconocidas o activación contradictoria; documentar actualización conjunta de schema y consumidores antiguos estrictos.
- [x] 2.3 Developer: implementar resolución selectiva de documentos/IDs y comprobación de hashes usando utilidades actuales; verificar Silver/Spark sin Gold/SQL/jobs/pipelines, listas vacías justificadas y documentos activos ausentes, con selección idéntica transmitida a todos los roles.
- [x] 2.4 Developer y Reviewer: reconciliar buenas prácticas con las reglas canónicas y documentar gobierno/excepciones; verificar que erratas no exigen una HU adicional y que un rol no puede cambiar obligación/criterios/selección para aprobar su propio resultado sin decisión del responsable.

## 3. Contrato y salida común

- [x] 3.1 Developer: añadir el único `handoff.schema.json` con secciones y requisitos por transición, referencias locales y `$defs` de snapshots/informe; añadir fixtures válidas e inválidas para planificación sin resultados, Tester con recibos, IDs externos/agente nulos, no-aplica justificado, JSON duplicado y versiones desconocidas; comprobar Draft2020-12 offline.
- [x] 3.2 Developer: adaptar plantilla de handoff y render determinista de las siete secciones sin mantener otro estado humano independiente; comprobar enlaces, intento origen y rechazo/detección de resumen obsoleto, con detalle distinto para Planner, Tester y cierre.
- [x] 3.3 Developer: conservar intentos y evidencia por creación exclusiva, incluyendo `previous_handoff` y contador de ronda técnica separado; verificar que corregir referencia crea nuevo intento sin sobrescribir el previo ni consumir/reiniciar rondas técnicas.

## 4. Git, alcance y vigencia compartidos

Bloque de refactorización técnica independiente, con mayor riesgo concentrado en identidad del candidato, clasificación de derivados y conservación de evidencia. Tras 4.1/4.2, implementar 4.3, 4.4 y 4.6 y verificar el conjunto mediante 4.5 antes de conectar los roles del grupo 5. Se conservan los identificadores para mantener las referencias del diseño. Este orden es una dependencia técnica de implementación, no una fase, componente ni aprobación humana adicional.

- [x] 4.1 Developer: ampliar observación Git compartida para snapshots de entrada/salida con HEAD/base, índice, modos, contenido rastreado y no rastreado, renombres/borrados/conflictos; verificar que detecta cambios posteriores en archivos antes limpios y en archivos ya modificados, conservando el origen/destino real.
- [x] 4.2 Developer: comparar diferencias del intervalo con rutas/acciones asignadas al rol, separando cambios de roles previos; comprobar escritura no permitida de Tester, renombre fuera de alcance, referencia inicial ausente y autoría incierta por escritura externa, sin reiniciar la HU ni simular autoría.
- [x] 4.3 Developer: incorporar proyección explícita de metadatos derivados a `git_adapter`/`workflow`/`contract.py` y procedencia del schema de plan, con política/contexto congelados y recibos de observación separados; verificar que un handoff futuro o intento nuevo no exige editar el plan ni predecir hashes, que resumen/recibo humano no altera la huella técnica y que criterio/regla/configuración/código/test/fixture alterado sí invalida.
- [x] 4.4 Developer: vincular proyección de Sync/Archive al diff revisado y mapa exacto de movimientos sin exclusiones globales; comprobar que movimiento previsto conserva vigencia, un cambio semántico encubierto invalida y los recibos de planes anteriores no se reetiquetan ni adoptan entre planes.
- [x] 4.5 Tester: después de 4.3/4.4/4.6, ejecutar la regresión conjunta de plan/run/gate sobre proyecciones, Sync/Archive, stage/commit y corrección de referencias usando directamente los adaptadores, antes de integrar roles o depender del CLI del grupo 5; entregar recibos que demuestren preservación del mismo plan/candidato/entorno cuando proceda y ausencia de suites invocadas por verificadores de evidencia. Cubrir invalidación real, dependencias funcionales de estado Git y casos no soportados; el resultado satisfactorio del bloque es precondición técnica del grupo 5.
- [x] 4.6 Developer y Tester: incorporar/verificar identidad `content-v2` del mismo plan antes y después de stage/commit, comparando manifiesto probado con árboles local/remoto y transformaciones autorizadas; añadir casos de staging parcial, hook que cambia código, modo distinto, commit ajeno, base cambiada y evidencia caducada. Para checks que consumen rama/índice/HEAD u otro estado Git, comprobar vigencia de esas entradas o informar que no están soportadas por la equivalencia, sin conservar su aprobación solo por archivos iguales. Comprobar que no se adopta entre planes ni altera recibos históricos y documentar el límite de planes anteriores, sin exigir soporte universal de estados Git.

## 5. Validador e integración de roles

Conectar estos consumidores solo después de verificar satisfactoriamente el bloque 4 mediante 4.5; no compensar defectos de identidad o vigencia con reglas del orquestador.

- [x] 5.1 Developer: implementar `transiciones.py check/render` sobre schema, Git y gate existentes, sin otro catálogo/runner; comprobar pre-Apply sin resultados futuros, post-Tester con contraste de evidencia primaria y ausencia de llamadas a run, red, instalación o publicación.
- [x] 5.2 Developer: implementar clases/efectos/códigos de salida y su consumo por el principal según código, modo e informe; probar advertencia, decisión necesaria e incumplimiento habilitado, sin manejador genérico que aborte toda la HU por un código no cero. Comprobar código 3 limitado a la continuación dependiente, código 4 sin veto nuevo en informative e informe ausente/ilegible como indeterminado, sin exponer valores sensibles ni interpretar exit 0 o un error como autorización o validez técnica.
- [x] 5.3 Developer: integrar modo informativo inicial y catálogo cerrado de condiciones bloqueantes; verificar en el consumidor inconsistencia nueva o error del validador sin veto añadido y, por separado, aprobación ausente o gate previamente obligatorio fallido/no acreditado que sí conserva la detención correspondiente. Comprobar restricciones previas mediante sus mecanismos actuales aun con informe ilegible, enforcing solo para IDs aprobados y ausencia de promoción o reparación autónoma.
- [x] 5.4 Developer: actualizar AGENTS, orquestador, cuatro perfiles y plantilla de tareas con lectura/escritura real por HU y paradas Propose/Apply/Sync/Archive/PR; verificar por recorridos de contrato que solo principal entrega Git, Reviewer puede Sync/Archive en su fase y nadie cambia criterios/políticas para aprobarse.
- [x] 5.5 Developer: documentar límites de instrucciones/detección/sandbox y las rutas/salidas CLI; comprobar inspección sin efectos y escritura de informe exclusiva que rechaza destino ocupado, colisión con evidencia y symlink/junction/traversal.
- [x] 5.6 Tester: ejecutar matriz focalizada de transiciones con casos válidos/inválidos, herramientas/dependencias ausentes y trabajo independiente durante una decisión pendiente; comprobar reanudación desde ese punto al resolver dudas, recibir autorización aplicable o corregir la condición técnica, conservando evidencia válida sin pedir otra vez la misma autorización ni sustituir evidencia obligatoria por aval humano. Guardar resultados por intento sin ejecución remota ni bucles automáticos de reintento.

## 6. Objetos y entrega por proveedor

- [x] 6.1 Developer: ampliar objetos del contrato y `evidencia-hu.md` derivada con IDs, tipos, operación, rutas, capas/capacidades, criterios/reglas y referencias; probar documentación no-aplica, código sin despliegue y evidencia externa de despliegue sin deducir verificación remota.
- [x] 6.2 Developer: definir plantilla PR canónica y materialización de `pr-title.txt`, `pr-body.md` y vista `pr.md`, con hashes en el contrato de entrega; verificar contenido idéntico para ambos proveedores y separación entre instrucciones de plantilla y cuerpo transportable, sin plantilla nativa divergente.
- [x] 6.3 Developer: actualizar delivery/documentación/principal/orquestador con transporte GitHub manual y Azure Services ya permitido; comprobar mediante ejemplos/fixtures Unicode, Markdown, saltos, comillas y caracteres especiales, decodificación de URL y fallback de contenido no precargable, sin crear PR remoto.
- [x] 6.4 Developer: especificar/verificar lectura posterior de título/cuerpo, repo, ramas y commit Azure, estados draft/form_prepared/creation_unconfirmed/created_verified y reconciliación ante respuesta ambigua; probar con dobles discrepancia y PR existente sin duplicación ni edición remota automática.
- [x] 6.5 Tester y Reviewer: comprobar autorización de solo Archive, solo push y autorización completa vigente; verificar que las primeras no habilitan acciones adicionales y la última no solicita confirmaciones repetidas por cada paso. Documentar que pruebas con dobles no certifican el proveedor real.

## 7. Integración y paquete candidato

- [x] 7.1 Tester: ejecutar integración proporcional de HU Silver/Spark, documental y bloqueo por evidencia obsoleta/escritura fuera de alcance; verificar límites de runtime inactivo y preservación de trabajo válido. Si falta un entorno requerido, registrar blocked/not_run, sin falsear el recorrido como ejecutado.
- [x] 7.2 Developer: añadir `scripts/package_manual_015.py` dirigido solo a K1 y reutilizar validaciones de integridad/neutralidad existentes; comprobar guardas ante destino incorrecto, preservación 0.1.3/0.1.4, upstream/licencias y ZIP/manifiesto/hash/informe concordantes, sin publicar release.
- [x] 7.3 Tester: ejecutar comprobaciones locales integradas del kit y empaquetado candidato; registrar comandos/resultados reales, neutralidad y límites, verificando que no se ejecutaron scripts 014 sobre versiones anteriores ni cambios remotos.
- [x] 7.4 Reviewer: revisar cumplimiento de las cuatro specs, contratos, evidencia, regresiones y migración/reversión; realizar verify y evaluar Sync únicamente con resultado favorable y gates vigentes. La casilla se completa con referencias a revisión real, no por existir el diseño.
- [x] 7.5 Principal: presentar expediente, diff de Sync cuando corresponda, resultados y decisiones pendientes; verificar que se distingue preparación local, aprobación de archivo y autorización de commit/push/PR, sin iniciar una acción no autorizada.

## Workflow follow-up

- Conservar la pausa actual: presentar esta propuesta y esperar revisión; solo una nueva solicitud humana habilita Apply.
- Después de implementación/revisión favorable, realizar Sync según su skill y presentar el expediente concreto para autorización humana de Archive; ejecutar Archive solo con esa respuesta y sin duplicar Sync.
- Commit/push y PR solo con autorización que cubra cada acción, candidato, destino y contenido. No son tareas que esta propuesta autorice ni resultados requeridos para preparar el diseño. Merge y despliegue permanecen fuera.
- Durante adopción autorizada, observar HU representativas en modo informativo usando evidencia normal. El responsable decidirá IDs concretos que pasan a enforcing tras casos válidos/inválidos comprobados; nunca una promoción autónoma.
- Si se necesita comprobar transporte con un proveedor real, plantear la operación concreta con autorización y entorno aplicables; conservar not_run hasta disponer de evidencia. No añadir una integración remota a este incremento.
