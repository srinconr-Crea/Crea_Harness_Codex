# Design

## Context

Ver [proposal.md](proposal.md) para motivación y alcance. La base 0.1.0 incluye onboarding, HU/gates del 04, validación/evidencia del 05 e infraestructura local de observabilidad/evals del 06. Esta última está verificada con 439 pruebas, smoke instalado y specs sincronizadas en ec84193/54faea5; su matriz real de agentes sigue pendiente.
El usuario autorizó el 2026-10-13 iniciar la implementación local de **07-story-and-pr-integrations** sobre esa infraestructura, con las tareas 2.4/3.3 de 06 pendientes. OpenSpec status y el archivo de 06 no sustituyen evidencia ni conceden permisos. Los comandos nuevos de este documento son propuestos.

## Goals / Non-Goals

**Goals:** HU de fuente trazable a PR draft autorizado con evidencia; repetir o reanudar no duplica publicación.

**Non-Goals:** implementación durante planificación, migración silenciosa de v1, cambios globales, uso de datos productivos, motor LLM propio para sustituir Desktop y consumo exacto sin fuente soportada.

## Decisions

1. StorySnapshot fija source_id, revision/etag, acceptance hash y refs; cambio externo de criterios invalida plan o exige revisión. Contenido externo no concede permisos.

2. ProviderCapability distingue read_story, create_branch, push, create_pr y write_story; solo activar las seleccionadas. Credenciales/host/repo se validan fuera del repo.

3. Antes de publicar se revalida candidato final, base/head, policy, approval y evidencia; sync/archive incluidos en el candidato o revalidados.

4. PublicationIntent contiene hash/head/base/provider y autorización explícita de acción. Una aprobación técnica no implica autorización social de comentar historias.

5. Reconciliar por remote branch/head y PR abierto del mismo intento antes de repetir; no crear duplicados y no sobrescribir ramas ajenas.

6. Crear PR draft por defecto en piloto; attach_artifact cuando corre dentro de Codex con herramienta disponible. Ausencia de integración se informa sin inventar asociación.

7. Separar habilitación de desarrollo y gate de publicación. La excepción aprobada permite implementar contratos/adaptadores, lectura seleccionada, preview y pruebas con dobles; las 126 evaluaciones Luna/medium de 06 conservan not_run y promoción blocked. Un candidato con evaluaciones requeridas pendientes MUST NOT hacer push, crear PR o comentar una historia aunque tenga autorización para publicar. Los dobles prueban controles/reconciliación, no certifican proveedores ni agentes. El smoke de escritura en un repo sintético real queda blocked hasta contar con los gates y la autorización específica de destino/acción; esa falta no impide implementar y probar su adaptador localmente.

Razonamiento y alternativas:
- Procedimientos/roles/validadores separados frente a centralizar todo en AGENTS: mantiene instrucciones acotadas y permite probar controles con código.
- Paquete Python único frente a lógica copiada en Skills: versiona y prueba comportamiento una vez; Skills aportan instrucciones/wrappers.
- Integración por proyecto frente a reemplazo global: permite revisar personalizaciones y separar clientes.
- Preview/evidencia frente a automatización opaca: fija entradas/efectos y registra resultados observados, incluidos bloqueos.
- Delegación por impacto frente a todos los roles siempre: evita duplicar contexto y mantiene un escritor y revisión independiente.

## Contracts and operational boundaries

StorySnapshot, ProviderBinding, PublicationIntent, PublicationAuthorization,
PublicationReceipt y StoryPlanBinding v1, con PublicationRequest para CLI.
StoryPlanBinding conserva en SQLite separado el vínculo inmutable y explícitamente
aprobado entre HU/intento/hash de plan y snapshot; revisión distinta exige nuevo
plan/aprobación. intent_sha256 funciona como idempotency_key de contenido;
outcome unknown exige lectura/reconciliación antes de reintentar.
El push CLI rechaza url.* heredadas y usa lease de rama ausente. El puente MCP
debe garantizar creación atómica con expected_old_oid=null/creation_only=true.
Attach solo se registra ante retorno True del callback que comprobó éxito real.
El candidato final verifica bytes físicos/modes y blobs Git, admitiendo solo
normalización LF/CRLF local explícita; filtros/encoding custom quedan blocked.

Objetos estrictos y versiones conocidas. Capacidad requerida ausente es blocked; fuente opcional ausente es unavailable/not_checked. Los comandos nuevos conservan JSON schema_version/command/status/checks y códigos 0 (operación comprobada sin bloqueos, con partial explícito si corresponde), 1 (bloqueo/fallo/conflicto), 2 (entrada inválida). Reportes sanitizados no exponen credenciales.

Recursos compartidos viven en el paquete; contexto/configuración cliente en target; política, conectores, estado, backups y evidencias sin sanitizar fuera. Configurar una herramienta no autoriza publicación o ejecución remota. El journal de onboarding v1 no se reutiliza como contrato de HU o de edición.

## Validation and traceability

Tests iniciales: T20.
Evals iniciales: E21, E22, E23.
Consultar docs/planning/quality. Todos los escenarios adicionales de las delta specs se trazan a prueba/protocolo y evidencia en la verificación del incremento. Los tests simulados no certifican Desktop/Databricks.

Añadir negativos de publicación con evals de 06 not_run/blocked aun con autorización explícita, y comprobar que preview sigue disponible sin efectos. E21/E22/E23 requieren ejecuciones/anotaciones reales para el gate final; los dobles no cuentan como esas evaluaciones. Las tareas 2.5/3.3 y el criterio de salida completo permanecen exigibles; esta excepción no habilita 08.

Spark/MLflow no son dependencias del runtime básico para cargar catálogos. Los runners especializados se aíslan y fijan versión; código cliente solo se ejecuta por adaptador autorizado.

## Risks / Trade-offs

- Superficie Desktop/modelos cambiante → certificado de versión efectiva y unsupported explícito.
- Instrucciones confundidas con controles → gates en adaptadores y permisos/CI independientes; declarar cobertura.
- Mezcla de clientes o secretos → identidad seleccionada, estado segregado y redacción.
- Calidad aparente sin ejecución → oráculos, controles limpios, checks críticos y not_run por defecto.
- Skills upstream con acciones/dependencias adicionales → revisar dependency closure antes de activar; descargar no concede permisos.
- Orden documental sin enforcement automático → tarea inicial de cada incremento verifica evidencia de predecesor; el gate de negocio llega en 04.

## Migration Plan

1. Confirmar evidencia de la infraestructura local de 06 y registrar la excepción aprobada, sus tareas pendientes y el bloqueo de promoción/publicación; comprobar alcance autorizado.
2. Incorporar nuevos contratos/código/recursos mediante apply y ejecutar sus pruebas.
3. Conservar v1; nuevos recursos tienen versiones y ownership propios.
4. Usar planes explícitos con hashes/backups para editar configuración cliente.
5. Recover solo retira/restaura recursos propios demostrables; drift produce conflict.
6. Emitir evidencia real y habilitar el siguiente incremento tras verificación. No sync/archive/commit/publicación automáticos en esta propuesta.
