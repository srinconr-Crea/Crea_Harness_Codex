# Spec Delta

## Purpose

Preparar una máquina y una identidad personal para trabajar sobre un proyecto ya configurado, reutilizando el onboarding compartido sin sobrescribirlo ni conceder permisos nuevos.

## ADDED Requirements

### Requirement: Existing checkout and shared readiness

La preparación SHALL identificar raíz, revisión, remoto y configuración del checkout. SHALL comprobar onboarding, catálogo, referencias y OpenSpec existentes, diferenciando preparación compartida de preparación personal. MUST NOT marcar completo un onboarding incompleto ni modificarlo para permitir una HU.

#### Scenario: Second developer clones approved configuration
- **WHEN** otra persona abre un clon con onboarding completo y referencias coherentes
- **THEN** reutiliza sus reglas, perfiles, specs y catálogo y evalúa únicamente la preparación local pendiente

#### Scenario: Shared setup is incomplete or inconsistent
- **WHEN** falta configuración requerida o setup_complete contradice el catálogo o las referencias
- **THEN** informa la discrepancia al responsable, conserva los archivos y no declara listo el desarrollo dependiente

### Requirement: Persistent entry point independent of distribution prompt

El proyecto configurado SHALL contener una entrada de preparación local y su guía, descubribles desde las instrucciones del proyecto. La sección C del prompt SHALL invocar esa misma capacidad sin ejecutar A o B. MUST NOT exigir conservar el prompt extenso de distribución en el repositorio cliente.

#### Scenario: Clone without packaging prompt
- **WHEN** el clon no contiene Prompt_configurar-kit-proyecto.txt pero sí los recursos operativos instalados
- **THEN** la persona puede iniciar y completar su preparación desde la entrada local documentada

### Requirement: Bounded personal environment binding

La preparación SHALL separar intérprete y alias personales de la configuración versionada mediante un binding local opcional con schema y claves permitidas. MUST NOT aceptar credenciales ni overrides de comandos, política, ramas, permisos, modelos, reglas o capacidades. El camino legacy sin binding SHALL conservar su comportamiento.

#### Scenario: Different interpreter locations
- **WHEN** dos desarrolladores tienen Python en rutas absolutas diferentes
- **THEN** cada uno registra su entorno local sin editar la configuración compartida y los planes identifican el intérprete efectivo de cada ejecución

#### Scenario: Local override attempts to change required checks
- **WHEN** el binding intenta redefinir catálogo, required_checks o destino del PR
- **THEN** se rechaza antes de ejecutar o escribir configuración y se conserva el estado anterior

### Requirement: Applicable tools and authorized preparation

La preparación SHALL detectar sistema operativo, herramientas, versiones y dependencias aplicables antes de proponer instalaciones. SHALL instalar o actualizar solo dentro de un alcance explícitamente autorizado. Una herramienta ausente SHALL dejar un pendiente concreto sin impedir diagnóstico independiente ni activar capacidades.

#### Scenario: Missing validation dependency without installation permission
- **WHEN** falta una dependencia de validación y no está autorizada su instalación
- **THEN** registra su nombre y efecto, no instala y continúa las inspecciones independientes posibles

#### Scenario: Tool already satisfies project requirements
- **WHEN** una herramienta existente cumple los requisitos vigentes
- **THEN** la conserva sin reinstalarla o actualizarla por rutina

### Requirement: Personal authentication and interactive authority

La preparación SHALL guiar las autenticaciones personales aplicables de Git/GCM, Azure y Databricks. Credenciales, MFA, confianza y decisiones de permisos SHALL permanecer bajo intervención de la persona. MUST NOT copiar sesiones ajenas, iniciar login implícito ni guardar secretos en informes o Git.

#### Scenario: Authentication requires MFA
- **WHEN** una comprobación requiere autenticación interactiva
- **THEN** indica el paso personal y espera esa intervención para la continuación dependiente, manteniendo diagnóstico independiente

#### Scenario: Project does not use Databricks
- **WHEN** Databricks no aplica o su integración está inactiva
- **THEN** no exige su login, no instala sus herramientas ni activa su integración como consecuencia de preparar la máquina

### Requirement: Safe connection checks

Las comprobaciones de conexión SHALL usar operaciones de lectura acotadas, destinos explícitos y credenciales ya disponibles. SHALL distinguir lectura comprobada, acceso denegado, fallo de conexión y operación no realizada. MUST NOT usar escrituras de prueba ni consultar Boards sin la HU y fase autorizadas.

#### Scenario: Azure repository can be read
- **WHEN** se solicita comprobar el repositorio Azure configurado y hay identidad disponible
- **THEN** contrasta el repositorio mediante lectura explícita sin PR, pipelines, cambios de permisos ni consultas generales de Boards

#### Scenario: Read permission does not establish publish permission
- **WHEN** una lectura del remoto resulta correcta
- **THEN** acredita solo esa operación y no afirma permisos de push, creación de PR, merge o despliegue no comprobados

### Requirement: Preserve configured project resources

La preparación C MUST NOT reinicializar OpenSpec, reinstalar skills existentes ni sobrescribir configuración compartida, perfiles, modelos, constituciones, reglas, catálogos, specs o evidencia. Las incompatibilidades SHALL quedar como pendientes de mantenimiento separado.

#### Scenario: Existing skill differs from distribution
- **WHEN** una skill o perfil personalizado difiere de la distribución
- **THEN** conserva los bytes, registra la diferencia pertinente y no ejecuta una actualización de kit dentro de C

### Requirement: Repeatable Windows preparation

La preparación SHALL ser repetible y funcionar con Windows/PowerShell y rutas con espacios sin exigir activar un virtualenv ni cambiar ExecutionPolicy. SHALL conservar un binding equivalente sin escrituras innecesarias y no cambiar configuración global implícitamente.

#### Scenario: Second identical preparation
- **WHEN** se repite C con el mismo checkout, herramientas y binding
- **THEN** confirma el diagnóstico sin editar archivos compartidos, repetir instalaciones o reescribir el binding equivalente

#### Scenario: PowerShell script wrappers are blocked
- **WHEN** la política local bloquea wrappers ps1
- **THEN** usa las entradas ejecutables o cmd soportadas y el intérprete explícito, o informa el límite sin cambiar la política

### Requirement: Local diagnostic record and honest status

El diagnóstico SHALL informar revisión/configuración observadas, herramientas, operaciones comprobadas, pendientes y estado ready, partial o blocked con motivos. Su persistencia SHALL ser local, sanitizada y explícita; MUST NOT certificar agentes nativos, hooks, runtime o permisos no observados.

#### Scenario: Explicit diagnostic output
- **WHEN** se solicita un informe en una ruta local permitida nueva
- **THEN** lo crea sin secretos, identifica las comprobaciones no realizadas y no sobrescribe un informe anterior

### Requirement: Side effect free default inspection

La inspección por defecto SHALL devolver diagnóstico sin escribir, instalar, autenticar, ejecutar suites, cambiar ramas ni contactar servicios. La lectura online, exportación y modificación del binding SHALL ser operaciones explícitas separadas. MUST NOT tratar inspeccionar como autorización para preparar herramientas.

#### Scenario: Offline inspection
- **WHEN** se invoca inspección sin opciones de lectura online ni salida
- **THEN** no modifica el checkout o estado global ni realiza llamadas remotas y declara esas comprobaciones no realizadas
