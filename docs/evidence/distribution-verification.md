# Verificación del incremento 08 — distribución candidata

Verificación final: 14 de octubre de 2026, America/Bogota.
Base: `ce75d69`, versión 0.1.0; implementación de 07 en `af9d645`.
Autorización de desarrollo anticipado: 13 de octubre de 2026.

## Resultado local y aceptación

Ocho de trece tareas cumplen su alcance local: 1.1, 1.2, 2.1–2.4 y 4.1–4.2.
El cambio **permanece activo**, por decisión explícita del usuario. Las tareas
3.1–3.4 y 4.3 están abiertas. Sync, commit y push conservan
`certified=false`, `release_allowed=false`, `publication_allowed=false` y
`next_increment_enabled=false`; no constituyen un release.

Se implementaron contratos v1 independientes, schemas raíz/paquete, ejemplos,
manifiesto candidato con 263 recursos fijados, seis dependencias Windows cp313
versionadas con SHA/licencias, bootstrap y launcher offline revisables,
update preview/apply/recover, ownership y lock por cliente, backups/journal
externos y gate de aceptación ligado al candidato.

La instalación inicial declara ownership explícito. Update solo cambia recursos
gestionados con hash intacto; rechaza personalización, drift y destinos ajenos.
Recover restaura objetos propios intactos y conserva estado/evidencia. El gate
exige once protocolos, evaluaciones Desktop Luna/medium de baseline y candidate,
144 repeticiones requeridas, certificado Desktop y configuraciones verificadas
por hashes. Un gate de aceptación aprobado no autoriza una operación PR.

## Evidencia comprobada

- Suite general: 534 pruebas aprobadas en 1013.69 s, sin fallos. Se ejecutó antes
  de incorporar algunas regresiones finales; no se atribuyen a ese run.
- Suite final del incremento: 52 pruebas aprobadas. Incluye T22 sobre TOML
  personalizado, hashes/ownership, locks, recuperación tras fallo, backups
  adulterados, planes rehasheados, launcher sin efectos y rechazo de junctions,
  superficie CLI, evals simuladas y configuración/candidato incorrectos.
- Wheel construido e instalado offline en `.test-data/d2` mediante launcher;
  smoke con `python -I` desde fuera del source: seis schemas, 263 recursos,
  seis dependencias, recursos anteriores conservados y release bloqueado.
- `openspec validate 08-pilot-and-reproducible-distribution --strict` y validación
  de todas las main specs; seis requisitos y quince escenarios sincronizados.
- Trazabilidad de los quince escenarios a tests y protocolos en
  [distribution-verification.json](distribution-verification.json).

La primera suite en sandbox tuvo 506 aprobadas y un fallo del control positivo
del filtro Git de una fixture histórica. Fuera del sandbox, esa prueba pasó y
la suite completa pasó; no se cambió el control ni el código anterior.
La primera instalación falló por creación de bytecode en rutas profundas
Windows. El launcher final usa `--no-compile` para recursos pasivos y un venv
local corto; el nuevo intento y el smoke pasaron. No se modificó soporte de
rutas ni execution policy global. El proceso de prueba usó RemoteSigned local.

La revisión independiente detectó y se corrigieron: límite de caracteres frente
a bytes UTF-8, evaluaciones CLI confundidas con Desktop, identidad de roles/
configuraciones no ligada al certificado, conflicto del lock ocultado mediante
rehash y destino del launcher fuera del proyecto/junction. Se conservaron
regresiones negativas. Las fixtures del gate prueban el importador; no son
capturas reales ni evidencia de aceptación de agentes.

## Verificación OpenSpec

| Dimensión | Resultado |
|---|---|
| Completeness | 8/13 tareas; cinco pendientes reales obligatorios |
| Correctness | Seis requisitos trazados; mecánica local comprobada, aceptación Desktop/remota y segundo entorno no verificados |
| Coherence | Contratos independientes, operaciones explícitas, integridad/confinamiento Windows y evidencia separada; v1 conservado |

Cinco incidencias críticas de completitud: completar 3.1 (aceptación de 06/07),
3.2 (alpha/beta reales), 3.3 (piloto por harness), 3.4 (aceptación e instalación
en otro equipo) y 4.3 (criterio de salida y certificación final).
La evidencia local no permite archivar como incremento aceptado.

No verificado: comportamiento real de roles/modelos/herramientas, sandbox
compatible, recorrido real de publicación/reconciliación y ejecución del piloto
en otro equipo. El protocolo conserva once recorridos `not_run`, 144 capturas
de 06/07 pendientes y cero ejecuciones reales nuevas. Se requiere seleccionar
recursos/autoridad sintéticos y observar resultados reales para cerrarlos.

El piloto manual NaturaPet conserva 25 tests remotos y PR draft como antecedente;
no satisface los protocolos del harness. No se alteran recibos históricos 06/07,
catálogos de calidad `not_run`, clientes productivos o configuración global.

Ver [guía y contratos](../pilot-and-distribution.md),
[smoke instalado](distribution-wheel-smoke.json),
[protocolo pendiente](distribution/protocols.json) y
[gate real del candidato](distribution/release-gate.json).
