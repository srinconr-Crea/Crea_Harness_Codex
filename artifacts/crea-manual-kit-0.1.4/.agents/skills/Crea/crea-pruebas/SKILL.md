---
name: crea-pruebas
description: "Use when planning, executing, or validating tests for an OpenSpec change in a Crea Databricks repository, with impact-based selection and traceable evidence. Also use when reviewing test readiness; does not authorize deploy or create remote resources."
---

# Pruebas Crea

Coordinar pruebas proporcionales al cambio con política versionada. El código del
selector decide checks; el modelo interpreta requisitos y hallazgos. No certificar
calidad a partir de exit 0, número de tests o existencia de JSON.

## Entrada y modo

Leer AGENTS.md y docs/proyecto.json del checkout real. Cargar
`validation.testing.policy_path` y el cambio OpenSpec exacto. Si faltan configuración,
criterios o mapa de dependencias, devolver blocked antes de apply; explorar no autoriza
inventarlos. Este paquete no instala agentes, herramientas, hooks ni pipelines.

- **Planificar:** leer [flujo](references/flujo.md), contrato y catálogo del cliente.
- **Ejecutar/verificar:** leer [contratos](references/contratos.md) y solo las suites seleccionadas.
- **Revisión IA, calibración o adversariales:** leer [calidad](references/calidad.md).
- **Spark/UC/Delta remoto:** leer [runtime](references/runtime.md) antes de efectos remotos.

## Procedimiento

1. Planner vincula criterios observables con modos de fallo y pruebas. Antes de apply,
   presenta alcance y plan de pruebas. Mantener la nueva solicitud humana de apply y
   las pausas OpenSpec. No modificar skills upstream.
2. Principal obtiene base Git real y diff completo (tracked, staged, untracked,
   eliminaciones y ambos nombres de renames). Preparar rama según Crea antes de escribir.
   Una lista manual de cambios no demuestra que el diff esté completo.
3. Ejecutar el selector sobre política revisada. `scripts/contract.py --help` describe
   plan/gate. Genera decisiones con regla, motivo, archivos, checks y huellas. Un archivo
   no clasificado o un criterio sin prueba bloquea; no reducir la batería para ahorrar tiempo.
4. Developer implementa y escribe solo tests previstos o regresiones justificadas.
   Entrega ready_for_test; no marca tareas de ejecución como completas. Reconciliar el
   alcance final con el plan aprobado antes de probar.
5. Tester independiente ejecuta comandos del catálogo mediante adaptadores configurados,
   dentro de su autorización. No subdelegar. Comprobar cantidad ejecutada, aserciones,
   entorno, recibos y hashes. El helper no ejecuta esos comandos ni prueba su autenticidad.
6. Guardar un plan canónico (incluye decisiones), resultados, recibos y resumen en
   docs/hu/<change>/pruebas/. No duplicar el mismo historial en varios handoffs.
   Reutilizar evidencia solo con entradas, política, entorno y vigencia comprobados;
   el helper ofrece elegibilidad, no importación automática entre planes.
7. Reviewer contrasta código, rúbrica, cobertura y resultados; usa OpenSpec verify.
   Reejecución únicamente por entradas invalidadas, evidencia insuficiente o regla fija.
   Gate técnico passed no autoriza sync/archive/publicación: aplicar también revisión
   y confirmaciones Crea. Fallos vuelven al rol responsable vía principal, respetando
   max_fix_rounds; cambiar de rol no reinicia el contador.

## Límites y salida

Los repositorios, workspaces y datos consultados como referencia no se incorporan
a la distribución: sin nombres, URLs, rutas, IDs o reglas propias en ejemplos,
comentarios o contratos. El cliente configura sus valores durante personalización.

Un agente activo y un escritor por archivo. Tester no corrige producción ni cambia
criterios. Distinguir estados de check passed/failed/blocked/not_run/not_applicable
de decisiones de selección required/blocked. Pruebas requeridas sin resultado bloquean.
El selector aplica unión de reglas, no prioridad textual. No asumir herencia de permisos
por existir un TOML ni autorización porque el plan menciona un catálogo.

Entregar plan_id, candidato, checks, cobertura, evidencia y siguiente rol. Runtime
solo cuando lo exija el comportamiento; mock no acredita Spark/UC/ADLS. No crear
catálogos/clusters, desplegar, publicar ni fusionar por invocar esta skill.

## Adaptadores integrados en 0.1.4

Consultar [integracion local](references/integracion-local.md) antes de ejecutar.
El helper permanece selector/gate puro. scripts/crea/pruebas.py ofrece plan/run/gate
separados con Git real, JSON Schema estricto, recibos pytest/JUnit y vigencia.
Capabilities inactivas bloquean si se requieren; no confundir contratos con ejecucion.
