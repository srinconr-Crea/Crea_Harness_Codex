# Design

## Context

Ver [proposal.md](proposal.md) para motivación y alcance. La base 0.1.0 proporciona contratos Pydantic v1, diagnóstico, init create-only y recuperación Windows. No tiene flujo de HU ni roles operativos.
Dependencia obligatoria: **05-databricks-validation-and-evidence**, implementada y verificada. OpenSpec status comprueba artefactos, no satisface este gate. Los comandos nuevos de este documento son propuestos.

## Goals / Non-Goals

**Goals:** Evals ejecutados con trazabilidad y gate reproducible; tokens/costos desconocidos se mantienen null con motivo.

**Non-Goals:** implementación durante planificación, migración silenciosa de v1, cambios globales, uso de datos productivos, motor LLM propio para sustituir Desktop y consumo exacto sin fuente soportada.

## Decisions

1. UsageObservation v1 lleva source, scope, observed_at, native_session_id si expuesto, input/output/cached tokens separados y cost_usd nullable. Cuota de cuenta nunca se reparte por HU.

2. No leer logs internos no documentados como contrato estable. Si Desktop no expone sesiones/uso atribuibles, registrar unavailable sin bloquear métricas de actividad.

3. Runner usa superficie soportada capaz de mantener la configuración objetivo. Eval manual en Desktop es un modo válido con evidencia; CLI valida solo la superficie CLI y no certifica Desktop.

4. Scorers deterministas verifican artefactos/acciones; juicio LLM opcional se calibra con etiquetas humanas y no reemplaza criterios críticos. Golden/holdout separados, 3 repeticiones por caso/configuración cuando se comparan modelos.

5. Gate: 100% de checks críticos en todas las repeticiones y >=90% de checks no críticos; blocked/not_run no cuentan como passed. Registrar false positives/negatives, varianza, duración y tokens si disponibles.

6. Hooks certificados alimentan eventos con idempotencia y no garantizan cobertura total. Comparación por mismo dataset/kit/runtime/modelo/esfuerzo y herramientas; presupuesto de evals explícito.

7. Cada milestone selecciona casos cuyo implementation_change ya está disponible. En 06 se evalúan los casos 01–06; los casos de proveedores se activan en 07 y el gate completo en 08. Casos futuros permanecen not_run y no se incluyen fraudulentamente como passed en el gate parcial. Holdout queda reservado a evaluación de promoción y no a ajuste iterativo de prompts; publicar un catálogo de diseño no demuestra independencia de un conjunto de producción, que se debe separar operativamente al implementar.

Razonamiento y alternativas:
- Procedimientos/roles/validadores separados frente a centralizar todo en AGENTS: mantiene instrucciones acotadas y permite probar controles con código.
- Paquete Python único frente a lógica copiada en Skills: versiona y prueba comportamiento una vez; Skills aportan instrucciones/wrappers.
- Integración por proyecto frente a reemplazo global: permite revisar personalizaciones y separar clientes.
- Preview/evidencia frente a automatización opaca: fija entradas/efectos y registra resultados observados, incluidos bloqueos.
- Delegación por impacto frente a todos los roles siempre: evita duplicar contexto y mantiene un escritor y revisión independiente.

## Contracts and operational boundaries

ActivityEvent, UsageObservation, EvalRun y EvalScore v1; result states passed/failed/blocked/not_run; CLI propuesto harness eval validate/run/report y harness usage report con alcance declarado.

Objetos estrictos y versiones conocidas. Capacidad requerida ausente es blocked; fuente opcional ausente es unavailable/not_checked. Los comandos nuevos conservan JSON schema_version/command/status/checks y códigos 0 (operación comprobada sin bloqueos, con partial explícito si corresponde), 1 (bloqueo/fallo/conflicto), 2 (entrada inválida). Reportes sanitizados no exponen credenciales.

Recursos compartidos viven en el paquete; contexto/configuración cliente en target; política, conectores, estado, backups y evidencias sin sanitizar fuera. Configurar una herramienta no autoriza publicación o ejecución remota. El journal de onboarding v1 no se reutiliza como contrato de HU o de edición.

## Validation and traceability

Tests iniciales: T19.
Evals iniciales: E13, E14, E15, E16, E17, E18, E20.
Consultar docs/planning/quality. Todos los escenarios adicionales de las delta specs se trazan a prueba/protocolo y evidencia en la verificación del incremento. Los tests simulados no certifican Desktop/Databricks.

Spark/MLflow no son dependencias del runtime básico para cargar catálogos. Los runners especializados se aíslan y fijan versión; código cliente solo se ejecuta por adaptador autorizado.

## Risks / Trade-offs

- Superficie Desktop/modelos cambiante → certificado de versión efectiva y unsupported explícito.
- Instrucciones confundidas con controles → gates en adaptadores y permisos/CI independientes; declarar cobertura.
- Mezcla de clientes o secretos → identidad seleccionada, estado segregado y redacción.
- Calidad aparente sin ejecución → oráculos, controles limpios, checks críticos y not_run por defecto.
- Skills upstream con acciones/dependencias adicionales → revisar dependency closure antes de activar; descargar no concede permisos.
- Orden documental sin enforcement automático → tarea inicial de cada incremento verifica evidencia de predecesor; el gate de negocio llega en 04.

## Migration Plan

1. Confirmar dependencia implementada/verificada y alcance autorizado.
2. Incorporar nuevos contratos/código/recursos mediante apply y ejecutar sus pruebas.
3. Conservar v1; nuevos recursos tienen versiones y ownership propios.
4. Usar planes explícitos con hashes/backups para editar configuración cliente.
5. Recover solo retira/restaura recursos propios demostrables; drift produce conflict.
6. Emitir evidencia real y habilitar el siguiente incremento tras verificación. No sync/archive/commit/publicación automáticos en esta propuesta.
