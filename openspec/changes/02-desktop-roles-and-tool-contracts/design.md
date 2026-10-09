# Design

## Context

Ver [proposal.md](proposal.md) para motivación y alcance. La base 0.1.0 proporciona contratos Pydantic v1, diagnóstico, init create-only y recuperación Windows. No tiene flujo de HU ni roles operativos.
Dependencia obligatoria: **01-quality-practices-and-eval-foundation**, implementada y verificada. OpenSpec status comprueba artefactos, no satisface este gate. Los comandos nuevos de este documento son propuestos.

## Goals / Non-Goals

**Goals:** Preparación supervisada implementada y verificada, matriz de capacidades observadas y limitaciones aceptadas explícitamente, y evidencia de evals con anotación humana; la certificación estricta se informa por separado y no es requisito para preparar onboarding. Archivos presentes nunca equivalen a certificación.

**Non-Goals:** implementación durante planificación, migración silenciosa de v1, cambios globales, uso de datos productivos, motor LLM propio para sustituir Desktop y consumo exacto sin fuente soportada.

## Decisions

1. AGENTS.md contiene reglas permanentes y entrada al workflow; las Skills contienen procedimiento; TOML contiene rol y ajustes compatibles. No duplicar todas las prácticas en cada prompt.

2. RoleCatalog v1 distingue responsabilidad de delegación: una HU pequeña puede usar el principal; auditor/verifier tienen obligación de no editar candidato y developer conserva un solo escritor. Esta obligación no demuestra aislamiento. Si Desktop permite escritura pese al perfil, se registra conflict y no se certifica read-only. El operador puede aceptar revisión supervisada del candidato identificado con comparación antes/después; drift bloquea aceptación. La comparación detecta cambios persistentes, no impide escritura ni garantiza detectar cambios restaurados.

3. Cada perfil operativo fija modelo y esfuerzo compatibles verificados en la cuenta. Falta del modelo requerido bloquea ese rol, sin sustitución silenciosa; catálogos no contienen nombres universales asumidos.

4. Integración usa un nuevo plan explícito de ediciones con old_hash/new_hash y backup externo. Revalida antes de reemplazar; conflicto conserva el archivo y no mezcla automáticamente instrucciones incompatibles.

5. Hooks solo se habilitan para eventos probados; MCP y sandbox se configuran por capacidades soportadas. Una recomendación de herramienta no es una restricción de permisos. Overrides runtime del padre pueden prevalecer sobre sandbox del TOML. Si la app expone modo read-only, una sesión de revisión independiente puede probarlo; su éxito no certifica sesiones mixtas ni requiere repetir pruebas indefinidamente.

6. Preparación supervisada es un resultado separado del DesktopCertificate estricto. Requiere aceptación del operador ligada a cliente/checkout, catálogo, candidato y versión de evidencia, no una aceptación global ni excepción en assess_certificate. Debe incluir capacidades observadas, límites y motivos de certified=false; un requisito de fase ausente sigue blocked.

7. Modelo/esfuerzo solicitados, declarados, expuestos por contrato runtime y auto-reportados se guardan con procedencia separada. No inferir configuración efectiva desde el modelo del padre o load_desktop(), que devuelve un catálogo pasivo. Evals conservan input/output originales, identidad de ejecución, anotación humana y defectos; un resultado negativo puede estar revisado sin convertirse en passed.

Razonamiento y alternativas:
- Procedimientos/roles/validadores separados frente a centralizar todo en AGENTS: mantiene instrucciones acotadas y permite probar controles con código.
- Paquete Python único frente a lógica copiada en Skills: versiona y prueba comportamiento una vez; Skills aportan instrucciones/wrappers.
- Integración por proyecto frente a reemplazo global: permite revisar personalizaciones y separar clientes.
- Preview/evidencia frente a automatización opaca: fija entradas/efectos y registra resultados observados, incluidos bloqueos.
- Delegación por impacto frente a todos los roles siempre: evita duplicar contexto y mantiene un escritor y revisión independiente.

## Contracts and operational boundaries

RoleCatalog v1, DesktopIntegrationPlan v1 y DesktopCertificate v1; certificado identifica versión app/motor, cuenta/availability sanitizada, rol/modelo/esfuerzo, herramientas y resultado observado.

Objetos estrictos y versiones conocidas. Capacidad requerida ausente es blocked; fuente opcional ausente es unavailable/not_checked. Los comandos nuevos conservan JSON schema_version/command/status/checks y códigos 0 (operación comprobada sin bloqueos, con partial explícito si corresponde), 1 (bloqueo/fallo/conflicto), 2 (entrada inválida). Reportes sanitizados no exponen credenciales.

Recursos compartidos viven en el paquete; contexto/configuración cliente en target; política, conectores, estado, backups y evidencias sin sanitizar fuera. Configurar una herramienta no autoriza publicación o ejecución remota. El journal de onboarding v1 no se reutiliza como contrato de HU o de edición.

## Validation and traceability

Tests iniciales: T21, T24.
Evals iniciales: E03, E04.
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

## Adaptación aprobada y evidencia Desktop

El usuario aprobó preparación supervisada el 2026-10-09. Evidencia preservada en
[desktop-runtime-2026-10-09](../../../docs/evidence/desktop-runtime-2026-10-09/manifest.json):
selección de roles real declarada por el runtime y escritura permitida para auditor/verifier.
El conflicto no se elimina. Seis outputs originales de E03/E04 conservados; E04
solo propone tests de null explícitos en una de tres repeticiones. La anotación
humana acepta este defecto para uso supervisado. Los contratos/comandos nuevos
están implementados y verificados para el alcance supervisado.

El informe supervisado y la comparación del candidato serán contratos/operaciones
separados, con schema_version conocido, campos estrictos y hashes de inputs.
La captura incluirá rutas autorizadas y contenidos/ausencias, excluyendo estado/evidencia
externos del candidato. Cambios persistentes, archivos añadidos/eliminados o identidad
incorrecta bloquean aceptación; el informe no borra ni revierte cambios del revisor.
Debe probarse candidato intacto, drift, aceptación ausente/obsoleta y conflicto de
sandbox conservado en el certificado. Ninguna excepción cambia contratos v1.

03 podrá comenzar tras implementar/verificar este alcance supervisado y su aceptación;
no basta con actualizar estos artefactos. La certificación de capacidades y las fases
que la requieren siguen bloqueadas hasta tener evidencia válida.
