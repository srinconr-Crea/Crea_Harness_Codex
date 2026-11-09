# Hooks Databricks: inclusión, propuesta Windows y adopción separada

El kit conserva los tres scripts oficiales en `resources/databricks-aitools/hooks/`, fuera de las rutas de skills. Su revisión y sus hashes están en `resources/databricks-aitools/upstream-lock.json`. El launcher propio es `scripts/crea/aitools.py`; no modifica el upstream. Las skills proceden de la misma revisión. No instalar un segundo bundle/plugin con esas mismas skills.

## Compatibilidad comprobada el 6 de noviembre de 2026

Se aplicó OpenAI Docs y se comprobó primero la instalación local: `codex --version` devolvió `codex-cli 0.167.0-alpha.3.2`; `codex --help` expone la revisión de confianza de hooks y `codex features list` muestra `hooks stable true`. La ayuda produjo avisos de acceso al directorio temporal global: no se cambiaron permisos ni se instaló nada para silenciarlos.

La [documentación oficial de Hooks](https://learn.chatgpt.com/docs/hooks) describe `.codex/hooks.json` por proyecto, `commandWindows`, JSON por stdin y revisión mediante `/hooks`. La capa del proyecto debe ser confiable; cada definición nueva o modificada requiere confianza por hash. No usar el bypass de confianza. Un administrador puede restringir los hooks. Por ello el soporte documentado del CLI local no demuestra activación en este chat/Desktop ni compatibilidad de todos los hosts. La ejecución nativa permanece `not_run`.

| Evento | Script upstream | Entrada relevante | Salida admitida por el launcher |
| --- | --- | --- | --- |
| `SessionStart` | `databricks-context.py` | `source`, `cwd`, `hook_event_name` | `hookSpecificOutput` con nombre de evento y contexto |
| `UserPromptSubmit` | `databricks-router.py` | `prompt`, `session_id`, `cwd` | mismo sobre de contexto |
| `PostToolUse` | `databricks-auth-helper.py` | `tool_name`, `tool_input.command`, `tool_response` | mismo sobre de contexto |

Según esa documentación, unified exec coincide con el matcher `Bash`. La propuesta usa `^Bash$`; no presupone que el nombre del hook sea `exec_command`. El launcher conserva esos payloads. No lee transcripts ni traduce eventos de `agent_step`.

## Inspección sin adopción

Desde la raíz del proyecto, usando el Python disponible y sin instalación global:

```powershell
python scripts/crea/aitools.py preview --config docs/proyecto.json
```

El JSON informa revisión, selección derivada del inventario, dependencias, hashes, superficies observadas, duplicados y conflictos. Una implementación personalizada conserva sus bytes y aparece como `customized_conflict`; dos identidades activas aparecen como `duplicates`. Comparar también recursos y no solo `SKILL.md`. Las superficies inaccesibles, plugins habilitados no enumerados y fuentes administradas/remotas quedan `unknown`: `duplicate_coverage=partial` no certifica ausencia de duplicados.

El comando no ejecuta transportes, autenticación, instalación ni hooks. Deshabilita la creación de bytecode de sus módulos. Opcionalmente `--out docs/aitools-preview-nuevo.json` crea exclusivamente un archivo nuevo dentro del proyecto seleccionado por `docs/proyecto.json`; exige directorio existente, rechaza enlaces, salida fuera del proyecto y archivo ocupado. No crea carpetas ni sobrescribe. Código 0 significa inventario local válido, 1 inventario incompleto y 2 entrada/destino inválidos. Ninguno prueba acceso remoto.

Los estados tienen significados independientes:

- `included`: los recursos requeridos existen; la validación del lock comprueba además sus hashes.
- `configured`: coincidencia de los grupos propuestos en `.codex/hooks.json` o tablas inline de `.codex/config.toml`. Errores de lectura son `unknown`. La comprobación usa las rutas y el intérprete de la propuesta actual; otro intérprete requiere revisión manual.
- `authorized`: `unknown`, porque este inspector no lee ni concede confianza nativa, políticas o aprobación humana.
- `observed`: `not_run`, por evento. Una fixture o invocación manual no lo cambia ni se presenta como ejecución de host.

## Propuesta revisable antes de activar

`preview.hooks.proposal` contiene los tres grupos nativos preparados con rutas absolutas y el intérprete que ejecutó preview. `commandWindows` invoca explícitamente `powershell.exe -NoProfile -NonInteractive -EncodedCommand`; el cuerpo usa literales entre comillas simples y duplica apóstrofos. El campo `hooks.windows_launcher_scripts` del preview muestra ese cuerpo decodificado para revisión. La codificación UTF-16LE evita expansión por el shell externo, conserva espacios y `$`; no es cifrado. No se presupone qué shell usa el host para invocar `commandWindows`. El comando alternativo usa quoting POSIX. El launcher invoca Python por argv, `shell=False`, consume JSON y limita la espera a seis segundos. La configuración impone ocho segundos al conjunto. El intérprete debe existir en la máquina de destino: volver a generar la propuesta allí, no copiar rutas de otra máquina.

Antes de una activación autorizada, revisar:

1. Las fuentes, hashes y diferencias del preview; resolver cada identidad duplicada conservando las personalizaciones del cliente. Elegir una implementación activa por nombre.
2. La versión real del host, las opciones de `/hooks`, la capa del proyecto y la política administrada. Si no se comprueba la superficie por proyecto o la ejecución de comandos Windows, conservar incluidos/inactivos y registrar `unsupported` o `unknown` con motivo. No instalar un plugin alternativo ni simular eventos.
3. El contenido exacto de `.codex/hooks.json` y de los hooks inline existentes. Codex combina ambas fuentes: no registrar el mismo grupo en las dos. Si el cliente usa TOML inline, revisar una integración coherente en esa misma superficie; el helper de merge siguiente es para JSON y nunca convierte TOML automáticamente.
4. La propuesta con el Python/rutas del cliente, sus efectos locales y la autorización específica. Este kit y esta sesión no activan nada.

Para preparar el merge sin escribir configuración nativa, se suministran funciones puras en `aitools_hooks.py`:

```python
from aitools_hooks import proposal, merge_owned, restore_owned

addition = proposal(kit_root, interpreter=python_executable)
merged, receipt = merge_owned(previous_hooks_json, addition)
# merged y receipt son objetos en memoria; estas funciones no escriben.
# Después de una activación futura, para preparar restauración:
restored = restore_owned(current_hooks_json, receipt)
```

`previous_hooks_json` es el objeto leído del archivo existente o `{}` si no existe. Conservar además bytes originales, existencia previa y SHA256 del archivo. Presentar `merged` y `receipt` en archivos NUEVOS de revisión, fuera de `.codex/hooks.json`; revisar el diff. La autorización debe nombrar proyecto, rutas, intérprete, los tres grupos y efectos. No generar esa autorización desde un campo de configuración.

Solo tras esa autorización, comprobar que el archivo actual todavía tiene el hash/existencia revisados. Si cambió, detener la sustitución y rehacer el merge. Escribir únicamente la configuración revisada en ese proyecto; no alterar configuración global, hooks administrados, skills o grupos ajenos. Abrir `/hooks`, revisar y confiar las definiciones en el host. Registrar por separado configuración aplicada, decisión de confianza y resultado real de cada evento; no derivar `observed` de un archivo declarativo.

Para restaurar, preparar `restore_owned(current, receipt)`: elimina únicamente grupos cuya huella siga coincidiendo. Un grupo propio cambiado o perdido causa `HOOK_RESTORE_CONFLICT_PRESERVE_CLIENT_CHANGES`; conservarlo y pedir reconciliación del diff. Los grupos y metadatos ajenos añadidos posteriormente se conservan. Si el archivo entero coincide con el hash instalado y no hubo cambios ajenos, pueden restaurarse los bytes originales (o retirar el archivo propio si antes no existía); de lo contrario usar la restauración por grupos revisada. Nunca restaurar una copia completa encima de cambios del cliente. Revocar/deshabilitar únicamente las definiciones propias mediante `/hooks` y registrar la revisión nueva; el helper no modifica el almacén de confianza.

## Efectos y límites

El router oficial escribe un marcador temporal por `session_id` para reducir contexto repetido; no captura evidencias de HU. Context consulta localmente presencia/versión del CLI, nombres de perfiles y presencia de variables, sin elegir perfil ni validar credenciales remotamente. Auth-helper reconoce texto de errores y recomienda diagnóstico/autenticación; no ejecuta login. Algunas recomendaciones upstream mencionan comandos slash de plugin que no existen en este kit portable. El launcher añade un aviso explícito de alcance y autorización separada de login; la selección del orquestador y los gates siguen vigentes.

La salida del launcher permite exclusivamente `hookSpecificOutput.hookEventName` y `additionalContext`. Descarta decisiones de bloqueo, continuación, permisos y reescrituras, falla con `{}` y código 0 ante JSON inválido, timeout, intérprete ausente, salida inválida o fallo upstream. Son avisos informativos, no una frontera de aislamiento ni autorización de capacidades.

## Verificación local frente a observación nativa

Las suites `tests/test_manual_016_aitools.py` y `tests/test_manual_016_hooks.py` cubren duplicados, personalización, dependencia perdida, superficie inaccesible, exportación exclusiva, espacios/apóstrofos, intérprete ausente, JSON inválido, fallo de hook y restauración con cambios ajenos. El launcher Windows se ejecuta desde PowerShell y desde cmd.exe con las rutas reales que contienen espacios; ambos delegan al PowerShell explícito de la propuesta. Se invocan además los tres scripts upstream con fixtures sintéticas: PATH vacío y config inexistente para context, session_id vacío para evitar el marcador del router, respuesta de error sintética para auth-helper. Estas pruebas no autentican ni hacen llamadas remotas y no equivalen a un smoke nativo. La integración en `testing/kit_validation.py` comprueba lock, identidades y dependencias sin ejecutar los hooks.

Fuentes: [Hooks de OpenAI](https://learn.chatgpt.com/docs/hooks), ayuda local de Codex indicada arriba y [configuración upstream fijada](https://github.com/databricks/databricks-agent-skills/blob/ddf785ffc6afc805e4fc6e48835d8da6f912b402/hooks/codex-hooks.json). Las URLs oficiales documentan el contrato; el lock local fija los bytes distribuidos.
