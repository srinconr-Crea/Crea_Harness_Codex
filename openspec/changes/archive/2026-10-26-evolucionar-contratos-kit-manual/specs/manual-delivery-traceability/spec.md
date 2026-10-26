# Spec Delta

## Purpose

Conectar HU, reglas, contenido, objetos y entrega del kit manual mediante evidencia canónica y salidas humanas coherentes, distinguiendo lo preparado de lo creado, desplegado o verificado.

## ADDED Requirements

### Requirement: Object delivery inventory

La evidencia de HU SHALL enlazar objeto/tipo, capa/capacidad aplicable, operación, rutas, criterios, reglas y referencias de entrega. SHALL distinguir previsto, código implementado, desplegado y verificado mediante evidencia independiente. El inventario MUST NOT duplicar especificaciones ni afirmar linaje operativo de datos.

#### Scenario: Notebook exists without deployment
- **WHEN** existe código de una transformación Silver y pruebas locales
- **THEN** puede acreditar implementación, conserva despliegue no acreditado y no afirma verificación del objeto remoto

#### Scenario: Documentary object
- **WHEN** el objeto es una guía sin capa de datos
- **THEN** registra tipo documental y no aplica justificado para capa/capacidad y despliegue

#### Scenario: Evidence of existing authorized deployment
- **WHEN** se aporta una referencia comprobable a una entrega ya realizada fuera de este incremento
- **THEN** vincula esa evidencia al objeto y ambiente sin ejecutar otro despliegue ni deducir verificación funcional

### Requirement: One human summary source

Cada salida humana de fase SHALL derivar del handoff e incluir HU/fase, resultado, alcance/candidato, reglas/evidencia, bloqueos, decisión requerida y siguiente paso con enlaces al detalle. El nivel de detalle SHALL ajustarse a la fase. MUST NOT mantener un segundo estado independiente ni inventar una decisión humana para continuar algo ya autorizado.

#### Scenario: Automatic handoff already authorized
- **WHEN** Developer entrega a Tester dentro del alcance aprobado
- **THEN** el resumen indica la continuación autorizada sin solicitar una confirmación adicional por el mero cambio de rol

#### Scenario: Stale rendered summary
- **WHEN** un resumen fue producido desde otro intento de handoff
- **THEN** indica la referencia desactualizada y lo regenera desde el contrato vigente sin alterar evidencia primaria

### Requirement: Canonical provider neutral PR content

El kit SHALL usar una estructura canónica para título y cuerpo de PR en GitHub y Azure DevOps, vinculada al candidato, pruebas y alcance revisados. La publicación SHALL transportar ese contenido exacto mediante el mecanismo permitido y comprobar el resultado. Una plantilla nativa opcional SHALL derivar de la fuente canónica sin edición independiente.

#### Scenario: GitHub prepared form
- **WHEN** se prepara el formulario GitHub para ramas y repositorio verificados
- **THEN** incorpora título/cuerpo revisados y comprueba sus valores, o entrega los textos exactos con limitación explícita si el formulario no puede precargarse

#### Scenario: Azure title or body drift
- **WHEN** el PR leído del proveedor difiere en título, cuerpo, repositorio, ramas o commit esperado
- **THEN** no lo declara verificado y comunica la discrepancia sin editar contenido remoto fuera de la autorización

### Requirement: Explicit delivery states and authority

La entrega SHALL distinguir borrador, formulario preparado, creación no confirmada y PR creado/verificado con ID/URL y lectura comprobada. Archive o push por sí solos MUST NOT autorizar crear PR. La autorización vigente que ya cubra acciones, destino y contenido SHALL reutilizarse sin confirmaciones repetidas. Merge y despliegue SHALL permanecer fuera del alcance.

#### Scenario: Push only permission
- **WHEN** la autorización cubre commit/push pero no crear PR
- **THEN** publica solo lo autorizado y entrega borrador/formulario sin afirmar PR creado

#### Scenario: Existing complete authorization
- **WHEN** están autorizados candidato, cierre, commit/push y PR Azure con destino y contenido vigentes
- **THEN** ejecuta esos pasos cuando sus gates pasan sin pedir permiso en cada transferencia

#### Scenario: Ambiguous provider response
- **WHEN** crear un PR autorizado termina sin confirmación
- **THEN** consulta por repositorio/ramas/candidato antes de reintentar; si no puede reconciliar, mantiene creación no confirmada sin duplicarlo

### Requirement: Stable specs and archived case remain distinct

Sync SHALL actualizar las especificaciones estables; Archive SHALL conservar el expediente del cambio; la evidencia SHALL conectar contenido, decisiones, objetos y entrega. Los movimientos previstos de Archive SHALL ser comprobables y no permitir introducir comportamiento nuevo sin revisión.

#### Scenario: Reviewed sync and archive movement
- **WHEN** Sync favorable produce el diff revisado y Archive mueve exactamente ese expediente autorizado
- **THEN** conserva referencias resolubles mediante el mapa de movimiento sin duplicar requisitos en el inventario de objetos

#### Scenario: New behavior during close
- **WHEN** el expediente final añade comportamiento que no estaba en el candidato revisado
- **THEN** detiene el cierre/publicación y solicita revisión y autorización aplicables
