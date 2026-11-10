# Revisión independiente del cambio 0.1.9

Revisor: herramienta collaboration, tarea real `/root/final_review`; lectura independiente, sin edición ni relanzamiento de suites. No acredita rol nativo Codex ni piloto de cuatro roles.

Se contrastaron proposal, design D1-D14, siete deltas, código y documentación del staging nuevo. Conteo directo: 47 requisitos/90 escenarios. Las superficies de implementación están presentes; la revisión encontró los siguientes defectos, corregidos por el implementador con evidencia conservada:

| Hallazgo | Corrección | Evidencia |
| --- | --- | --- |
| P1: simulación HEAD/Q podía certificar cambios sin commit | `SIMULATION_COVERS_HEAD_ONLY`, Git partial; lee contratos actuales del checkout | red-simulation-review-binding.xml → green-simulation-offline-guards.xml |
| P1: lectura Git podía invocar fsmonitor, lazy fetch o refrescar índice | flags fsmonitor=false; GIT_NO_LAZY_FETCH=1 y GIT_OPTIONAL_LOCKS=0 en ambos wrappers | red-offline-guards-collected.xml → green-simulation-offline-guards.xml; green-semantic-bounds-render.xml |
| P2: identidad Azure rechazaba proyecto/repo iguales | identidad posicional sin uniqueItems | red-offline-guards-collected.xml → green-simulation-offline-guards.xml |
| P2: vista humana omitía refs canónicas | render incluye snapshot e informe, con hashes | red-semantic-bounds-render.xml → green-semantic-bounds-render.xml |
| P2: refs semánticas reiniciaban presupuesto y podían leer rutas ajenas | presupuesto acumulado y unión de review_paths pertinente | red-semantic-bounds-render.xml → green-semantic-bounds-render.xml; green-unknown-check-bounds.xml |

El implementador cerró adicionalmente la lectura de contratos sin commit, resolución de revisión de dependencias y checks recomendados desconocidos. No se cambió una spec para aceptar estos defectos. No se solicitó otra revisión del mismo diff: las pruebas de regresión y la batería final de Tester verifican las correcciones.

La revisión exige matriz durable de escenario→implementación→prueba/inspección→evidencia y paquete final verificado. full-kit-initial.xml fue favorable antes de las últimas correcciones; no representa el estado final. Los intentos históricos fallidos se conservan y no se suman como resultados favorables.

Límites previstos: no servicios Azure/Databricks reales, no hooks o agentes nativos observados, no piloto real con dos personas. La integración en quality y promoción a test permanecen humanas. Ningún cambio rastreado observado en 0.1.3-0.1.8; integridad final se comprueba mediante baseline y empaquetador.
