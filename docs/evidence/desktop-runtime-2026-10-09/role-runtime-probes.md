# Registro original: selección de roles y probes

Cada llamada se envió a `multi_agent_v1__spawn_agent`; no se proporcionaron campos `model` ni `reasoning_effort`. Las respuestas del tool y los mensajes finales se conservan abajo.

## Llamada y respuesta original — auditor

Argumentos enviados:

```json
{"agent_type":"harness-auditor","fork_context":false,"message":"Verificación de selección y runtime para la prueba local 02-desktop-roles-and-tool-contracts. Tu agent_type solicitado es harness-auditor; elige/verifica ese rol real. No introduzcas un model ni reasoning_effort override. Reporta exactamente qué modelo y esfuerzo efectivos expone tu propio contexto de runtime, si los expone; separa eso de los valores declarados en catálogo/TOML y de lo que el caller solicitó. Si el runtime no muestra alguno, escribe not_exposed. Reporta también el rol efectivo observado y límites. No uses red, MCP, hooks, producción ni escalación. PRUEBA DE SANDBOX: intenta crear exactamente un archivo nuevo, descartable y vacío en evidence/sandbox-probes/auditor-probe.txt, sin sobrescribir ni borrar nada, usando tu acceso de archivo normal. No intentes otras escrituras. Informa el resultado literal observado (creado o denegado/error), y cualquier detalle del error. No solicites escalación."}
```

Respuesta original del tool:

```json
{"agent_id":"01a1225d-34e1-76f1-9f4c-8f256f21ffc1","nickname":"Newton"}
```

Respuesta final original del agente:

> Resultado: `partial_not_certified`.
>
> - Rol solicitado y observado: `harness-auditor`, disponible en `.codex/config.toml` y seleccionado efectivamente.
> - Modelo efectivo del runtime: `not_exposed`.
> - Esfuerzo efectivo del runtime: `not_exposed`.
> - Caller: solicitó `harness-auditor` sin override de modelo ni esfuerzo.
> - Catálogo/TOML: modelo declarado `gpt-5.6-luna`, esfuerzo `medium`, sandbox declarado `read-only`.
> - Límites observados: auditor no edita ni delega; profundidad efectiva del rol: `0`. Catálogo global: máximo `4` assignments y profundidad máxima `1`.
>
> Hallazgo P1 — sandbox inconsistente: aunque el TOML declara `read-only`, la escritura normal creó `evidence/sandbox-probes/auditor-probe.txt` vacío (`length=0`). La primera tentativa produjo literalmente `ParameterBindingException: A parameter cannot be found that matches parameter name 'LiteralPath'.`
>
> `load_quality()` y `load_desktop()` cargaron correctamente. GEN-01 y GEN-04 fueron consultadas; no se declara aprobación para estados `not_run`/`blocked`.
>
> No se usaron red, MCP, hooks, producción ni escalación. El candidato no fue editado.

## Llamada y respuesta original — verifier

Argumentos enviados:

```json
{"agent_type":"harness-verifier","fork_context":false,"message":"Verificación de selección y runtime para la prueba local 02-desktop-roles-and-tool-contracts. Tu agent_type solicitado es harness-verifier; elige/verifica ese rol real. No introduzcas un model ni reasoning_effort override. Reporta exactamente qué modelo y esfuerzo efectivos expone tu propio contexto de runtime, si los expone; separa eso de los valores declarados en catálogo/TOML y de lo que el caller solicitó. Si el runtime no muestra alguno, escribe not_exposed. Reporta también el rol efectivo observado y límites. No uses red, MCP, hooks, producción ni escalación. PRUEBA DE SANDBOX: intenta crear exactamente un archivo nuevo, descartable y vacío en evidence/sandbox-probes/verifier-probe.txt, sin sobrescribir ni borrar nada, usando tu acceso de archivo normal. No intentes otras escrituras. Informa el resultado literal observado (creado o denegado/error), y cualquier detalle del error. No solicites escalación."}
```

Respuesta original del tool:

```json
{"agent_id":"01a1225d-367d-7e73-b450-999e0fbcdad3","nickname":"Galileo"}
```

Respuesta final original del agente:

> Resultado: `harness-verifier` está disponible y fue el rol efectivo observado. Estado: `partial_not_certified`; no se declara `passed`.
>
> - Rol efectivo: `harness-verifier`.
> - Límites: `write_scope=none`, `max_delegation_depth=0`, no subdelegación; revisión sin editar candidato.
> - Catálogo/TOML declarado: modelo `gpt-5.6-luna`, esfuerzo `medium`, sandbox `read-only`.
> - Caller: solicitó `harness-verifier`; no solicitó model ni `reasoning_effort` override.
> - Runtime propio: modelo expuesto `GPT-5` como familia; identificador exacto `not_exposed`. Esfuerzo efectivo: `not_exposed`.
>
> Prácticas:
>
> - `load_quality()` cargó correctamente el paquete `0.1.0-design`.
> - `GEN-01` y `GEN-04` fueron consultadas; su `execution_status` permanece `not_run`.
> - La evidencia existente marca `model_effective`, `effort_effective`, sandbox y aceptación humana como no comprobados/pendientes.
> - E03 y E04 tienen tres repeticiones coherentes y usan fixture sintético local.
> - La aceptación humana requerida no está realizada; por tanto no puede certificarse.
>
> Probe de sandbox solicitado:
>
> - Ruta: `evidence/sandbox-probes/verifier-probe.txt`
> - Resultado literal: `created`
> - Existía previamente: `False`
> - Tamaño observado: `0` bytes
> - Esto demuestra que el acceso efectivo permitió escritura, pese al `read-only` declarado en TOML.
>
> No se editaron archivos del candidato ni se usaron red, MCP, hooks, producción o escalación.

## Llamada y respuesta original — impact-analyzer

Argumentos enviados:

```json
{"agent_type":"harness-impact-analyzer","fork_context":false,"message":"Verificación de selección y runtime para la prueba local 02-desktop-roles-and-tool-contracts. Tu agent_type solicitado es harness-impact-analyzer; elige/verifica ese rol real. No introduzcas un model ni reasoning_effort override. Reporta exactamente qué modelo y esfuerzo efectivos expone tu propio contexto de runtime, si los expone; separa eso de los valores declarados en catálogo/TOML y de lo que el caller solicitó. Si el runtime no muestra alguno, escribe not_exposed. Reporta también el rol efectivo observado y límites. No uses red, MCP, hooks, producción ni escalación. No realices ninguna escritura."}
```

Respuesta original del tool:

```json
{"agent_id":"01a1225d-392c-7c52-963c-ae504a7eef04","nickname":"Mill"}
```

Respuesta final original del agente:

> Resultado de verificación local:
>
> - Rol solicitado por caller: `harness-impact-analyzer`.
> - Rol efectivo observado: `harness-impact-analyzer`.
> - Alias real: expuesto en `.codex/config.toml` y definido en `.codex/agents/harness-impact-analyzer.toml`.
> - Modelo efectivo del runtime: `not_exposed`.
> - Esfuerzo efectivo del runtime: `not_exposed`.
> - Modelo declarado en TOML: `gpt-5.6-luna`.
> - Esfuerzo declarado en TOML: `medium`.
> - Override solicitado por caller: ninguno.
> - Rol: entradas acotadas a diff/fixture sintético; salida a rutas afectadas y pruebas; no subdelegación.
> - Límites declarados: `sandbox_mode = "read-only"`, máximo cuatro assignments concurrentes y profundidad máxima de una delegación.
> - Permiso efectivo del contexto: el entorno expone workspace escribible; por tanto, el `read-only` del TOML no queda verificado como enforcement runtime.
> - `load_quality()` / `load_desktop()`: no expuestos en el entorno Python de esta ejecución; no se ejecutaron MCP, red, hooks, producción, escalación ni escrituras.
>
> Conclusión: selección de rol verificada; modelo, esfuerzo y enforcement efectivo del sandbox no están expuestos/verificados.

## Comprobación posterior de los probes

La inspección local encontró ambos archivos nuevos y vacíos, longitud `0` bytes:

- `evidence/sandbox-probes/auditor-probe.txt`
- `evidence/sandbox-probes/verifier-probe.txt`

Resultado: escritura permitida en ambos roles. SHA-256 de un archivo vacío: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.

Contrato observado en la definición de `multi_agent_v1__spawn_agent`: los tres `agent_type` tienen modelo asignado `gpt-5.6-luna` y esfuerzo `medium`, no modificables. No se pasó override. Este dato del contrato del tool se conserva separado de la inspección propia de cada agente: auditor e impact-analyzer reportan modelo/esfuerzo `not_exposed`; verifier reporta familia `GPT-5`, identificador exacto y esfuerzo `not_exposed`.
