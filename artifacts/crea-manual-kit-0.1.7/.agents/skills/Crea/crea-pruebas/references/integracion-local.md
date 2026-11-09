# Adaptación local 0.1.4

Carpeta fuente 0.1.0 copiada completa. Adaptadores separados en scripts/crea/testing/
invocados mediante scripts/crea/pruebas.py. Helper puro sin Git, suites o APIs.
Extensión opcional provenance enlaza Git/config/adaptadores al plan sin efectos.
Inventario de adaptaciones en docs/pruebas/INTEGRACION.json.

Referencias originales describen requisitos pendientes del paquete 0.1.0; usar
docs/pruebas/README.md y capabilities.json para el estado real integrado.
Usar CLI integrada plan/run/gate: contract.py directo no sustituye revalidación
Git/schema/recibos/vigencia. ready_for_test → ready_for_review; Reviewer consume
gate/recibos, no run automático. Untracked/fixture/config/entorno/TTL invalidados
bloquean y vuelven al responsable vía principal. Adopción entre planes inactiva:
no retocar IDs/fechas. Runtime/Spark/SAST/mutation/evals/CI requeridos sin adaptador
activo bloquean. Preservar OpenSpec/confirmaciones humanas, un rol activo, sin
subdelegación ni reinicio del contador global de rondas.
