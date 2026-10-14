# Proposal

## Why

El harness dispone de contratos, preparación e integración local, pero hoy exige preparar dependencias y archivos por separado; su Skill de onboarding llega al cliente después de prepararlo. Falta una entrada instalable que convierta esos componentes en la experiencia de un comando y una conversación propuesta por el usuario.

## What Changes

- Añadir un instalador PowerShell de un comando para Windows x64, con versiones/hashes fijados, runtime aislado por usuario y registro reversible de una Skill `harness-setup` disponible antes de crear un cliente. Codex Desktop previamente instalado y autenticado es un prerrequisito externo.
- Conectar la Skill con una nueva fachada de setup: importar descriptor, política, binding y URL de repositorio o pedir únicamente los datos faltantes; detectar herramientas; presentar un plan compuesto; preparar el checkout y recursos mediante adaptadores existentes.
- Añadir un contrato separado de acceso con rutas permitidas para lectura/escritura y denegaciones, sin reinterpretar ni modificar silenciosamente descriptor/política/binding v1. La política se aplica en adaptadores propios y gates; permisos reales de Desktop se diagnostican aparte.
- Preparar herramientas faltantes en ámbito de usuario, incluida Databricks CLI cuando se necesita; guiar OAuth y configuración de perfiles sin pedir secretos en el chat.
- Producir evidencia de descubrimiento de Skills, configuración de los ocho roles, `AGENTS.md`, runtime y capacidades locales/remotas. Distinguir preparado, observado, bloqueado y no comprobado.
- Conservar personalizaciones, recuperación por etapa y ausencia de efectos de preview. No certificar capacidades por copiar archivos ni habilitar release/publicación mientras sigan pendientes los gates históricos.

## Capabilities

### New Capabilities

- `harness-installation-entrypoint`: entrada de instalación autocontenida, descubrimiento inicial de la Skill y mantenimiento reversible del runtime de usuario.
- `guided-environment-setup`: coordinación conversacional de insumos, dependencias, acceso por rutas, autenticación y diagnóstico integral del entorno.

### Modified Capabilities

Ninguna. Se añaden fachadas y contratos separados que componen `harness-distribution`, `guided-client-onboarding`, `client-configuration` y `desktop-integration`; sus contratos v1 y gates se conservan.

## Impact

Extiende `src/harness_local/distribution_kit`, distribución, CLI, onboarding guiado, recursos Desktop y contratos/esquemas nuevos en `harness_core`. Añade pruebas de instalación aislada, setup y un protocolo real de segunda máquina. Las Skills nuevas se empaquetan como recursos gestionados; configuración de clientes y estado permanecen fuera del producto.

Primera plataforma: Windows x64 y PowerShell, reutilizando Python 3.13 y protección Windows existente. Requiere acceso a fuentes oficiales o un kit offline preparado. Instalación de Codex, inicio de sesión/MFA, confianza de Skills/plugins y restricciones administrativas no son automatizables de forma garantizada. El instalador del candidato puede probarse de forma explícita sin declarar release certificado. No se instala ni publica nada durante esta propuesta.
