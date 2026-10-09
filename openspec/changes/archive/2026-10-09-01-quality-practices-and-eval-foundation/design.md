# Design

## Context

Ver [proposal.md](proposal.md) para motivación y alcance. La base 0.1.0 proporciona contratos Pydantic v1, diagnóstico, init create-only y recuperación Windows. No tiene flujo de HU ni roles operativos.
Dependencia obligatoria: **bootstrap-codex-local-core y apply-client-onboarding (archivados)**, implementada y verificada. OpenSpec status comprueba artefactos, no satisface este gate. Los comandos nuevos de este documento son propuestos.

## Goals / Non-Goals

**Goals:** Catálogos cargables, íntegros y trazables; ningún recurso activa herramientas o produce resultados ficticios.

**Non-Goals:** implementación durante planificación, migración silenciosa de v1, cambios globales, uso de datos productivos, motor LLM propio para sustituir Desktop y consumo exacto sin fuente soportada.

## Decisions

1. Mantener las copias oficiales íntegras; adaptaciones y restricciones del harness van en wrappers/referencias propios. La Databricks License se conserva y el contenido se usa para desarrollo conectado a Databricks.

2. PracticePack v1: pack_id, version, sources y rules[] con id (rule_id lógico), technology, severity, statement, applicability, evidence y source_refs. Los borradores actuales son entradas a formalizar, no contratos runtime ya soportados; la tarea de schemas puede añadir rationale sin perder IDs/fuentes. Calidad técnica no equivale a permiso operativo.

3. EvalCase v1: id, role, task, input, expected{known_defects,checks[]}, split, source_rules, implementation_change y execution_mode. Cada check incluye id, description, critical, scorer y human_annotation_required. Dataset versionado por hash; observed_output/scores son null hasta ejecución. Casos acceptance-cases.json complementan los 24 tests con todos los escenarios OpenSpec.

4. Extensiones del cliente añaden o endurecen reglas; una excepción a una regla técnica requiere motivo, alcance y revisión. No puede ampliar permisos o saltar gates.

Razonamiento y alternativas:
- Procedimientos/roles/validadores separados frente a centralizar todo en AGENTS: mantiene instrucciones acotadas y permite probar controles con código.
- Paquete Python único frente a lógica copiada en Skills: versiona y prueba comportamiento una vez; Skills aportan instrucciones/wrappers.
- Integración por proyecto frente a reemplazo global: permite revisar personalizaciones y separar clientes.
- Preview/evidencia frente a automatización opaca: fija entradas/efectos y registra resultados observados, incluidos bloqueos.
- Delegación por impacto frente a todos los roles siempre: evita duplicar contexto y mantiene un escritor y revisión independiente.

## Contracts and operational boundaries

practice-pack.json, test-cases.json y eval-cases.json; schema_version=1; límite 1 MiB por documento y 256 casos por catálogo; paths de fixture relativos confinados.

Objetos estrictos y versiones conocidas. Capacidad requerida ausente es blocked; fuente opcional ausente es unavailable/not_checked. Los comandos nuevos conservan JSON schema_version/command/status/checks y códigos 0 (operación comprobada sin bloqueos, con partial explícito si corresponde), 1 (bloqueo/fallo/conflicto), 2 (entrada inválida). Reportes sanitizados no exponen credenciales.

Recursos compartidos viven en el paquete; contexto/configuración cliente en target; política, conectores, estado, backups y evidencias sin sanitizar fuera. Configurar una herramienta no autoriza publicación o ejecución remota. El journal de onboarding v1 no se reutiliza como contrato de HU o de edición.

## Validation and traceability

Tests iniciales: T23.
Evals iniciales: validación de definiciones; sin resultados de agentes en este incremento.
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
