# Observabilidad y evaluación manual

Los contratos ActivityEvent, UsageObservation, EvalProfile, EvalRun, EvalScore,
EvalInput y UsageInput v1 son independientes de onboarding, HU y validación v1.
Los schemas se distribuyen con el wheel y en schemas/. No se instalan hooks ni
se ejecuta un motor LLM. Los comandos leen un JSON y emiten un reporte sanitizado;
no modifican clientes, configuración global, ni sus fuentes. Guardar reportes
por cliente/HU/intento en el directorio de evidencia externo seleccionado.

## Actividad y uso

`harness usage report --input observaciones.json --json` devuelve status=partial
y código 0 si el documento es válido: es un reporte local comprobado con uso
unavailable. Cada evento lleva cliente, HU, intento, rol, timestamp con timezone,
source, event_id (clave idempotente), kind y status. Se aceptan fuentes declaradas
harness-local o desktop-manual. La cobertura es submitted_events_only;
hooks_certified=false. Delegaciones, retries, pruebas, ejecuciones remotas y
duraciones se cuentan por tipo; no se infieren sucesos ausentes.

Duplicados idénticos cuentan una vez. Cambiar contenido bajo la misma clave
rol/event_id produce event_id_conflict; mezclar cliente/HU/intento produce
activity_identity_mismatch. Los payloads conservan solo mediciones numéricas,
booleanos y null; se eliminan claves sensibles y se reemplaza texto libre por
[REDACTED]. redacted=true registra esa transformación. La procedencia estructural
se conserva. Los campos de identidad rechazan credenciales reconocibles.

Desktop devuelve input/output/cached_tokens y cost_usd=null con el motivo
supported_attributable_source_unavailable. No se convierten porcentajes de cuota,
longitud de texto ni precios de API en facturación Desktop. El contrato permite
importar un recibo de sesión CLI declarado con documentación y asociación a HU,
sesión nativa y unidades explícitas; no lo certifica ni acepta costo monetario.
El adaptador Desktop entregado usa exclusivamente unavailable. No hay adaptador
de facturación ni inferencia de cobertura total de hooks.

Fuentes revisadas el 2026-10-13:
[plugins oficiales](https://developers.openai.com/plugins/build/plugins) documentan
hooks sujetos a revisión/confianza y scripts presentes en el entorno. No hay
certificación local de esos hooks en este incremento.
[observabilidad de Agents API](https://developers.openai.com/api/docs/guides/agents-api/observability)
describe consumo de sesiones de esa API; no certifica una sesión Desktop existente.
El contrato del tool get_usage_limits disponible en esta sesión declara alcance
de cuenta. Estas fuentes no establecen atribución a la HU actual; unavailable es
el resultado del adaptador, no una afirmación de que todo Desktop carece de hooks.

## Ejecutar un protocolo manual

Preparar el protocolo sin invocar modelos:

```powershell
.\.venv\Scripts\python.exe scripts/prepare_evaluation_protocol.py
harness eval validate --input docs/evidence/observability-evals/pending-batch.json --json
harness eval report --input docs/evidence/observability-evals/pending-batch.json --json
```

El usuario eligió Luna/medium para baseline y candidate. El nombre Luna es la
preferencia solicitada; su identificador y versión efectivos aún no se verifican.
El protocolo contiene 21 casos disponibles de 01–06, tres repeticiones por perfil,
126 ejecuciones pendientes. E21/E22/E23 de 07 quedan not_run fuera del gate 06.
El CLI rechaza milestones 07/08 hasta que esos incrementos estén disponibles.
Los catálogos originales de diseño mantienen observed_output/scores=null.

1. Copiar el batch a estado externo; separar operativamente golden y holdout.
   development selecciona solo golden; promotion incluye holdout. No usar holdout
   para ajustar instrucciones. El catálogo público de diseño no demuestra que un
   conjunto real sea independiente. Reservar el conjunto de promoción y registrar
   quién accedió a él antes de capturarlo; el runner impide importarlo en development.
2. Congelar dataset, kit, roles, prácticas, configuración, runtime, herramientas,
   modelo y esfuerzo efectivos. Capturar la configuración real de Desktop y su
   versión; actualizar ambos perfiles y configuration_evidence_ref con una referencia
   al recibo externo revisado. Recalcular config_sha256 y profile_sha256 usando
   SHA-256 de JSON canónico (claves ordenadas, separadores compactos, UTF-8).
3. Presentar al rol únicamente tarea/input del caso y fixture sintética, sin su
   oráculo. Ejecutar tres conversaciones independientes por caso/perfil con
   configuración congelada. Registrar hora, duración, transcript/screenshot y
   acciones/artefactos. No usar resultados pytest como respuestas de agentes.
4. Un anotador revisa el output y las acciones contra cada check del catálogo.
   En casos human_annotation_required la etiqueta debe ser human; no basta una
   declaración automática. Anotar check_id/status/evidence_ref/annotator/reason.
   Un estado blocked/not_run permanece pendiente aunque otros checks pasen.
   Registrar observed_defects, incluidos falsos hallazgos del control limpio.
5. Sanitizar etiquetas y razones antes de exportarlas. EvalRun referencia el
   artefacto de anotación por artifact_ref y artifact_sha256; este hash corresponde
   al JSON canónico de output (observed_defects/checks). El transcript original y
   las capturas se conservan externamente y el anotador mantiene la asociación a
   esa referencia. El runner comprueba coherencia del recibo, no autenticidad de
   capturas ni honestidad del anotador. simulated=true en todos los dobles.
6. Añadir runs con run_id/case_id/role/profile_sha256/repetition/surface/mode,
   status/observed_at/duration_ms/artifact_ref/artifact_sha256/output/simulated.
   `harness eval run --input batch.json --json` importa y puntúa esos recibos;
   no inicia una conversación Desktop. `report` reconstruye el mismo gate.

run con execution_mode=automatic devuelve blocked sin invocar APIs privadas o
motor alternativo. validate comprueba contratos/versiones/coherencia y devuelve
valid (código 0); eso no promueve una configuración. run/report devuelven 1 cuando
el gate está blocked; entradas inválidas devuelven 2 sin imprimir los datos.
budget_runs limita el tamaño del lote explícito; no equivale a presupuesto de tokens.

## Scoring y promoción

artifact-review-v1 produce un score por check, usando la rúbrica del catálogo,
la anotación ligada al artefacto y comparación exacta de known_defects. Reporta
false_positives y missed_defects; una diferencia falla checks críticos. El gate
exige todos los críticos, >=90% de no críticos y todas las repeticiones completas.
Un recibo simulated, superficie distinta, hash stale, repetición duplicada o
configuración sin evidencia no puede promover. Las anotaciones LLM se bloquean:
no se entrega juez calibrado; ese componente es opcional y no sustituye checks.

El reporte compara perfiles solo con dataset/kit/runtime/herramientas/superficie
constantes, muestra matriz de rol/modelo/esfuerzo/caso/repetición, tasas, falsos
hallazgos, duración media y varianza. Sin duraciones observadas muestra null.
Consumo desconocido permanece null con motivo. certification=false indica que
un gate sobre recibos manuales no certifica automáticamente Desktop ni publica.

## Errores principales

| Código | Causa |
| --- | --- |
| invalid_observation_document | Campos/version/timestamp inválidos, secretos estructurales, duplicados JSON, NaN o límites excedidos |
| activity_identity_mismatch / event_id_conflict | Mezcla de identidad o replay alterado |
| eval_resource_version_mismatch | Dataset/kit no coincide con recursos instalados |
| incomparable_profiles | Cambian condiciones que deben ser constantes |
| unknown_profile / execution_surface_mismatch | Hash de perfil o superficie incorrectos |
| holdout_reserved / case_outside_milestone | Caso incompatible con propósito/milestone |
| eval_budget_exceeded / duplicate_repetition | Presupuesto insuficiente o repetición duplicada |
| milestone_not_available | Incremento 07/08 aún pendiente |

Esta implementación entrega infraestructura y protocolo. Sin ejecuciones manuales
reales no se satisface la tarea 2.4 ni el criterio de salida completo de 06; 07
permanece sin habilitar. Ver docs/evidence/observability-evals-verification.md.
