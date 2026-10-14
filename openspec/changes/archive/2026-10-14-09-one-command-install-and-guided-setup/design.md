# Design

## Context

Ver `proposal.md` para la motivación. La implementación inspeccionada aporta `distribution.py` y `distribution_kit/launcher.ps1`, `guided_onboarding.py`, `desktop_resources.py`, contratos v1, CLI y `windows_fs.py`. El launcher exige Python/Git externos; bootstrap detecta herramientas mediante `which`. El onboarding prepara recursos por etapas y copia su Skill después de preparar el cliente. La política v1 contiene `read_only_paths` y `denied_paths`, pero no un permiso positivo general de lectura/escritura. Las pruebas de distribución/guiado/Desktop ya cubren hashes, conflictos, redacción y recuperación: se extienden esas garantías.

La instalación local verificada de 08 es una base técnica, no un release aceptado. La autorización de esta propuesta cubre planificar integración local sobre ella; implementar requiere apply posterior. No se alteran certificados ni las evaluaciones pendientes.

## Goals / Non-Goals

**Goals:**

- Tener una entrada de instalación y una Skill de setup disponibles sin preparar previamente un cliente.
- Mantener runtime, cliente e identidad/estado separados y convertir el flujo normal en decisiones de negocio, no edición manual de contratos de comandos.
- Preparar dependencias necesarias y producir un informe de capacidades comprobables, utilizable por 10.

**Non-Goals:**

- Instalar/autenticar Codex, resolver MFA o aprobar confianza en nombre del operador; soportar todas las arquitecturas/SO en el primer incremento.
- Reemplazar el motor nativo de conversación/delegación o interceptar cualquier herramienta de Desktop.
- Certificar sandbox, publicar una release, desplegar datos/jobs o promover los gates históricos mediante este setup.

## Decisions

### 1. Instalador independiente y runtime por usuario

Entregar `install-harness.ps1` como entrada del kit candidato, invocable mediante un único comando PowerShell documentado. Acepta kit offline o manifiesto remoto de versión exacta, raíz de instalación opcional y modo preview. El usuario obtiene/revisa el punto de entrada desde el canal de distribución; no se propone ejecutar texto remoto mediante `Invoke-Expression`. La URL pública definitiva es un parámetro de publicación posterior, no un requisito para probar un kit local.

Default: `%LOCALAPPDATA%/LocalHarness/installations/<version>/`; registro de instalación y lock separado bajo `%LOCALAPPDATA%/LocalHarness/`. Mantener compatible el launcher v1; nueva fachada llama runtime absoluto, nunca `python`/`harness` encontrados arbitrariamente en PATH. Validar propietarios, hashes, rutas finales y reparse points con las garantías Windows existentes.

Si existe Python 3.13 compatible y aceptado, construir venv privado. Si falta, usar un instalador oficial de Python Windows de versión fijada, instalación por usuario en ruta gestionada, sin cambios de PATH ni asociación global; el plan incluye los efectos de registro de usuario y la recuperación admitida por su instalador. Git portátil oficial, Node ZIP oficial y OpenSpec fijado en ámbito local se añaden solo cuando las capacidades seleccionadas los necesitan. No usar `latest` ni invocar un bootstrap no fijado para pip/npm. Las dependencias transitivas del runtime y herramientas se fijan en lock/manifiesto y se verifican antes de ejecutar. La instalación no puede eludir controles corporativos o del sistema.

Alternativas descartadas: exigir Python instalado mantiene el problema actual; un plugin por sí solo no distribuye/ejecuta el runtime Python automáticamente. Publicar un plugin completo añade aprobaciones/canal de distribución ajenos al objetivo inicial; el camino obligatorio es Skill de usuario más runtime aislado.

### 2. Descubrimiento inicial separado de recursos del cliente

La instalación escribe exclusivamente su Skill de entrada y registro de runtime en el ámbito personal de Skills soportado por el host. La documentación actual describe `$HOME/.agents/skills`; no asumir que una ruta legacy `$CODEX_HOME/skills` funciona en todas las versiones. Registrar superficie/ruta/versiones observadas, detectar colisiones y proporcionar recarga o reinicio si no aparece. No editar catálogos internos ni activar mecanismos no soportados.

La Skill genérica resuelve el runtime mediante un registro validado sin interpolar respuestas del chat como shell. Puede ejecutarse desde un chat local sin repo cliente. Recursos `.agents/skills/harness-*`, `.codex/agents/harness-*.toml`, `.codex/config.toml` y bloque gestionado de `AGENTS.md` se preparan en el cliente mediante los adaptadores existentes, conservando contenido personalizado.

`resource_installed` es comprobable por CLI; `skill_discovered` requiere observación real en Codex. Una prueba con filesystem doble no marca el segundo. Referencia: [Build skills](https://learn.chatgpt.com/docs/build-skills), consultada 2026-10-14.

### 3. Contratos separados para importación, acceso y setup

Proponer contratos nuevos versionados sin alterar esquemas publicados v1:

| Contrato | Entradas/salida esenciales |
| --- | --- |
| InstallationRecord | versión/product hash, runtime absoluto, herramientas/versiones/hashes, Skill gestionada, ownership, capacidades pendientes |
| SetupInput | referencias a descriptor/política/binding v1, repository_url opcional, access_scope, selecciones locales, capacidades solicitadas y procedencia de cada campo |
| AccessScope v1 | read_allow, write_allow, deny, referencia/hash de política v1 e identidad del cliente |
| SetupPlan | identidad/checkout, hashes de entradas/precondiciones, operaciones/etapas/dependencias, destinos exactos, descargas, comandos tipados, efectos externos, revisión/hash |
| SetupReport | etapas/resultados, prepared, recursos instalados, observaciones Desktop, capabilities con estado/evidencia/reason/next_action y gates existentes |

Archivos portables: descriptor/política actuales y contrato adicional `access-scope.json` exportable a la configuración del cliente. Binding y selección de perfil/rutas absolutas pertenecen al estado externo; no se copian ciegamente entre máquinas. `state_dir` conserva la identidad terminal `client_id/checkout_id`. La URL debe coincidir con owner/repo v1 tras normalización, sin credenciales incrustadas. Clonar solo cuando el destino seleccionado esté ausente y el plan lo incluya; un checkout existente debe tener remoto/base apropiados y cambios locales explicitados.

AccessScope usa rutas relativas canónicas y prefijos de directorio explícitos; no glob ambiguo. Deny vence; lectura exige read_allow; escritura exige write_allow y lectura del recurso cuando la operación la necesita. Política v1 y plan HU restringen adicionalmente; `read_only_paths` siempre prohíbe escritura. Se rechazan rutas absolutas, `..`, ADS, nombres reservados, alias de case Windows, enlaces y escapes. Acceso de metadatos Git/contratos gestionados se presenta como requisito técnico en el plan, sin excepciones ocultas de lectura. No se amplía write_allow para copiar Skills: integración gestionada tiene su alcance propio revisable, limitado a archivos exactos del plan.

### 4. Fachada de setup compuesta y una revisión autorizable

Proponer `harness setup interview|preview|apply|status|recover`, manteniendo comandos existentes. `interview` produce preguntas/valores con procedencia; el chat recoge decisiones y pasa argumentos tipados o contratos temporales externos gestionados sin solicitar edición manual. `preview` combina planes hijos y descargas, no ejecuta login ni consultas remotas. Exportación exclusiva es una operación explícita distinta.

Etapas: validar/importar → preparar herramientas → seleccionar/clonar checkout → preparar configuración/integración → guiar autenticación cuando requerida → comprobar capacidades → reporte. El plan padre vincula los hashes de planes hijos, permisos y destinos. La aprobación humana cubre exactamente esa revisión; no duplicar confirmaciones internas cuando están cubiertas. Cambios de alcance requieren nueva revisión; OAuth, confianza del host y permisos del SO siguen siendo interacciones externas independientes.

Registrar journal antes de cada mutación, verificar drift por etapa, conservar backups/lock/ownership y no afirmar rollback transaccional de operaciones externas. Un login cancelado permite conservar `prepared` local y reanudar la fase remota. Una clonación incompleta o instalación de herramienta se recupera solo dentro de la raíz propia verificada. La baseline HU requiere checkout limpio: los recursos preparados deben integrarse mediante commit local revisado o un mecanismo ya compatible; se comunica y registra ese paso en el plan, sin push implícito.

### 5. Databricks y autenticación guiada

Para capacidad Databricks, usar CLI ZIP oficial Windows amd64 fijado y verificado en la instalación de usuario. Mantener perfil/host seleccionados en binding externo; ejecutar login OAuth nativo únicamente tras autorización de la fase. Mostrar qué navegador/perfil configurar y comprobar identidad/conectividad mediante lectura seleccionada. No pedir PAT/password al chat ni copiar credenciales; redactar stdout/stderr y evitar argumentos sensibles.

GitHub privado, Git autenticado y Databricks pueden requerir interacción humana. Login válido no acredita permisos de jobs ni fixture compatible: esos requisitos siguen separados. Ninguna comprobación ejecuta notebooks/jobs, crea tablas o modifica workspace por defecto. Referencias: [CLI ZIP](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/cli/install) y [OAuth U2M](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/auth/oauth-u2m), consultadas 2026-10-14.

### 6. Estado de capacidades y errores

Estados por capacidad: `available`, `blocked`, `not_checked`, `unsupported`; distinguir recurso preparado de evidencia observada. Cada observación tiene identidad, versión, timestamp, prueba y vigencia. La Skill entrega requisitos pendientes y HU local/remota admisible. `certified`, `release_allowed` y gates de publicación se derivan de sus validadores existentes, jamás del setup exitoso.

Errores de la nueva fachada: `invalid_input`, `identity_mismatch`, `access_denied`, `tool_unavailable`, `download_integrity_failed`, `skill_discovery_pending`, `auth_pending`, `permission_conflict`, `plan_stale`, `owned_resource_conflict`, `recovery_required`. Categorías CLI nuevas: 0 éxito, 2 entrada inválida, 3 capacidad bloqueada, 4 conflicto/precondición, 5 infraestructura, 6 recuperación requerida; conservar los códigos de adaptadores legacy en detalles y no modificar sus contratos. El reporte parcial también conserva estos motivos por etapa.

Los TOML son configuración de agentes nativos, no procesos independientes ni sandbox por rol. La documentación actual requiere `name`, `description` y `developer_instructions`, y los subagentes heredan permisos del padre. El renderizador debe detectar el formato soportado y rechazar/adaptar explícitamente formatos anteriores sin instalar claves ignoradas. Referencia: [Subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents), consultada 2026-10-14.

## Risks / Trade-offs

- Descargas/antivirus/administración restringidos → manifiesto fijado, kit offline y bloqueo explícito; no garantía de instalar en todo host.
- Cambios en descubrimiento/formato Codex → prueba de compatibilidad por versión y evidencia real de invocación, sin depender de rutas internas.
- Un usuario interpreta `AGENTS.md` como aislamiento → informe y comprobaciones separadas; permisos efectivos pertenecen al host.
- Plan compuesto abarca efectos no reversibles como login → journal por fase y recuperación conservadora; credenciales nativas quedan administradas por su herramienta.
- Dos clientes comparten runtime, pero no identidad → registro genérico sin reglas cliente y binding/estado externos separados.
- Candidato no certificado → documentación y gate visible; aceptación del nuevo flujo no reemplaza pendientes de 06–08.

## Migration Plan

1. Añadir contratos/fachadas y recursos nuevos, con pruebas sobre v1 intacto.
2. Construir kit candidato fijado; probar instalación en entorno aislado y después otra máquina real sin Python del producto.
3. Migrar únicamente mediante un plan explícito: preservar v1, resolver alcance positivo y registrar binding local nuevo.
4. Verificar setup desde chat con insumos completos y parciales, cliente con instrucciones personalizadas y dos clientes. Guardar protocolo/evidencia sin secretos.
5. Update/recover conserva instalación previa y datos; remover solo recursos propios intactos. No activar 10 hasta verificar las interfaces del setup; no publicar release hasta satisfacer sus gates.
