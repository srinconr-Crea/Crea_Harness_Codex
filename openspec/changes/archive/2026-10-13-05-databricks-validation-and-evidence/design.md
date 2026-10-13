# Design

## Context

Ver [proposal.md](proposal.md) para motivación y alcance. La base 0.1.0 proporciona contratos Pydantic v1, diagnóstico, init create-only y recuperación Windows. No tiene flujo de HU ni roles operativos.
Dependencia obligatoria: **04-hu-lifecycle-and-development-gates**, implementada y verificada. OpenSpec status comprueba artefactos, no satisface este gate. Los comandos nuevos de este documento son propuestos.

## Goals / Non-Goals

**Goals:** Evidencia determinista y remota genuina donde se exige, ligada al candidato; sin credenciales o runtime disponibles se registra bloqueo.

**Non-Goals:** implementación durante planificación, migración silenciosa de v1, cambios globales, uso de datos productivos, motor LLM propio para sustituir Desktop y consumo exacto sin fuente soportada.

## Decisions

1. L0 parsing/lint/schema; L1 lógica Python y PySpark sintético aislado; L2 semántica SQL/Spark/Delta en runtime certificado; L3 integración notebook/job/bundle en sandbox seleccionado. No equivalencia automática entre capas.

2. No importar código cliente con credenciales del desarrollador. Código arbitrario va a worker aislado sin credenciales o job con identidad separada y recursos allowlist.

3. Databricks profile/host/job/volume/runtime se seleccionan y verifican explícitamente. Tests remotos son opcionales solo si el plan aprobado no los exige; falta de acceso a prueba requerida bloquea candidato.

4. Bundle validate puede resolver/auth/consultar según configuración; se trata como operación potencialmente remota, con preflight, identidad y autorización. Validación YAML offline no demuestra validación de bundle.

5. JobRequest vincula client/run/attempt/candidate/data/runtime/request_key. Antes de repetir envío ambiguo se reconcilia; no asumir que un timeout canceló la ejecución.

6. Performance requiere baseline y perfil reproducible. No exigir cache, partición, broadcast o UDF alternatives sin evidencia y condiciones aplicables.

Razonamiento y alternativas:
- Procedimientos/roles/validadores separados frente a centralizar todo en AGENTS: mantiene instrucciones acotadas y permite probar controles con código.
- Paquete Python único frente a lógica copiada en Skills: versiona y prueba comportamiento una vez; Skills aportan instrucciones/wrappers.
- Integración por proyecto frente a reemplazo global: permite revisar personalizaciones y separar clientes.
- Preview/evidencia frente a automatización opaca: fija entradas/efectos y registra resultados observados, incluidos bloqueos.
- Delegación por impacto frente a todos los roles siempre: evita duplicar contexto y mantiene un escritor y revisión independiente.

## Contracts and operational boundaries

ValidationPlan, ValidationRequest y ValidationEvidence v1: test_id, candidate_sha256, plan_revision, practice_pack_sha256, tool/runtime/data hashes, status, result URI/hash, remote_run_id y timestamps; límites/logs sanitizados.

Objetos estrictos y versiones conocidas. Capacidad requerida ausente es blocked; fuente opcional ausente es unavailable/not_checked. Los comandos nuevos conservan JSON schema_version/command/status/checks y códigos 0 (operación comprobada sin bloqueos, con partial explícito si corresponde), 1 (bloqueo/fallo/conflicto), 2 (entrada inválida). Reportes sanitizados no exponen credenciales.

Recursos compartidos viven en el paquete; contexto/configuración cliente en target; política, conectores, estado, backups y evidencias sin sanitizar fuera. Configurar una herramienta no autoriza publicación o ejecución remota. El journal de onboarding v1 no se reutiliza como contrato de HU o de edición.

## Validation and traceability

Tests iniciales: T01, T02, T03, T04, T05, T06, T07, T08, T09, T10, T11, T12, T13, T14, T18.
Evals iniciales: E07, E09, E10, E11, E12.
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
