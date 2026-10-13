# Onboarding guiado del cliente

`harness onboard` acepta una plantilla QuestionnaireDraft v1 o la misma estructura
rellenada durante una entrevista con la Skill `harness-client-onboarding`.
El operador elige explícitamente cliente, checkout, políticas, roles/modelos y
referencias de herramientas. No se ejecutan respuestas como comandos.

La plantilla distribuida está en
`src/harness_local/guided_kit/questionnaire.json`. Cada answer contiene value,
status (`known`/`unknown`), source (`user`/`template`/`local`) y confirmed.
`unknown` usa null y confirmed=false. Los campos requeridos son target_path,
policy_path, binding_path, development, tool_binding y catalog; binding_mode,
repository, base_branch, state_dir y development_policy_path son opcionales.
Para binding_mode=proposed, state_dir, repository y base_branch son necesarios.
Una lista de posibles targets produce pregunta de selección y bloquea efectos.
Las observaciones locales tienen source=local, confirmed=false y no se convierten
en autorización. Con plantilla completa no se repiten decisiones ya confirmadas.

Ejemplo mínimo de respuesta:

```json
{"value":"C:/Clientes/alpha","status":"known","source":"user","confirmed":true}
```

Development lleva schema_version=1, client_id, stack, conventions, business_rules,
roles, validations y sources. Por ejemplo, roles=["auditor"], validations=["pytest"].
Business_rules pertenece al cliente, nunca al kit genérico. Sources conserva la
procedencia del contexto, mientras la entrevista conserva cada selección completa.
Tool_binding lleva schema_version=1, client_id, checkout_id y tools. Cada tool
tiene id, kind (local/cli/mcp/skill), connection_ref (identificador o null) y status
(declared/unavailable/not_checked). No admite credenciales, URLs como referencias,
autenticación ni afirmaciones de disponibilidad observada por mero registro.
Catalog es RoleCatalog del 02, con selección explícita de perfiles disponibles
revisada por el operador; roles activados deben coincidir con development.roles.
El CLI no consulta ni certifica disponibilidad de modelos de la cuenta.

Los schemas están en `schemas/` y en el wheel. La carpeta de recursos incluye una
plantilla completa sintética validada contra schemas: los paths y el modelo son
ejemplos que se deben sustituir, no perfiles descubiertos en una cuenta real.
Los contratos descriptor, policy y binding v1 se conservan sin campos nuevos.

```powershell
harness onboard --config C:/HarnessConfig/interview.json --dry-run --json
harness onboard --config C:/HarnessConfig/interview.json --dry-run --plan-out C:/HarnessPlans/alpha.json --json
harness onboard --apply --plan C:/HarnessPlans/alpha.json --stage prepare --json
harness onboard --apply --plan C:/HarnessPlans/alpha.json --stage integrate --json
harness onboard --apply --plan C:/HarnessPlans/alpha.json --stage certify --evidence C:/HarnessEvidence/alpha.json --json
```

Cada apply autoriza una sola etapa. El preview no escribe target, estado, config
global o destinos remotos. `--plan-out` crea exclusivamente el plan externo pedido;
un destino existente, hardlink o reparse point bloquea la exportación. El directorio
del binding y del plan debe existir. El plan congela contenido, hashes, identidad
del checkout, procedencia, recursos y política; modificar entradas exige otro preview.

Preparación crea únicamente recursos ausentes autorizados: recursos init del kit,
`.harness/development.yaml`, `.harness/context.md`, Skill de onboarding y
`<binding>.tools.json` externo. El binding v1 nuevo se crea después del contexto
portable. Un archivo existente compatible se preserva; uno distinto bloquea.
Cuando AGENTS personalizado hace que init v1 sea conflictivo, el plan conserva
ese rechazo y usa CompositePreparationPlan independiente, sin editar AGENTS en
prepare. Integrate revisa las adiciones del 02 sobre AGENTS/config.toml y usa su
adaptador con backups. El plan de integración se crea exclusivamente junto al
binding (`guided-<run_id>-integration.json`), fuera del checkout y del estado,
como exige el contrato del 02. El preview muestra su ubicación y las ediciones
previstas; tras preparar se verifica que cada byte sigue igual al revisado.

La política bootstrap debe autorizar todos los archivos nuevos y las ediciones
de integración. `.harness/` protegida bloquea bootstrap: hay que aportar una
política explícitamente revisada y repetir preview. El asistente no la relaja.
Development_policy_path permite seleccionar y verificar otra política del mismo
cliente/repository/base_branch; su hash queda en el plan. No cambia silenciosamente
el binding v1 ni activa esa política para futuras HUs. Esas transiciones llegan en 04.

OnboardingRun registra preflight, collect, preview, prepare, integrate y certify.
Los archivos propios guardan identidad y hash; los locks y handles Windows se
comparten con las garantías de init/02. Una ejecución incompleta no se reanuda
automáticamente ni afirma rollback del conjunto. Se recupera por etapa:

```powershell
harness onboard --recover --plan C:/HarnessPlans/alpha.json --stage integrate --json
harness onboard --recover --recover-apply --plan C:/HarnessPlans/alpha.json --stage integrate --json
harness onboard --recover --plan C:/HarnessPlans/alpha.json --stage prepare --json
harness onboard --recover --recover-apply --plan C:/HarnessPlans/alpha.json --stage prepare --json
```

Recuperar integración antes de preparación. Drift, reemplazo de identidad o
propiedad incierta produce conflict y conserva el archivo. Los planes, journals
y evidencia externa se conservan para auditoría; recuperación retira/restaura
únicamente los recursos propios demostrables. Después de recuperar, generar un
nuevo preview en vez de sobrescribir o reusar automáticamente planes antiguos.
Repetir una etapa completada verifica integridad y devuelve idempotent=true.

Certify recibe CertificationInput v1: certificate Desktop del 02, snapshot de
candidato, acceptance supervisada o null y required_capabilities. La aceptación
se liga a cliente/checkout, catálogo, snapshot y evidencia. El catálogo base tiene
un recibo de dependencia sobre 02 (commit 3963ac2, archivo d175d84 y hashes de
evidencia verificada/aceptada). Ese recibo acredita el incremento del producto;
no certifica el runtime del cliente. El cliente necesita su propia evidencia.

El informe separa prepared, supervised_preparation_accepted, certified y
remote_not_checked. Permisos conflictivos se conservan en strict_certificate y
limitations incluso tras aceptación. Una capacidad exigida ausente, conflictiva
o no observada bloquea certify; los archivos preparados siguen indicados como tales.
No se afirma conectividad remota, aislamiento ni HU completa por preparar archivos.
La comparación de candidatos detecta cambios persistentes en scopes, no evita
escrituras ni detecta ediciones restauradas. Declaraciones manuales no son firmas.

JSON conserva schema_version/command/status/checks. Código 0: etapa local comprobada,
con partial explícito por certificación/remoto pendiente. Código 1: decisión faltante,
conflicto, drift o capacidad requerida bloqueada. Código 2: entrada inválida,
contrato/version desconocido o combinación de flags incorrecta. Secretos son
rechazados sin copiarse al plan, journal, contexto o error público.
