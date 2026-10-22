# Pruebas Crea 0.1.4

Kit y proyecto conviven en la raíz del repositorio. Los JSON iniciales son plantillas
neutrales: setup_complete=false bloquea planificación ejecutable. Personalizar
criterios, consumidores y comandos reales, sin inferirlos de un ejemplo.

## Fuente única y responsabilidades

`docs/proyecto.json.validation.testing.policy_path` apunta al catálogo único de
checks/argv/inputs/criterios/assertions/reglas. `validation.required_checks` contiene
exclusivamente IDs; un ID obligatorio debe estar seleccionado para la HU. El
selector aplica unión de reglas y dependencias; unknown o criterio sin check bloquea.

Planner define riesgos/criterios/consumidores/plan preliminar; Developer escribe
código y tests previstos, diagnóstico focalizado y regresiones justificadas;
Tester ejecuta el plan final; Reviewer contrasta código/cobertura/recibos y OpenSpec.
Un rol activo, sin subdelegación y contador global max_fix_rounds. No modificar
expected para aprobar. El plan técnico no concede permisos de operación.
Una ronda comienza cuando principal despacha una corrección tras needs_changes y
termina con su nueva ejecución/revisión; varios checks fallidos del mismo intento
no son varias rondas. Registrar round_id y candidatos inicial/final en handoff.

## Implementado y comprobable

| Módulo | Evidencia y límite |
|---|---|
| contract.py | Selector/gate puro; mismo input produce mismo plan; no Git ni procesos. |
| git_adapter.py | Base SHA ancestro, HEAD, staged, unstaged, untracked, rename/delete/type/conflictos; NUL y snapshot. No red ni descubrimiento automático de consumidores. |
| execution.py | argv revisado, intérprete explícito, cwd raíz, timeout, entorno mínimo, sin shell y logs acotados/redacción básica. No sandbox contra tests hostiles. |
| reports.py | IDs/contadores JUnit y criterios; skips/0 tests bloqueados; JSON coverage.py por archivo/umbral. No prueba cobertura semántica. |
| schemas.py | Draft2020-12 + formatos, offline; campos extra y referencias remotas rechazados. |
| workflow.py / pruebas.py | Plan/run/gate separados; Git/config/adaptadores, recibos, entorno, edad e integridad; Reviewer no relanza suites. |
| kit_validation.py | JSON/schema/TOML/YAML/referencias/paths anidados y bytes originales; no ejecuta negocio ni agentes. |

El entorno local registra huella de intérprete/plataforma/metadata de paquetes;
no acredita permisos remotos ni equivalencia con DBR. Incluir locks/config y
dependencias consumidas entre inputs; metadata no atesta todos sus bytes. TTL
único en execution.max_evidence_age_seconds. reuse_seconds es elegibilidad futura
entre planes, no caché activa. Recibos no son firmas: conservar evidencia primaria.

## Git y circularidad

Inventario total por capas y recibo de exclusiones con hashes. Solo se excluyen
outputs exactos declarados en execution.outputs bajo pruebas de una HU; nombres
restringidos a plan/git/resultados/gate/recibos/logs/JUnit/cobertura/resumen. No
excluir código/tests/fixtures/criterios/política. Un output que coincida con inputs
de un check bloquea. Un untracked nuevo invalida, aunque faltara en el plan anterior.
No basta git diff --name-only. Planificar nunca ejecuta suites.

## Ejecución y no repetición

Configurar execution.python_executable y reviewed_policy_digest después de revisar
el catálogo. Por ID: junit_path, assertion_tests y cobertura opcional. JUnit usa
classname::name completo, incluso parámetros. Exit 0 sin assertions/IDs requeridos
no pasa; todos los skips de la suite requerida bloquean aunque se cumpla min_tests.

Run solo admite pytest/local/local_execution en 0.1.4. Otras capacidades: blocked.
El runner emite reporte; el parser no lo inventa. XML/JSON malformado, reporte
ausente o recibo ajeno no pasan. Logs acotados/redactados no autentican assertions;
la redacción es básica: revisar datos antes de versionar.

Conservar intentos: para reejecutar, outputs nuevos bajo attempt-<id>/ y plan
regenerado. No sobrescribir receipts ni retocar fechas/plan_id. No hay importación
entre planes. Reviewer usa gate sin run; solicita al Tester reejecución solo por
invalidación, evidencia insuficiente o regla fija, registrando motivo. Gate vuelve
a obtener Git/reportes para detectar inputs nuevos o evidencia alterada.
CLI exige nombres por rol (plan.json/resultados.json/gate.json/git.json), bloquea
colisiones con evidencia primaria y preserva planes/recibos de intentos anteriores.

## Capacidades por fases

capabilities.json/schema registran entrega/inactividad. Habilitar requiere
desarrollo, fixtures, revisión y nueva versión; cambiar un booleano no implementa.
Si un check requiere una capacidad inactiva, bloquea aunque una suite local pase.

| Capacidad inactiva | Integración futura requerida |
|---|---|
| Runtime / Spark local | Manifest autorizado, preflight → smoke → suite, API/DBR, IDs/versiones/huellas/assertions, inventario aun con fallo y cierre aprobado. |
| Semgrep / triage | JSON scanner; errores separados de vulnerabilidades; positivos/negativos/FP conocidos; reglas consultivas hasta promoción humana. |
| Mutation local | Copia aislada, baseline verde, viable/killed/survived/incompetent, triage y presupuesto; nunca mutar checkout productivo/remoto. |
| Reviewer evals | Dataset humano independiente, FP/FN/acuerdo/costos, calibration.json único, promoción/override humano, sin autopromoción. |
| Reutilización entre planes | Linaje plan/resultado origen, hashes/definiciones iguales, entorno/TTL/autorizaciones; can_reuse no basta. |
| CI | Opt-in por integración específica; no instalar workflows en setup. |

Runtime por comportamiento/política, no por extensión: solo MD no activa Spark.
Mock/Spark local no prueba UC/ADLS/DBR; bundle validate no prueba ejecución. Sin
crear cluster/catalog por HU. Perfil/host/identidad/rutas/negocio por cliente.
Ver [runtime](runtime.md). CI: PR/checks sin deploy → merge humano → deploy autorizado
del SHA → smoke → promoción. No asumir ramas/triggers ni operar jobs/tablas/permisos.

## Catálogo, rúbrica y adversariales

Completar failure-modes.json: riesgo → requisito → expected independiente →
fixture/test. Nulos/tipos/límites/duplicados/grano/concurrencia/replay/autorización
solo si aplican. Revisar consumidores desde imports/llamadores/config/notebooks;
un grep vacío no demuestra ausencia de consumidores dinámicos.

Reviewer: corrección, seguridad, rendimiento, tests faltantes, estilo/documentación;
especialidad Python/Spark/SQL/infra por aplicabilidad. Archivo/línea/evidencia por
hallazgo; rendimiento con medición. review.schema.json separa suggested_action y
effective_stage. Umbrales únicos en calibration.json; stage=block sin promoción
humana bloquea. Evals/promoción automáticos inactivos, sin autopromoción por JSON.
Overrides en review-history.json conservan decisión IA/humana, motivo/evidencia,
candidato/regla y regresión si aplica.

Adversariales pasan al rechazar ataque **y** permitir control legítimo: rutas,
catálogos, SQL/argumentos, secretos, dependencias y superficie LLM si aplica. Fixtures
locales prueban traversal, XML con entidades, argv no revisado, recibos ajenos y
controles legítimos; no acreditan seguridad de un servicio o producto remoto.
No ejecutar todas las herramientas por HU; instalar solo en setup autorizado.

## Verificar esta distribución

```powershell
& $python -B -m unittest discover -s tests/crea -v
& $python -B scripts/crea/validar-kit.py --original
```

Tests crean repositorios Git sintéticos y procesos locales sin red. No equivalen
a cuatro agentes despachados; piloto real Codex/runtime autorizado queda pendiente.
Setup y comandos: [configuración manual](../configuracion-manual.md).
