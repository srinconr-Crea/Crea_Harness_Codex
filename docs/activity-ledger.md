# Actividad local y entrada conversacional

El cambio 10 registra comandos propios en `<state_dir>/activity.sqlite3`, fuera
del checkout y separado por binding cliente/checkout. `hu.sqlite3` conserva la
autoridad de estados, aprobaciones, candidatos y gates. La base de actividad no
autoriza acciones ni reemplaza los journals de los adaptadores.

## Inicio desde chat

Invocar `harness-hu` con una historia textual. Codex reutiliza la preparación de
setup 09 y pregunta criterios, rutas, operaciones y tests que falten. Resuelve el
runtime verificado de instalación y usa opciones tipadas; no exige JSON manuales.

```powershell
harness work preview --path TARGET --policy POLICY --binding BINDING --story HU1 --story-text "Sumar cantidades sintéticas" --writer principal --criterion "Suma exacta para vacío y decimales" --scope harness_pilot/total.py --scope harness_pilot/test_total.py --change create --test T16 --mode supervised_single_agent --available-model MODELO:EFFORT --json
```

Reemplazar MODELO:EFFORT por el perfil seleccionado y disponible. Preview devuelve
preguntas o un plan con hash; no crea HU ni bases. Presentar ese plan. Tras
autorización humana del hash vigente, repetir las opciones con `work start` y
`--authorize SHA`. Los contratos generados entran al ciclo HU existente.
`--plan-out FILE` es una exportación explícita y exclusiva del preview.

`supervised_single_agent` permite implementación local admisible, con cero
delegaciones. No satisface revisión independiente. En modo nativo comprobar
delegación y modelo/esfuerzo; cuando la fase exige independencia, observar también
aislamiento. Booleanos y nombres de actor no acreditan ejecución. La Skill registra
referencias de tareas reales y conserva `not_run` donde falte evidencia.

```powershell
harness work status --path TARGET --policy POLICY --binding BINDING --story HU1 --json
harness work resume --path TARGET --policy POLICY --binding BINDING --story HU1 --operation resume-1 --json
```

Status presenta próxima acción, aprobación vigente, contexto/candidato efectivo y
estados local/remoto/publicación. Resume revalida preparación, binding, política,
base y pending del ciclo; no reinicia límites ni fabrica evidencia. Cambios de
contexto invalidan aprobación; cambios de candidato invalidan pruebas afectadas.
Implementación, candidato, validación, revisión y cierre continúan mediante
`harness hu` y los adaptadores existentes. PR y deploy requieren sus autorizaciones
y gates propios. No se invocan desde `work start`.

## Consulta y significado de métricas

```powershell
harness activity status --path TARGET --policy POLICY --binding BINDING --json
harness activity report --path TARGET --policy POLICY --binding BINDING --hu HU1 --attempt 1 --json
harness activity export --path TARGET --policy POLICY --binding BINDING --hu HU1 --out REPORT.json --json
```

También hay filtros `--role`, `--since` y `--until`, con timestamps ISO y zona.
Status/report abren SQLite en modo `ro`; no crean archivos, migran ni incrementan
contadores. Una base ausente devuelve `ledger_missing`. Export crea exclusivamente
el destino explícito y conserva procedencia; un archivo existente no se sobrescribe.
La selección valida el checkout y el binding antes de abrir la base.

`counts` muestra eventos deduplicados, `incomplete_operations` inicios sin resultado,
`incomplete_durations` operaciones sin duración completa, `failed_operations` y
`blocked_operations` resultados reales. Duración usa reloj monotónico únicamente
en el proceso que ejecutó el efecto. UTC ordena eventos; no reconstruye tiempo de
un proceso perdido. Comandos y milisegundos son actividad, nunca consumo LLM.

Tokens/costo Desktop permanecen `null` con
`supported_attributable_source_unavailable`. `usage` conserva recibos CLI
soportados declarados, con sesión, referencia documental, asociación, unidades y
periodo. No son facturación Desktop. La versión actual no admite importar costo
facturado, cuota global ni estimaciones por texto. Recibos superpuestos generan
`measurement_conflicts`; no se suman. Unidades/monedas no admitidas se rechazan.

## Esquema y recuperación

Esquema SQLite 2: `ledger_metadata`, `operations`, `activity_events`,
`usage_observations` y `coverage`. Contratos JSON de entrada son versión 1,
publicados con prefijo `ledger-` para preservar los schemas de observabilidad v1.
Metadata fija client_id, checkout_id y fingerprint completo del binding. Reutilizar
una base con otra identidad falla; mover equipo requiere binding nuevo y estado
separado. No hay downgrade ni migración automática.

Setup autorizado inicializa la base antes de sus etapas y antes de la primera HU;
su preview declara el efecto sin crearlo. Para clientes existentes:

```powershell
harness activity init --path TARGET --policy POLICY --binding BINDING --json
harness activity migrate --path TARGET --policy POLICY --binding BINDING --out BACKUP.sqlite3 --json
```

Init importa una vez el journal propio del setup seleccionado, si existe, sin
imputar HU ficticia. Su timestamp es recepción/importación, no fecha histórica
reconstruida; duración desconocida es null. Una migración 1→2 guarda un snapshot
exclusivo antes de cambiar índices/versionado; esquemas desconocidos se rechazan.
No se modifica `hu.sqlite3` durante init, consulta o migración.

Cada operación persiste inicio antes del efecto, con espera SQLite de 250 ms.
`ledger_busy`/`ledger_unavailable` impiden una mutación nueva. Resultado perdido
deja inicio pendiente. Setup reconcilia una etapa completada desde su journal y
HU desde su evento transaccional, sin repetir el efecto confirmado. Proceso
interrumpido no inventa resultado ni duración. Operaciones genéricas pendientes
requieren reconciliar el journal del adaptador antes de repetirlas.

Adaptadores de validación admiten `activity_context` explícito con selección,
operation_id y HU/intento/rol cuando corresponda; las consultas no lo admiten.
Publicación/distribución conservan sus journals y aceptan contexto seleccionado.
Una instalación global sin cliente conserva su journal global; no se atribuye a
todas las HU. Eventos/payloads son tipados, limitados y redactados antes de insertar:
no conversación, contenido de archivos, stdout crudo ni secretos.

## Hooks opcionales

El adaptador empaquetado `harness_local.activity_hooks` acepta `PostToolUse` mediante
stdin acotado. Consume solamente identidad de sesión/cwd/tool-call y una asociación
cliente/checkout/HU/intento confirmada externamente; descarta argumentos, respuesta
y transcript_path. `tool_operations` asocia explícitamente una llamada a una
operación propia para excluirla del conteo duplicado. Otra sesión/checkout se rechaza.

Según la [documentación oficial de hooks](https://learn.chatgpt.com/docs/hooks),
la configuración local requiere revisión/confianza del host. Inspeccionar `/hooks`
y confiar la definición exacta manualmente. El módulo verifica además el SHA de la
definición seleccionada; nunca habilita confianza ni edita configuración global.
La asociación y el comando deben usar rutas absolutas del runtime instalado:

```powershell
PYTHON -m harness_local.activity_hooks --path TARGET --policy POLICY --binding BINDING --association ASSOCIATION.json --definition HOOKS.json --trusted-sha256 SHA
```

Configurar ese comando como handler de `PostToolUse` según el formato oficial y
revisar tanto el script instalado como la definición. Cambios requieren nueva
revisión. No activar hooks para consultas si se busca excluir también esas llamadas
nativas; la actividad propia siempre excluye sus consultas.

Matriz de diagnóstico: comandos propios `enabled`; imports `submitted_events_only`;
hooks sin configuración confiada `native_actions_not_observed`; evento compatible
recibido `documented_events_observed_partial`; tokens/costo Desktop `unavailable`.
`diagnose()` comprueba eventos declarados, script presente y confianza informada,
sin afirmar que el host lo ejecutó. La ausencia de hooks no bloquea la base propia.

```powershell
harness activity diagnose-hooks --path TARGET --policy POLICY --binding BINDING --json
```

Sin una declaración explícita seleccionada con `--input`, el diagnóstico devuelve
`native_actions_not_observed`; no inspecciona bases ni conversaciones internas.

Los agentes standalone requieren `name`, `description` y `developer_instructions`;
heredan permisos del padre. Véase [Subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents).
Instrucciones, perfiles y hooks no restringen por sí mismos las herramientas.

## Límites de aceptación

Pruebas locales y dobles no sustituyen otra máquina, otro chat real, OAuth,
aislamiento Desktop ni las 144 evaluaciones manuales pendientes de 06–08.
Archivo administrativo, commit y push no habilitan certified/release/publicación.
Consultar la evidencia específica del incremento antes de atribuir aceptación.
