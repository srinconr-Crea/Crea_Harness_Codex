# Base de prácticas, tests y evals

El cambio 01 añade una API local de recursos y contratos. No añade comandos,
agentes, hooks, conectores ni ejecución Databricks. Los contratos de onboarding
v1 y la configuración global conservan su comportamiento.

```python
from harness_local.quality_resources import load_quality
from harness_core.quality import resolve_practices, definition_report

bundle = load_quality()
plan = resolve_practices(bundle.practices, 'pyspark')
print([rule.id for rule in plan.rules])
print(definition_report(bundle.evals, available_modes=set()))
```

## Contratos

`PracticePack`, `TestCase`, `TestCatalog`, `EvalCase`, `EvalCatalog` y
`PracticeExtension` tienen schemas en `schemas/` y en el paquete. El generador
`scripts/generate_schemas.py` conserva ambas copias. Los objetos definidos
rechazan campos desconocidos y coerción; `input` de un eval permite datos
sintéticos arbitrarios. Versión de schema 1; versión de contenido independiente.
Los catálogos tienen máximo 256 entradas y los documentos máximo 1 MiB.
Los loaders rechazan JSON duplicado, secretos y paths no confinados. El único
metadato exento de la detección por nombre es `hu_token_source: null`.

JSON Schema expresa forma, tipos y límites; Pydantic y la composición comprueban
además IDs únicos, referencias y conflictos entre documentos. Validar únicamente
el schema no satisface estos controles semánticos. `validate_catalogs` resuelve
reglas/fuentes/checks; `load_quality` resuelve también el fixture empaquetado.
`load_definition` lee un documento propio; `load_fixture` confina rutas relativas,
rechaza enlaces y no importa código cliente.

Errores: `invalid_quality_definition`, `document_too_large`, `duplicate_key`,
`missing_rule`, `fixture_missing`, `fixture_invalid`, `quality_resources_invalid`,
`client_mismatch`, `practice_base_mismatch`, `extension_conflict` y
`unsupported_technology`. Los loaders devuelven errores sin valores sensibles;
la API directa de modelos puede devolver ValidationError y debe manejarse antes
de mostrarlo al usuario. No se ha añadido CLI ni un nuevo contrato de exit codes.

## Extensión seleccionada de un cliente

La precedencia es base inmutable, adiciones cliente, evidencias adicionales y
excepciones técnicas revisadas del scope seleccionado. Una extensión declara
`client_id`, `base_pack_id` y `base_version`; requiere seleccionar ese mismo
cliente. No hay autodetección ni mezcla de repositorios.

`rules` solo añade IDs nuevos; `sources` añade procedencia nueva; `strengthen`
contiene `rule_id` y `additional_evidence`. No se sobrescriben ni eliminan reglas
base. Una excepción exige `rule_id`, `reason`, `scope`, `reviewed_by` y
`decision_ref`; queda registrada junto a la regla y solo se incluye en el scope
exacto. Estos metadatos declaran la revisión, no autentican al revisor: la
aprobación verificable llega con el flujo de HU del incremento 04.

La extensión no tiene campos de permisos, rutas, herramientas o bypass de
aprobación. Su texto es calidad técnica pasiva y no se interpreta como permiso.
No recibe ni altera una Policy. Un consumidor futuro debe conservar permisos y
gates separados; una frase libre no puede convertirla en autorización operativa.

## Integridad y licencia

El wheel incluye 32 reglas, 24 tests, 24 evals y el fixture sintético. Incluye
también nueve Skills oficiales y sus 110 archivos, sin modificación, bajo
`harness_local/quality_kit/vendor/`. `SOURCE.json` conserva commit, URLs,
bytes, SHA-256 y Databricks License; LICENSE/NOTICE permanecen junto al contenido.
El loader verifica manifiestos y referencias antes de entregar los recursos.
La huella comprueba integridad respecto a la distribución recibida; no es firma.
Estas copias son datos de referencia: no se instalan como Skills activas, no se
ejecutan scripts y no requieren Spark/MLflow en el runtime básico.

## Definiciones y resultados separados

Las definiciones permanecen `not_run`, con `scores` y `observed_output` null.
Un runtime requerido ausente produce reporte `blocked`, conservando ejecución
`not_run`. Tener un runtime disponible tampoco ejecuta ni aprueba un caso.
`compare_findings` es una rúbrica de conjuntos: detecta defectos omitidos y
falsos positivos; no sustituye los demás checks ni certifica un agente.

El hash del fixture fija el dataset. Los manifests fijan catálogos completos,
incluidos sus splits golden/holdout. El gate definido exige tres repeticiones,
100% de críticos y al menos 90% de no críticos; blocked/not_run no aprueban.
Los casos públicos etiquetados holdout no constituyen un conjunto reservado:
la separación operativa y ejecución del runner corresponden al incremento 06.
Workers SQL/PySpark/Databricks corresponden al incremento 05.
