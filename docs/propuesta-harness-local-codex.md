# Propuesta de Harness Local para Codex Desktop

Revisión: **9 de octubre de 2026**, America/Bogota.
Estado: **base local y fundamento de calidad implementados; incrementos 02–08 pendientes**.
Esta revisión sustituye el itinerario inicial del 8 de octubre. Los cambios archivados y su evidencia conservan el historial.

## 1. Objetivo y estado real

Una persona nueva debe poder preparar un cliente mediante entrevista o plantilla y completar una HU desde Codex Desktop, con roles, herramientas, prácticas, pruebas, revisión, evidencia y PR autorizado.

El producto Local-Harness comparte procedimiento y controles. Cada cliente conserva código, specs y contexto propio. Codex mantiene conversación, inferencia, herramientas y delegación; el núcleo Python aporta contratos, validadores, estado y adaptadores.

Implementado en 0.1.0: descriptor/política/binding v1, doctor, init preview/export/apply create-only, recursos OpenSpec, locks/journal y recuperación conservadora Windows. Incrementos archivados: bootstrap-codex-local-core y apply-client-onboarding. Ver [README](../README.md) y [evidencia](evidence/apply-client-onboarding.md).

Pendiente: onboarding conversacional, roles configurados, herramientas por rol, flujo persistido de HU, gates de desarrollo/PR, validación remota, observabilidad, ejecutor de evals, instalador y update. Ninguno de los comandos nuevos que aparecen abajo está disponible todavía.

Preparado durante esta planificación: 32 prácticas, 24 casos de prueba, 24 evals con ocho roles, fixture sintético y nueve Skills oficiales descargadas. El incremento 01 formaliza contratos/carga/empaquetado y extensiones técnicas; ver [operación de calidad](quality-foundation.md). Los casos siguen siendo definiciones: status not_run significa ausencia de ejecución de agentes o pruebas de HU. La validación de los documentos no certifica el flujo operativo.

## 2. Responsabilidades y separación

| Ámbito | Contenido | Regla |
| --- | --- | --- |
| Producto | Skills de procedimiento, plantillas de roles, prácticas, catálogos/evals, Python, adaptadores, distribución | Genérico y versionado; sin negocio ni credenciales de un cliente |
| Cliente | Código/tests, OpenSpec, documentación, AGENTS, .codex, Skills y extensiones particulares | Configuración y contexto portable del proyecto |
| Desarrollador | Políticas seleccionadas, bindings, conexiones, estado, backups y registros | Externo al target y separado por cliente/checkout |
| Codex Desktop | Sesión, inferencia, tools y subagentes | Capacidades deben probarse en la app objetivo |
| Databricks/CI/proveedor Git | Ejecución, permisos efectivos, validación/publicación | Identidad, alcance y autorización explícitos |

.codex no es exclusivamente negocio: contiene configuración de ejecución. Contexto técnico y de negocio puede vivir en specs, documentación y Skills. La separación se hace por responsabilidad y reutilización, no por llamar “negocio” a toda carpeta ajena al código.

Estructura **objetivo**, no inventario actual:

```text
Local-Harness/
  src/harness_core/        contratos, estado de HU, gates, integridad
  src/harness_local/       comandos, integración, adaptadores
  skills/                 onboarding, HU, contexto, validación, cierre
  agent_templates/        roles genéricos
  practice_packs/         reglas comunes versionadas y sus referencias
  evals/                  datasets, scorers y protocolos/runner
  resources/vendor/       snapshot Databricks y procedencia
  installer/              bootstrap y actualización
  plugin/                 distribución opcional certificada
  tests/, schemas/, docs/

Cliente/
  .harness/client.yaml       identidad v1 actual
  .harness/development.yaml  selección portable futura
  .harness/kit.lock.json     versiones/hash futuros
  AGENTS.md                 reglas del proyecto e inicio de workflow
  .codex/config.toml        ajustes de proyecto compatibles
  .codex/agents/*.toml      roles generados/integrados y revisados
  .agents/skills/           OpenSpec y recursos específicos
  openspec/, docs/, src/, notebooks/, tests/, resources/
```

La lógica Python se instala como paquete único. Skills pueden tener wrappers, pero no copian store, gates o telemetría en cada carpeta.

## 3. Configuración y confianza

Se mantienen sin cambios silenciosos los tres contratos v1:
- Descriptor cliente: identidad, repository, base_branch y openspec_root.
- Política externa seleccionada: rutas/límites operativos; su hash asegura integridad, no firma/autorización externa.
- Binding externo: checkout/target, policy hash, state_dir y referencia opcional de perfil.

Los nuevos contratos separan información que v1 no admite:
- ClientDevelopmentConfig: stack, convenciones, referencias de negocio, extensiones de prácticas, roles y ValidationPlan seleccionados.
- ClientToolBinding externo: proveedores/perfiles/conexiones seleccionados, sin secretos.
- RoleCatalog/ToolRequirements: responsabilidad, entradas/salidas, modelo/esfuerzo y capacidades required/optional.
- DesktopCertificate: observaciones reales de versión/superficie/roles/herramientas.
- ReleaseManifest/kit lock: versiones, hashes, ownership y compatibilidad.

Los modelos, esfuerzos, host, perfil, runtime Spark/DBR, recursos sandbox y proveedor de historias se seleccionan en configuración/onboarding; no se presuponen disponibles universalmente. GitHub será el primer proveedor remoto implementado; Jira/Linear son extensiones opcionales por contrato.

## 4. Experiencia de onboarding

La Skill harness-client-onboarding guía; el ejecutable valida/aplica:
1. Elegir checkout existente. La instalación/clonado no se disfraza de init actual.
2. Aceptar plantilla o entrevista y descubrir estructura local.
3. Preguntar solo decisiones faltantes: identidad, convenciones, reglas, políticas, roles/modelos, herramientas y validaciones.
4. Mostrar datos descubiertos, fuentes y selecciones; no inferir permisos de contexto.
5. Generar plan con contenido, destinos, hashes y acciones por etapa.
6. Revisar y aplicar preparación/integración explícita.
7. Probar dentro de Desktop Skills, roles, modelo/esfuerzo y herramientas.
8. Emitir prepared/certified y pendientes remotos diferenciados.

El init v1 sigue create-only y bloquea AGENTS personalizado. Onboarding nuevo lo reutiliza donde sea aplicable; para clientes personalizados tiene preparación compuesta e integración revisada, sin ejecutar un plan v1 conflictivo. Ediciones necesitan contrato separado con old/new hashes, backup y recuperación.

Si .harness/ está protegido y falta descriptor, bootstrap queda bloqueado. Se selecciona una política de onboarding revisada; el asistente no relaja la política por sí mismo.

La Skill es el asistente conversacional. El launcher/instalador del 08 facilita la entrada desde un equipo nuevo; la Skill y el CLI pueden usarse antes desde el entorno de desarrollo.

## 5. Flujo dentro de Codex y roles

AGENTS.md contiene reglas permanentes e invocación del workflow. harness-hu describe secuencia, delegaciones y fallos. Cada TOML define un rol y ajustes compatibles; prácticas detalladas viven en referencias/Skills.

| Rol | Entrega | Herramientas previstas |
| --- | --- | --- |
| Principal | Secuencia, decisiones, aprobaciones, estado y cierre | Comandos de HU/gates, conectores seleccionados |
| Analyst / enrich-HU | HU aclarada y criterios | Fuente de historias, specs y contexto cliente |
| Impact analyzer | Dependencias/rutas/riesgos con referencias | Búsqueda local, documentación |
| Planner / propose | Artefactos OpenSpec y manifiesto de validación | explore, propose, update |
| Developer | Implementación y pruebas del alcance | apply, prácticas por tecnología |
| Tester | Pruebas ejecutadas y evidencia | Workers aislados, adaptadores Databricks |
| Auditor / reviewer | Hallazgos independientes y regresiones | Diff, prácticas, evidencia |
| Verifier | Concordancia specs/candidato/criterios/evidencia | verify y gate de validación |

Responsabilidades no implican ocho subagentes en cada HU. El principal puede resolver fases pequeñas; revisión independiente y un escritor por rutas compartidas son propiedades del flujo. Delegación, concurrencia y correcciones tienen límites explícitos.

Modelo y esfuerzo se fijan por perfil y se prueban en Desktop. Modelo ausente bloquea ese rol; no hay sustitución silenciosa. La documentación soporta configuraciones de rol, pero su disponibilidad y permisos efectivos se certifican en la aplicación objetivo. [Subagentes de Codex](https://learn.chatgpt.com/docs/agent-configuration/subagents).

## 6. Herramientas, Skills, MCP y hooks

ToolRequirement identifica capability, propósito, required/optional, versión, selección, permiso efectivo y evidencia. Una instrucción de “solo lectura” no demuestra permiso de solo lectura.

Skills comunes: procedimiento del harness y prácticas técnicas. Skills cliente: convenciones/reglas particulares. Skills oficiales Databricks: dependencia opcional fijada por commit; wrappers añaden límites operativos sin modificar upstream.

MCP/CLI/API se eligen por proveedor y capacidad. Lectura de historia, push, create PR y write story son permisos diferentes. El primer conector no obliga a instalar todos los demás.

Hooks complementan eventos cubiertos: inicio, herramientas, compactación, delegación y cierre, únicamente cuando existan y se hayan probado. Cambios de configuración/confianza deben ser visibles. No garantizan interceptar toda acción de Desktop. La documentación separa AGENTS, Skills, MCP y subagentes. [Personalización](https://learn.chatgpt.com/docs/customization/overview).

## 7. Ciclo de HU y gates

Explore/enrich → impacto → propose/update → aprobación de revisión → apply → pruebas → auditoría/verify → cierre OpenSpec → candidato final → PR autorizado.

Estado externo por cliente/checkout/HU/intento registra:
- Fuente/revisión de historia, base, plan/manifiesto y aprobación actor/fecha/hash.
- Roles/modelos/esfuerzos efectivos y asignación de escritor.
- Candidato con archivos nuevos, cambios y eliminaciones.
- Pruebas, evidencia, hallazgos y correcciones.
- Operaciones remotas pendientes, job IDs y receipt de PR.

Cambio de alcance invalida aprobación; cambio del candidato invalida pruebas/revisión correspondientes. Sync/archive que cambia el candidato debe incluirse antes de prueba final o revalidarse según impacto. Hasta dos correcciones por intento; fallos de infraestructura se reportan separadamente.

SQLite se propone para coordinación de HU a partir de 04; el journal de onboarding actual mantiene su formato JSON. Interrupción exige revalidación/reconciliación; no se interpreta un timeout como operación no realizada.

Gates controlan transiciones/adaptadores del kit. Permisos de sandbox, credenciales, CI y protección de ramas determinan lo posible fuera del procedimiento. No se promete cobertura total de acciones Desktop.

La aprobación técnica y la autorización de publicar tienen alcance explícito; pueden recogerse juntas si la persona lo autoriza. No se añaden confirmaciones redundantes, ni se inventa autorización para comentar historias, mergear o desplegar.

## 8. Prácticas y validaciones Databricks

El [paquete de calidad](planning/quality/README.md) diferencia reglas required y recomendaciones advisory. Excepciones técnicas requieren motivo/alcance/revisión; jamás amplían permisos.

Cobertura inicial:
- SQL: contrato de grano/cardinalidad, null/decimal/fechas y semántica de runtime; rendimiento requiere perfil/baseline.
- Python: lógica comprobable, efectos separados, errores observables y dependencias fijadas.
- Notebooks: control de versiones, lógica compartida y ejecución desde sesión limpia.
- PySpark: filas/esquema, vacíos/duplicados/nulls, tolerancias e idempotencia cuando aplique.
- YAML/DABs: targets, variables y resolución de referencias; parse offline y bundle validate tienen alcances distintos.
- CI/CD: pruebas/promoción, artefactos versionados, identidad y separación de ambientes.

Fuentes principales: [notebooks](https://learn.microsoft.com/es-es/azure/databricks/notebooks/best-practices), [testing PySpark](https://spark.apache.org/docs/latest/api/python/getting_started/testing_pyspark.html), [bundles](https://docs.databricks.com/aws/en/dev-tools/bundles/faqs) y [CI/CD](https://docs.databricks.com/aws/en/dev-tools/ci-cd/flows). Son adaptaciones del harness, no certificación de cada regla por el proveedor.

ValidationPlan selecciona capas según impacto:
- L0: parsing/lint/schema y referencias locales.
- L1: unit tests Python/PySpark sintéticos en worker aislado.
- L2: comportamiento SQL/Spark/Delta en runtime compatible.
- L3: integración notebook/job/bundle en sandbox autorizado.

Código cliente no se importa con credenciales del desarrollador por defecto. Pruebas locales arbitrarias van a worker sin credenciales; remotas a identidad separada y recursos allowlist. bundle validate puede resolver/acceder a servicios: se trata como potencialmente remoto.

Cada evidencia incluye candidate/plan/practice hashes, runtime/datos, comando/identidad, estado, resultado/hash y job run ID. Mocks prueban adaptadores; no demuestran ejecución Databricks. Required blocked/not_run impide certificar candidato.

## 9. Tests y evals

Tres capas distintas:
1. Tests del kit: contratos, integridad, transiciones, confinamiento y recuperación.
2. Pruebas de una HU: comportamiento funcional/integración y criterios del cliente.
3. Evals de agentes: calidad del proceso, herramientas, instrucciones, modelos y razonamiento.

El catálogo inicial incluye controles limpios y defectos conocidos, ambigüedad, fallos de runtime, scope, evidencia obsoleta y publicación. Sus checks tienen oráculos independientes y criticidad; no son resultados ejecutados.

Evaluación manual en Desktop es válida con protocolo/evidencia. Automatización solo usa interfaces soportadas; CLI certifica CLI. Tres repeticiones por caso/configuración para comparar perfiles. Gate: todos los críticos aprobados y >=90% de no críticos; blocked/not_run no cuentan como passed.

Golden se usa para desarrollo; holdout se reserva para promoción. Los ejemplos de holdout en esta planificación son semillas de diseño, no un conjunto secreto independiente de producción. Al implementar se separan operativamente casos y acceso. Juicio LLM opcional se calibra con etiquetas humanas y no reemplaza checks críticos.

Cada milestone evalúa capacidades disponibles; casos de proveedores se activan en 07 y el catálogo completo en 08. Cambiar prácticas/rol/modelo/herramientas exige comparar con baseline antes de promover.

## 10. Observabilidad y consumo

Registrar actividad por HU/intento/rol: duración, delegaciones, retries, pruebas, eventos cubiertos y runs remotos. Identificadores nativos se usan solo cuando interfaz soportada los expone.

Tokens/costo se guardan con source, scope y unidades si existe una fuente atribuible. Si no, null con motivo unavailable. Cuota de cuenta no se distribuye por HU; estimación de texto o precio API no equivale a factura Desktop.

El recolector vive en el paquete/adaptador, no duplicado en cada Skill. Hooks certificados pueden alimentar eventos, pero no conceden acceso a toda la telemetría interna. MLflow es opcional para exportación/evals, sin convertirse en requisito del núcleo. Costos Databricks requieren asociación real de run y registros de uso; no atribuir un warehouse compartido completo a una HU.

## 11. Roadmap y dependencias

La secuencia detallada está en [roadmap](planning/roadmap.md). Cada incremento requiere implementación y verificación del anterior:
01 calidad/evals → 02 roles/herramientas Desktop → 03 onboarding guiado → 04 HU/gates → 05 validación Databricks → 06 observabilidad/evals → 07 historias/PR → 08 piloto/distribución.

Todos tienen proposal, design, delta specs y tasks sin marcar. OpenSpec valida estructura; no enforcea por sí mismo dependencias entre cambios. Antes de 04 se verifica manualmente la evidencia del predecesor; después se incorporan gates de negocio pertinentes.

Distribución reproducible es el último incremento: lock/manifiesto, launcher, plugin donde esté certificado y update/recover con comparación installed/upstream/local hashes. Preserva personalizaciones y estado. El plugin no se presupone instalador de Python o agentes.

## 12. Criterio de producto terminado

Usuario nuevo en Windows → preparación guiada → configuración efectiva verificada en Desktop → HU sintética → pruebas exigidas → auditoría/verify → PR draft autorizado, con evidencia y recuperación de interrupciones.

Dos clientes sintéticos demuestran aislamiento. Después una copia NaturaPet prueba el flujo con su política y recursos sintéticos seleccionados. Datos/catálogos/jobs reales, merge y despliegue productivo requieren alcance distinto y permanecen fuera del piloto.

Release exige pruebas de instalación en segundo entorno, eval gate completo y actualización/reversión preservando personalizaciones. Capacidades pendientes se reportan como pendientes; no se declaran listas por existir archivos.

## 13. Procedencia e historial

Snapshot oficial Databricks: commit ba45d10df7413de14c32937bbd584aeee17d22a2, nueve Skills/110 archivos, LICENSE y NOTICE conservados. [Procedencia y hashes](../resources/vendor/databricks-agent-skills/SOURCE.json). Descargado para diseño, sin instalación ni ejecución.

La revisión inicial examinó Demo-Harness-Databricks/Db_Spec_Harness en bb559dea91e1a32180c1c8e97b9a5c0b15077593 y Naturapet_DLH/develop en c5efcf154c7e56101e6dd6c3ea830f6512e6b184. Es evidencia histórica, no afirmación sobre sus ramas actuales. El runtime mediado original no se porta entero a Desktop.

El artículo Medium aportado se consultó como referencia secundaria, sin copiarlo ni usarlo como autoridad normativa. Prácticas y fuentes se registran en [practices.json](planning/quality/practices.json).

Evidencias existentes: [bootstrap](evidence/bootstrap-codex-local-core.md), [onboarding](evidence/apply-client-onboarding.md), [verificación onboarding](evidence/onboarding-verification.md). No prueban todavía roles, hooks, token accounting ni HU end-to-end.
