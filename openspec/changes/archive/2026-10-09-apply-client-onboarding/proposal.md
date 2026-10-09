# Proposal

## Why

La base 0.1.0 valida y muestra un onboarding, pero exige un binding escrito manualmente y deja la preparación OpenSpec pendiente. Necesitamos preparar un checkout cliente mediante un plan revisable, aplicar solo sus archivos autorizados y recuperar una ejecución interrumpida sin mezclar producto, cliente y estado personal.

## What Changes

- Extender `init --dry-run` para proponer un binding nuevo a partir de datos explícitos y exportar opcionalmente un plan versionado mediante `--plan-out`.
- Añadir `init --apply --plan FILE`: revalidar entradas, identidad, permisos y precondiciones antes de crear los archivos ausentes previstos, preservando todo archivo existente.
- Incorporar contenido OpenSpec genérico, fijado a 1.13.2 y verificable, para configuración y siete Skills. Validar primero su generación oficial en un entorno temporal aislado; runtime consumirá recursos empaquetados, sin instalaciones.
- Registrar ejecución y hashes en JSON fuera del checkout, con exclusión mutua, operaciones recuperables e informe de doctor al finalizar.
- Añadir recuperación explícita que elimine únicamente archivos creados por esa ejecución que sigan intactos; conservar modificaciones posteriores del desarrollador.
- Mantener revisión manual de AGENTS personalizado, configuración Codex y autenticación. Las escrituras previstas deberán estar admitidas por la política explícita.
- Compatibilidad: `init --dry-run` existente y sus contratos v1 se conservan. `init` sin modo explícito sigue rechazado. Exportar el plan será una escritura solicitada aparte del preview read-only.

## Capabilities

### New Capabilities

- `onboarding-application`: aplicación local de un plan acotado, revalidado e idempotente, con preparación OpenSpec y reporte final.
- `onboarding-recovery`: registro por ejecución, bloqueo concurrente y recuperación conservadora tras fallo o interrupción.

### Modified Capabilities

- `onboarding-preview`: binding propuesto, contenido OpenSpec determinado y exportación explícita del plan; preservar los escenarios existentes y la ausencia de efectos del preview sin exportación.

## Impact

Afecta `harness_core` (contratos del plan, validación de destinos y autorización de operaciones), `harness_local` (preview, CLI, aplicador/registro/recuperación), recursos empaquetados y pruebas. Se mantienen los contratos descriptor/política/binding v1 y doctor read-only. Se actualizarán README y guías durante apply.

No incluye clonado, instalador/plugin, cambios globales de Codex, modelos/agentes/hooks operativos, SQLite, ejecución de tests del cliente, autenticación ni operaciones remotas. El resultado prepara archivos locales; no certifica funcionamiento de Desktop ni Databricks. Este cambio solo autoriza planificación hasta que el usuario solicite apply.
