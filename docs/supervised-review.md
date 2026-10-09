# Preparación y revisión supervisada

La preparación supervisada permite trabajar con limitaciones aceptadas sin
afirmar certificación estricta. `assess_certificate` conserva sus reglas: un
revisor con escritura efectiva sigue en conflicto. La aceptación del operador
no habilita fases que requieran esa capacidad.

## Procedimiento

1. Revisar/aplicar la integración y conservar su plan/journal externos.
2. Conservar observaciones Desktop por rol con versión, procedencia y evidencia.
   Modelo solicitado, contrato runtime y auto-reporte son fuentes distintas.
   No usar `load_desktop()` pasivo para inferir configuración efectiva.
3. Capturar el candidato antes de delegar la revisión, incluyendo todas las
   rutas candidatas autorizadas. Directorios incluyen descendientes; archivos
   ausentes se registran para detectar creaciones. La captura no incluye todo
   el repositorio automáticamente.
4. El operador revisa las limitaciones y registra `SupervisedAcceptance` con
   cliente/checkout, catálogo, hash del snapshot y evidencia. Se debe conservar
   la aprobación humana de origen. El archivo es una declaración manual, no
   firma ni mecanismo de autenticación.
5. Ejecutar preparación supervisada y luego revisión del candidato identificado.
   Comparar de nuevo antes de aceptar el resultado. Drift bloquea aceptación;
   no se revierte ni borra lo que cambió el revisor.

```powershell
harness review-snapshot --path C:/Clientes/demo --policy C:/Config/policy.json --binding C:/Config/binding.json --catalog C:/Config/catalog.json --observations C:/Evidence/desktop.json --scope src --scope tests --out C:/Evidence/before.json --json
harness supervised-prepare --path C:/Clientes/demo --policy C:/Config/policy.json --binding C:/Config/binding.json --catalog C:/Config/catalog.json --observations C:/Evidence/desktop.json --snapshot C:/Evidence/before.json --acceptance C:/Evidence/acceptance.json --plan C:/Evidence/integration.json --json
harness review-compare --path C:/Clientes/demo --policy C:/Config/policy.json --binding C:/Config/binding.json --catalog C:/Config/catalog.json --observations C:/Evidence/desktop.json --snapshot C:/Evidence/before.json --json
```

`--require auditor:permissions` exige esa capacidad observada y bloquea si está
en conflicto. Lo mismo ocurre con una capacidad desconocida. Sin acceptance,
la preparación devuelve blocked; no se infiere aprobación desde los archivos.
`supervised-prepare` revalida integración aplicada intacta y candidato actual,
además de la aceptación. Una modificación posterior a ese comando exige nueva
comparación; el resultado no autoriza escrituras ni publicación.

## Contratos y límites

`CandidateSnapshot` y `SupervisedAcceptance` son contratos estrictos separados
con schema_version 1 y schemas empaquetados. El snapshot guarda identidad,
rutas, tipo, hash de contenido y ausencias, no bytes de negocio. Incluye hashes
de descriptor/política/binding y del certificado (metadatos/version/observaciones).
Modificar identidad/configuración/evidencia invalida la revisión. El catálogo
se identifica por hash; las limitaciones aceptadas deben cubrir cada check
no observado. La selección de los roles activos debe tener fuente Desktop.

Captura: máximo 32 scopes sin solapamientos, 256 entradas, 2 MiB por archivo y
16 MiB de contenido total. Rechaza traversal, enlaces/junctions/hardlinks,
rutas denegadas, `.git`, `.codex`, `.agents`, `.harness` y `evidence`. Excluir
evidencia/estado del candidato evita que guardar el informe provoque drift.
Exportar snapshot crea exclusivamente un archivo externo; destino existente
o solapado se rechaza. Sin exportación no hay escrituras.

Los handles Windows fijan padres y archivos durante la captura; se comprueba
la lista de hijos y ausencias al finalizar. No hay snapshot atómico del volumen
ni aislamiento durante toda la revisión. Solo detecta diferencias persistentes
en scopes seleccionados; no detecta necesariamente una modificación restaurada
ni archivos ajenos al candidato. Los hashes no impiden que un operador altere
declaraciones y vuelva a generar aceptación; se conserva la evidencia de origen.

Los tres comandos usan schema_version/command/status/checks. Código 0 indica
comprobación local lista (puede conservar certified=false), 1 bloqueo/conflicto
y 2 entrada inválida. Errores nuevos: supervised_identity_mismatch,
supervised_evidence_mismatch, integration_not_applied, candidate_scope_denied,
candidate_changed_during_capture, candidate_too_large e invalid_candidate_scope.
No cambian los contratos/comandos v1 ni `desktop-check`.

## Evidencia de 02

El cliente sintético produjo preparación supervisada lista y certificado false.
Una fase que exige aislamiento de auditor quedó blocked. E03 tiene tres
respuestas compatibles con sus checks; E04 omite tests de null en dos de tres.
El usuario aceptó este defecto para uso supervisado: se conserva en
[human-annotation.json](evidence/desktop-runtime-2026-10-09/human-annotation.json).
No se presenta E04 como aprobado en todas las repeticiones ni como holdout
reservado. MCP/hooks y valores runtime no expuestos conservan esos límites.
