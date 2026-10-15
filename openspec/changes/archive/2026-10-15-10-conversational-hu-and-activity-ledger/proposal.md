# Proposal

## Why

La preparación guiada debe desembocar en una HU ejecutable desde el chat sin fabricar manualmente archivos para cada comando. El SQLite actual conserva el ciclo de HU, mientras la observabilidad importa eventos externos: falta registrar automáticamente la actividad propia y hacerla consultable con su cobertura real.

## What Changes

- Añadir una fachada conversacional de `harness-hu` que reutilice la preparación de 09, recoja la historia, presente un plan revisable y conduzca comandos de ciclo, pruebas, revisión y reanudación existentes.
- Definir el papel de `AGENTS.md` como instrucciones del coordinador nativo de Codex y comprobar disponibilidad real de roles/herramientas. Cuando falte delegación o aislamiento exigido, comunicar y bloquear la fase correspondiente o ofrecer un modo supervisado explícito admisible.
- Crear durante setup una SQLite externa `activity.sqlite3`, separada de `hu.sqlite3`, para eventos automáticos de comandos propios, duración, resultados, validaciones, errores, reintentos y procedencia por cliente/checkout/HU/intento/rol.
- Añadir consulta local y exportación de actividad y consumo observado. Tokens/costos permanecen `null` con motivo cuando no hay fuente soportada y asociación comprobable; no estimarlos desde texto ni desde cuotas de cuenta.
- Ofrecer importación idempotente y extensión opcional por hooks documentados y autorizados del host, sin hacerlos requisito para actividad propia ni atribuir cobertura completa de Desktop.
- Verificar el recorrido instalación → setup → HU local → interrupción/reanudación → informe en otra máquina y con dos clientes aislados; conservar todos los gates históricos de certificación y publicación.

## Capabilities

### New Capabilities

- `conversational-hu-entrypoint`: entrada desde el chat y coordinación de HU que reutiliza identidad, configuración, aprobaciones y gates existentes.
- `local-activity-ledger`: persistencia y consulta SQLite de actividad propia, importación con procedencia y cobertura explícita de consumos.

### Modified Capabilities

Ninguna. El almacenamiento de actividad añade una fachada a `development-observability`; mantiene sus requisitos de atribución y consumo observado. `hu-lifecycle` sigue siendo autoridad de estados, aprobaciones y gates.

## Impact

Depende de las interfaces implementadas y verificadas de `09-one-command-install-and-guided-setup`. Extiende recursos `harness-hu`/Desktop, CLI, servicios de HU y observabilidad; añade un repositorio SQLite de actividad y un paso de inicialización al setup, sin migrar silenciosamente `hu.sqlite3` ni introducir otro motor LLM.

SQLite y métricas de operaciones propias son alcance obligatorio. Captura de acciones nativas ajenas al kit y tokens/costos exactos son capacidades condicionales: sin una interfaz soportada, se entrega actividad útil y diagnóstico `unavailable/partial`. Se excluyen scraping de almacenamiento interno de Codex, sustitución por un motor API, dashboard web y deploy/merge automáticos. La aceptación local nueva no sustituye las 144 evaluaciones manuales ni la aceptación remota pendientes de 06–08.
