# Compatibilidad de HU con destino del PR

Opt-in `delivery.compatibility.enabled=true`, revisado por el responsable. Sigue
informativo mediante transiciones existentes. Sin la opción no exige informes legacy.
Un control nuevo solo bloquea mediante promoción explícita; gates/autorizaciones previos
siguen vigentes y una decisión funcional necesaria se tramita como pendiente humano.

## Tres operaciones diferentes

Desde la raíz y con intérprete preparado, sustituir HU, intento y SHA por valores reales:

```powershell
python -B scripts/crea/entrega.py snapshot --repo . --change HU002 --attempt 1 --out docs/hu/HU002/compatibilidad/attempt-1/target.json
python -B scripts/crea/compatibilidad.py inspect --repo . --handoff docs/hu/HU002/handoffs/revision-1.json --target-snapshot docs/hu/HU002/compatibilidad/attempt-1/target.json
```

Snapshot es una adquisición explícita: consulta refs y puede obtener objetos en refs
auxiliares acotadas; no toca ramas de trabajo. Inspeccionar snapshots ya existentes es
offline, sin escritura por defecto, suites o instalación. Nunca usar una tracking ref
vieja como verificación actual ni crear quality si falta. Los errores de permisos/red
no significan rama libre. No hay reintentos indefinidos ni login implícito.

`simulate` es explícito y crea objetos temporales aislados bajo `.crea/tmp/`:

```powershell
python -B scripts/crea/compatibilidad.py simulate --repo . --source-sha SHA_REAL --target-snapshot docs/hu/HU002/compatibilidad/attempt-1/target.json --scratch "C:/ruta real/proyecto/.crea/tmp/HU002-1" --out docs/hu/HU002/compatibilidad/attempt-1/simulation.json
```

Requiere destino nuevo, no ejecuta merge/rebase sobre el checkout, hooks o drivers
externos. Atributos no equivalentes o Git no soportado dejan un límite explícito. La
simulación no ejecuta tests ni demuestra compatibilidad funcional.

## Revisión funcional y resultados

El inspector propone review_paths, document_refs y scope_digest. Reviewer contrasta
los requisitos/reglas y contratos en ambas revisiones, incluida dependencia inversa de
consumidores, y crea una revisión según `compatibilidad-review.schema.json`. Debe
identificar source/target/scope exactos y aportar refs de objeto/hash para contradicciones.
Con `--semantic-review` y `--simulation` se consumen esos informes; no se infiere
significado de hashes ni independencia por archivos distintos. El catálogo sigue único.

| Resultado | Acción |
| --- | --- |
| compatible | Continuar dentro del alcance comprobado con gates/aprobaciones vigentes |
| requires_review | Resolver revisión de componentes, alcance o checks identificados |
| conflict_detected | Reconciliar conflicto textual o funcional con el responsable |
| undetermined | Completar referencias, acceso o dimensión no acreditada |

Coverage complete/partial y freshness current/stale/unverified se informan aparte.
Un conflicto comprobado no desaparece porque otro análisis esté incompleto. Compatible
no garantiza ausencia universal de defectos. Sin mapa de contexto se usa Git/catálogo y
referencias disponibles, se declara cobertura limitada y no se activa el mapa automáticamente.

Casos: A, componentes independientes pueden continuar tras HU001; B, productor cambiado
identifica consumidor/checks; C, misma regla incompatible requiere decisión; D, contratos
contradictorios en archivos distintos siguen siendo conflicto con Git limpio; E, Q1→Q2
invalida la observación pertinente; F, quality ausente/inaccesible queda indeterminado.

## Evidencia, vigencia y cierre

Declarar antes del plan rutas exactas/tipos futuros en `scope.compatibility_artifacts`.
Los planes nuevos que los adoptan usan content-v3; content-v2 conserva sus contratos.
Un JSON válido por nombre no es metadata autorizada. Archivos previos se congelan por
hash; posteriores se validan por schema/identidad y no pueden esconder producción.
Obligaciones funcionales nuevas permanecen inputs y exigen reconciliar el plan.

Enlazar el informe final con hash en `evidence.compatibility`. Antes de PR, ejecutar
`entrega.py freshness --repo . --snapshot <target.json>` y exportar a un archivo nuevo
con `--change HU002 --out <ruta nueva de la HU>`; no modifica ramas. Usarlo como
`--current-target` del inspector y volver a analizar si cambió Q. El informe conserva
refs/hash de snapshot, simulación, revisión y lectura final. No sobrescribir intentos.

Avance independiente de Q no invalida automáticamente el plan local ni pide otro permiso.
Cambios funcionales o de entorno sí aplican la invalidación actual. No se importan recibos
entre planes/máquinas. Pruebas sobre H no acreditan un árbol combinado no ejecutado:
si hace falta, el equipo prepara un candidato autorizado y Tester usa plan/run/gate.
Capacidad requerida inactiva conserva blocked. Ningún informe autoriza integración o deploy.

Las referencias `observation=worktree` identifican bytes actuales (incluidos cambios sin
commit) con HEAD como ancla; `observation=git` identifica objetos de Q. Una baja del
candidato no se sustituye por el documento antiguo de HEAD. Ambas fuentes respetan
exclusiones y presupuesto. La revisión funcional debe usar la misma observación y hash.
