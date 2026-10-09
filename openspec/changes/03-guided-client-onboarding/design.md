# Design

## Context

Ver [proposal.md](proposal.md) para motivación y alcance. La base 0.1.0 proporciona contratos Pydantic v1, diagnóstico, init create-only y recuperación Windows. No tiene flujo de HU ni roles operativos.
Dependencia obligatoria: **02-desktop-roles-and-tool-contracts**, implementada y verificada para preparación supervisada con aceptación explícita y evidencia. La certificación estricta completa no es requisito para preparar onboarding; una capacidad fallida sigue bloqueando fases que la exijan. OpenSpec status comprueba artefactos, no satisface este gate. Los comandos nuevos de este documento son propuestos.

## Goals / Non-Goals

**Goals:** Una persona nueva completa el flujo con plantilla o entrevista y recibe configuración trazable sin ampliar permisos por inferencia.

**Non-Goals:** implementación durante planificación, migración silenciosa de v1, cambios globales, uso de datos productivos, motor LLM propio para sustituir Desktop y consumo exacto sin fuente soportada.

## Decisions

1. LLM recopila y explica; núcleo valida y aplica. No se ejecuta shell arbitrario derivado de respuestas; herramientas faltantes se muestran como pasos explícitos.

2. Preguntar target, repo/base, convenciones, reglas, validaciones y conectores faltantes; inferencias observadas se presentan con procedencia y se confirman antes de activar configuración.

3. Contexto portable del cliente guarda convenciones/stack/reglas; ToolBinding externo guarda referencias de perfil/conexión y estado. Nunca guardar tokens ni URLs con credenciales.

4. El contrato v1 se mantiene. Nuevas selecciones viven en development.yaml y binding de herramientas separado; cualquier migración futura es explícita/versionada.

5. OnboardingRun agrupa etapas preflight, collect, preview, prepare, integrate, certify; fallo no implica rollback total ni reanuda efectos automáticamente. Preparación supervisada aceptada y certified son resultados separados. Conserva conflict/unsupported/not_checked y motivos del 02; no transforma aceptación del operador en garantía de permisos. Cualquier fase que requiera una capacidad fallida queda blocked.

6. El init v1 bloquea AGENTS personalizado y no se relaja ese contrato. El asistente lo reutiliza solo cuando su plan es aplicable. Para repos personalizados, un adaptador nuevo de preparación compuesta conserva AGENTS existente, crea únicamente recursos ausentes autorizados con las mismas garantías Windows y usa el plan de integración del 02 para las ediciones revisadas. No aplica un OnboardingPlan v1 marcado conflict ni ignora sus precondiciones.

7. Una política que protege .harness/ puede impedir bootstrap. El asistente muestra el bloqueo y solicita una política de onboarding explícitamente revisada; no relaja la política ni infiere autorización de las respuestas de contexto. La política efectiva de desarrollo se selecciona y verifica separadamente si difiere.

Razonamiento y alternativas:
- Procedimientos/roles/validadores separados frente a centralizar todo en AGENTS: mantiene instrucciones acotadas y permite probar controles con código.
- Paquete Python único frente a lógica copiada en Skills: versiona y prueba comportamiento una vez; Skills aportan instrucciones/wrappers.
- Integración por proyecto frente a reemplazo global: permite revisar personalizaciones y separar clientes.
- Preview/evidencia frente a automatización opaca: fija entradas/efectos y registra resultados observados, incluidos bloqueos.
- Delegación por impacto frente a todos los roles siempre: evita duplicar contexto y mantiene un escritor y revisión independiente.

## Contracts and operational boundaries

ClientDevelopmentConfig v1 (.harness/development.yaml), ClientToolBinding v1 externo, OnboardingRun v1 y QuestionnaireDraft v1. CLI previsto: harness onboard --config FILE --dry-run/--apply --plan FILE; no disponible aún.

Objetos estrictos y versiones conocidas. Capacidad requerida ausente es blocked; fuente opcional ausente es unavailable/not_checked. Los comandos nuevos conservan JSON schema_version/command/status/checks y códigos 0 (operación comprobada sin bloqueos, con partial explícito si corresponde), 1 (bloqueo/fallo/conflicto), 2 (entrada inválida). Reportes sanitizados no exponen credenciales.

Recursos compartidos viven en el paquete; contexto/configuración cliente en target; política, conectores, estado, backups y evidencias sin sanitizar fuera. Configurar una herramienta no autoriza publicación o ejecución remota. El journal de onboarding v1 no se reutiliza como contrato de HU o de edición.

## Validation and traceability

Tests iniciales: T15.
Evals iniciales: E01, E02, E24.
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
