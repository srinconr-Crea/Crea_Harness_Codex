# Design

## Context

Ver `proposal.md` para motivación. `hu.py` crea `hu.sqlite3` y conserva runs/events/pending del ciclo de HU; sus gates de identidad, plan/candidato y recuperación ya están implementados. `observability_service.py` lee eventos/UsageInput externos y produce reportes, sin persistir una base de consumos. El adaptador `desktop_usage` devuelve datos no disponibles cuando falta una fuente atribuible soportada. Los recursos Desktop son instrucciones/configuración; la activación real se prueba aparte.

09 aporta registro de runtime, setup de herramientas y contrato positivo de rutas. Este cambio depende de esas interfaces verificadas, no de un release certificado de 08. Extiende las pruebas de `test_hu_cli.py`, `test_observability.py`, integración Desktop y onboarding, conservando contratos/evidencia históricos.

## Goals / Non-Goals

**Goals:**

- Hacer que la Skill conduzca una HU con contratos generados y estado persistido sin repetir setup ni depender de memoria del chat.
- Registrar automáticamente actividad propia útil desde la preparación y consultarla mediante una SQLite local externa.
- Mantener trazabilidad, fallos, procedencia y cobertura sin afirmar uso/costo que no se observa.

**Non-Goals:**

- Construir otro coordinador LLM, garantizar disponibilidad de todos los modelos/roles o aislar subagentes mediante instrucciones.
- Obtener secretos, inspeccionar bases internas de Codex, estimar tokens por caracteres o equiparar cuotas globales a una HU.
- Proporcionar dashboard web, capturar necesariamente toda acción nativa, ejecutar deploy/merge o aprobar gates reales con dobles.

## Decisions

### 1. Skill como interfaz, ciclo existente como autoridad

Actualizar la Skill de proyecto `harness-hu` y el bloque gestionado de AGENTS para: resolver binding/runtime → verificar preparación vigente → recoger HU → generar plan → presentar revisión → registrar autorización existente → conducir adaptadores y evidencias → reportar estado. Proponer fachada `harness work preview|start|resume|status` que genera entradas de los comandos existentes, sin reemplazar el servicio HU ni duplicar su máquina de estados.

La HU en texto aporta intención; criterios, rutas y validaciones ambiguos se preguntan. Referencias a Jira/GitHub se consultan solo con herramientas y acceso disponibles. Las selecciones heredadas tienen procedencia y hash; cambio de política/checkout/modelo/capacidad relevante exige revalidación. Los contratos temporales generados se guardan en estado externo autorizado, nunca secretos ni instrucciones del producto cliente en perfil global.

La aprobación no cubre efectos futuros indefinidos: reutilizar autorización vigente dentro de la revisión y solicitar revisión nueva ante drift. PR/publicación siguen adaptadores y gates existentes; ninguna prueba local crea un PR de manera automática. Reanudación lee `hu.sqlite3` y pending, comprueba Git/binding/candidato y reconcilia antes de volver a ejecutar efectos.

Alternativas descartadas: un script que invoque otro LLM duplica Codex; una Skill que solo enumere comandos deja intacta la carga manual del usuario; guardar todo en memoria conversacional pierde recuperación entre chats.

### 2. Roles nativos y modos explícitos

Conservar los ocho roles y sus perfiles autorizados. El coordinador nativo dirige roles/herramientas cuando están disponibles y registra evidencia de ejecución real con identificador de tarea o referencia comprobable. Si no hay delegación, puede proponerse un modo principal supervisado cuando la fase no exige independencia; se etiqueta `supervised_single_agent`, no se fabrica una revisión independiente. Fases que exigen aislamiento o independencia quedan bloqueadas si no se observan.

Modelos/effort se comprueban en el host y no se sustituyen silenciosamente. AGENTS aporta instrucciones, no un ejecutable; los agentes heredan permisos del padre. La política positiva de 09 restringe operaciones propias y el gate detecta diff externo fuera del plan. Garantías más fuertes requieren restricciones del host. Referencia: [Subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents), consultada 2026-10-14.

### 3. SQLite separada y cobertura mínima obligatoria

Crear `<state_dir>/activity.sqlite3` durante apply de setup; mantener `<state_dir>/hu.sqlite3` sin migración silenciosa. Raíces externas verificadas mediante las garantías Windows del kit, nunca dentro del repo, enlazadas ni compartidas entre identidades distintas. `sqlite3` de la biblioteca estándar evita un servidor y dependencias nuevas. Esquema con `user_version`, migración explícita respaldada y transacciones locales acotadas; WAL solo en filesystem local compatible y busy timeout acotado.

Tablas propuestas:

| Tabla | Contenido/garantía |
| --- | --- |
| ledger_metadata | versión, client_id, checkout_id y binding fingerprint |
| operations | operation_id, ámbito setup/HU, hu_id/attempt/role nullable, inicio/fin UTC, elapsed_ms nullable, status/result, revisión/candidato y source |
| activity_events | event_id, operation_id, idempotency_key única por source e identidad, tipo, timestamp y payload tipado redactado/acotado |
| usage_observations | fuente/source_event_id únicos, unidades/alcance, asociación, tokens/costo nullable, currency nullable, unavailable_reason y evidencia de procedencia |
| coverage | fuente/capacidad, enabled/observed/not_available, versión/periodo y motivos |

Identificadores HU/rol nulos se admiten para setup y comandos del coordinador sin atribución a un rol especializado. No registrar una HU ficticia ni deducir el modelo ejecutado desde su configuración. Duración se mide con reloj monotónico en la operación; UTC aporta orden/calendario, no se reconstruye una duración exacta de un proceso muerto. Actividad automática abarca comandos mutantes y ejecutores propios; previews/consultas no escriben en la base ni inflan contadores. Los eventos de preparación anteriores a crear la base se importan del journal propio una vez con su procedencia.

Integrar un wrapper común alrededor de adaptadores de setup/HU/validación/historia-PR/distribución que ya aceptan identidad o un contexto explícito. Operaciones globales de instalación sin cliente mantienen journal de instalación y no se imputan automáticamente a todas las HU. Escribir inicio antes del efecto; si no puede persistirse, no iniciar mutación nueva. Persistir resultado después del efecto; fallo después del efecto queda visible en journal/pending propio y obliga reconciliación, no a repetirlo. `hu.sqlite3` sigue siendo autoridad: no existe atomicidad ficticia entre las dos bases y un sistema remoto.

### 4. Contratos y consultas

Añadir `ActivityEvent`, `LedgerQuery`, `LedgerReport` y `UsageObservation` versionados. Entrada tipada tiene source, identidad/ámbito, idempotency_key, timestamp y campos allowlist. Se valida límite de payload, asociación y redacción antes de persistir; rechazar SQL libre del usuario y no guardar conversación, contenido de archivos o stdout crudo.

Proponer `harness activity status|report|import|export` con filtros cliente/checkout/HU/intento/rol/periodo; salida humana y JSON. Reporte muestra conteos deduplicados, duraciones completas, pendientes, fallos, reintentos y cobertura. `status/report` abre SQLite en read-only sin crear archivo, sin migrar ni escribir eventos. Export usa creación exclusiva del destino solicitado, redacta y conserva procedencia. Reutilizar validadores de observabilidad existentes para imports; reject mismatch no se convierte en evento del cliente equivocado.

Errores adicionales: `ledger_missing`, `ledger_identity_mismatch`, `ledger_busy`, `ledger_unavailable`, `ledger_schema_unsupported`, `event_invalid`, `usage_unattributable`, `native_source_unavailable`. Mantener categorías de fachada definidas en 09 y motivos estructurados. `ledger_missing` en consulta es diagnóstico, nunca inicialización implícita; fallos de almacenamiento bloquean nuevas mutaciones cubiertas, no la consulta/reparación de estado existente.

### 5. Consumo observado con ausencia explícita

Campos de tokens y costo admiten null de manera independiente, con fuente, unidades, moneda, alcance, asociación verificada y unavailable_reason. Una duración o número de comandos es actividad, no consumo LLM. El reporte no suma observaciones de alcances superpuestos (sesión total + eventos hijos) ni agrega monedas/unidades incompatibles; marca conflictos de medición.

Desktop mantiene `supported_attributable_source_unavailable` cuando no hay una interfaz documentada que entregue esos valores asociables al cliente/HU. Se preserva la importación manual soportada con procedencia; datos de un proveedor API pueden registrarse solo en su ámbito API y jamás como facturación Desktop. Cuotas de cuenta sirven como información global si se muestran aparte, no como registros de consumo de HU.

La falta actual de una fuente atribuible es un resultado admitido, no una tarea interminable de buscar interfaces privadas. Captura automática de comandos propios y SQLite son obligatorias; consumo exacto condicional cumple su contrato devolviendo null/motivo y evidencia del diagnóstico.

### 6. Hooks opcionales y confianza del host

Añadir adaptador opt-in para eventos documentados del host cuando existan y la definición esté revisada/confiada por el usuario. Los hooks no son necesarios para registrar comandos propios; pueden aportar eventos nativos con identidad comprobada, fuente separada y deduplicación. Eventos no atribuibles quedan rechazados o en diagnóstico de cobertura, sin imputarlos a la HU activa por proximidad temporal.

Implementar un paquete local mínimo de hooks con scripts en el host, apoyado en la distribución del runtime; no confundir instalar archivos con habilitar/confíar. La documentación oficial indica confianza separada y que instalar un plugin en web no despliega scripts al host. Para versiones no compatibles, entregar `native_actions_not_observed` y flujo de importación, sin editar archivos internos de Codex. Si el esquema documentado carece de tokens, los hooks no se convierten en fuente de tokens. Referencias: [Hooks](https://learn.chatgpt.com/docs/hooks) y [Package your plugin](https://developers.openai.com/plugins/build/plugins), consultadas 2026-10-14.

## Risks / Trade-offs

- Dos almacenes y efectos remotos no son transacción única → operation_id/journal previos, estados pendientes y reconciliación sin duplicar efectos.
- SQLite bloqueada o disco lleno → espera acotada, error explícito y bloqueo de nuevas mutaciones cubiertas; no marcar trazabilidad completa.
- Hooks duplican eventos propios o no cubren herramientas → source y operation_id, deduplicación y cobertura visible; excluir de sumas datos superpuestos.
- Roles configurados pero no ejecutados → evidencia nativa ligada a identidad; modos supervisados explícitos y fase bloqueada cuando requiere independencia.
- Usuario espera factura exacta de Codex → tokens/costos null con motivo verificable; nunca estimaciones encubiertas.
- Trazabilidad contiene datos sensibles → allowlist/redacción previa, permisos locales, retención/exportación explícitas; no logs de conversación.

## Migration Plan

1. Implementar 09 y validar sus interfaces locales; añadir esquema/repositorio de actividad con inicialización explícita para clientes existentes y primer setup.
2. Instrumentar operaciones propias e importar journals previos de setup idempotentemente; comprobar que `hu.sqlite3` conserva estados.
3. Actualizar Skill/AGENTS mediante planes de integración gestionados, preservando personalizaciones y v1.
4. Activar opcionalmente el adaptador de hooks solo tras detección y confianza; su ausencia deja operativa la base de actividad propia.
5. Probar en segunda máquina: invocar setup antes del cliente, crear dos clientes, ejecutar HU local, interrumpir/reanudar desde otro chat y consultar/exportar SQLite. NaturaPet se usa como piloto seleccionado externamente con datos sintéticos y sin deploy/merge/recursos reales implícitos.
6. Conservar evidencias reales separadas de dobles. La aceptación de este recorrido no satisface automáticamente las 144 ejecuciones not_run, certificación remota ni release de 06–08. Rollback de recursos gestionados preserva bases/journals/evidencia; un esquema no compatible se informa sin downgrade destructivo.
