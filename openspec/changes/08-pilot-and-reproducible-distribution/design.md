# Design

## Context

Ver [proposal.md](proposal.md) para motivación y alcance. La base implementada hasta 07 proporciona contratos v1, diagnóstico, onboarding, flujo local de HU, roles y publicación con gates. Su aceptación remota sigue pendiente; los comandos nuevos de este documento son propuestos.
Por autorización del usuario del 2026-10-13, **07-story-and-pr-integrations** es la base de implementación local, mientras que su verificación completa y los pendientes de 06 siguen siendo dependencias obligatorias de certificación y release. OpenSpec status comprueba artefactos, no satisface estos gates.

## Goals / Non-Goals

**Goals:** Usuario nuevo completa onboarding y HU en Desktop, dos clientes permanecen aislados y update/recover preserva personalizaciones.

**Non-Goals:** implementación durante planificación, migración silenciosa de v1, cambios globales, uso de datos productivos, motor LLM propio para sustituir Desktop y consumo exacto sin fuente soportada.

## Decisions

1. Primero equipo limpio y dos clientes genéricos; luego copia piloto NaturaPet bajo su política aprobada. Negocio del piloto no pasa al paquete.

2. El paquete candidato contiene versiones/hash de dependencias, prácticas, roles y Skills, y estados explícitos de evidencia pendiente. El bundle certificado de release exige certificados Desktop y evals reales de 06/07. La existencia del candidato no prueba certificación. Firma/integridad solo se afirma si existe fuente de confianza real.

3. Update no reutiliza init create-only para sobrescribir. Plan de actualización compara installed_hash/upstream_hash/local_hash y preserva ediciones; conflicto exige resolución y nuevo plan.

4. Installer distingue binarios instalados, recursos preparados, login pendiente, confianza pendiente y funciones unsupported. No ejecutar instaladores upstream sin revisión/versionado.

5. Plugin distribuye capacidades admitidas; Python/agentes/otras dependencias se gestionan separadamente si plugin no las cubre. No activar globalmente recursos de negocio.

6. Gate de release exige cierre verificado de los pendientes 06/07, onboarding, selección real de roles/modelos/herramientas, HU a PR autorizado mediante el harness, interrupción/reanudación y update/recover probados. El avance del código local no cambia los gates de evals, publicación o capacidades existentes.

7. Separar implementación de aceptación: contratos, bootstrap, launcher, update/recover, empaquetado candidato y pruebas locales pueden completarse ahora. Los protocolos remotos se preparan sin ejecutarlos ni simular resultados reales. Certificación, release, archivo como incremento aceptado y habilitación del siguiente incremento permanecen bloqueados hasta obtener la evidencia exigida.

Razonamiento y alternativas:
- Procedimientos/roles/validadores separados frente a centralizar todo en AGENTS: mantiene instrucciones acotadas y permite probar controles con código.
- Paquete Python único frente a lógica copiada en Skills: versiona y prueba comportamiento una vez; Skills aportan instrucciones/wrappers.
- Integración por proyecto frente a reemplazo global: permite revisar personalizaciones y separar clientes.
- Preview/evidencia frente a automatización opaca: fija entradas/efectos y registra resultados observados, incluidos bloqueos.
- Delegación por impacto frente a todos los roles siempre: evita duplicar contexto y mantiene un escritor y revisión independiente.

## Contracts and operational boundaries

ReleaseManifest, InstallationBinding, UpdatePlan y PilotReport v1; kit.lock.json en cliente fija recursos requeridos, estado externo conserva ownership y backups.

Los reportes/manifiestos distinguen estado de implementación local, aceptación y evidencia requerida. Una dependencia con evidencia not_run/blocked conserva certified=false y release_allowed=false aun con todas las pruebas locales aprobadas. Un paquete candidato no incluye certificados ficticios ni hereda certificación de una autorización de piloto manual.

Objetos estrictos y versiones conocidas. Capacidad requerida ausente es blocked; fuente opcional ausente es unavailable/not_checked. Los comandos nuevos conservan JSON schema_version/command/status/checks y códigos 0 (operación comprobada sin bloqueos, con partial explícito si corresponde), 1 (bloqueo/fallo/conflicto), 2 (entrada inválida). Reportes sanitizados no exponen credenciales.

Recursos compartidos viven en el paquete; contexto/configuración cliente en target; política, conectores, estado, backups y evidencias sin sanitizar fuera. Configurar una herramienta no autoriza publicación o ejecución remota. El journal de onboarding v1 no se reutiliza como contrato de HU o de edición.

## Validation and traceability

Tests iniciales: T22.
Evals durante desarrollo local: validación de definiciones; no se atribuyen resultados de agentes a estas pruebas. Aceptación final: importar y evaluar las 144 ejecuciones reales requeridas de 06/07 y completar los protocolos de 08; toda evidencia ausente permanece not_run/blocked.
Consultar docs/planning/quality. Todos los escenarios adicionales de las delta specs se trazan a prueba/protocolo y evidencia en la verificación del incremento. Los tests simulados no certifican Desktop/Databricks.

Spark/MLflow no son dependencias del runtime básico para cargar catálogos. Los runners especializados se aíslan y fijan versión; código cliente solo se ejecuta por adaptador autorizado.

## Risks / Trade-offs

- Superficie Desktop/modelos cambiante → certificado de versión efectiva y unsupported explícito.
- Instrucciones confundidas con controles → gates en adaptadores y permisos/CI independientes; declarar cobertura.
- Mezcla de clientes o secretos → identidad seleccionada, estado segregado y redacción.
- Calidad aparente sin ejecución → oráculos, controles limpios, checks críticos y not_run por defecto.
- Skills upstream con acciones/dependencias adicionales → revisar dependency closure antes de activar; descargar no concede permisos.
- Desarrollo anticipado confundido con aceptación → registrar base y pendientes antes de implementar, y exigir cierre de dependencias en el gate final de release; no marcar protocolos reales como completados por pruebas locales.

## Migration Plan

1. Registrar base implementada de 07, pendientes reales de 06/07 y autorización de desarrollo local anticipado, sin certificar dependencias.
2. Incorporar nuevos contratos/código/recursos mediante apply y ejecutar sus pruebas.
3. Conservar v1; nuevos recursos tienen versiones y ownership propios.
4. Usar planes explícitos con hashes/backups para editar configuración cliente.
5. Recover solo retira/restaura recursos propios demostrables; drift produce conflict.
6. Completar aceptación real de 06/07 y protocolos de 08; emitir evidencia, verificar el criterio de salida y solo entonces certificar release y habilitar el siguiente incremento. No sync/archive/commit/publicación automáticos en esta propuesta.
