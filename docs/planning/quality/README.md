# Prácticas, casos de prueba y evals iniciales

Estos recursos son **artefactos de diseño concretos**, no suites ejecutadas ni funciones disponibles en el CLI.
Se crean bajo el alcance de planificación OpenSpec. El cambio 01 ya implementa sus schemas/carga/empaquetado y composición técnica; ver ../../../docs/quality-foundation.md. 05 implementa workers y pruebas de desarrollo y 06 implementa runner/scorers de agentes.
Resultados actuales: not_run; observed_output y scores son null.

## Recursos

| Archivo | Contenido |
| --- | --- |
| practices.json | 32 prácticas SQL, Python, notebook, PySpark, YAML/DABs, CI/CD y generales; 12 fuentes |
| test-cases.json | 24 pruebas de comportamiento con input y expected independientes |
| eval-cases.json | 24 tareas de agente, ocho roles, 48 checks, split golden/holdout y defecto conocido |
| fixtures/synthetic-sales.json | Tres órdenes sintéticas, dimensiones limpia/duplicada y contrato decimal/null |
| acceptance-cases.json | Escenarios OpenSpec trazados a inputs/oráculos del contrato; ejecución pendiente |
| manifest.json | Hash/tamaño de recursos propios de diseño |

No guardar datos reales ni secretos. Los snippets de casos son entradas de evaluación, no instrucciones de ejecutar recursos remotos.

## Ejemplo y oráculo

La suma no null de las tres órdenes es 30.00 COP, en decimal. Join con dimensión única conserva tres filas.
La dimensión duplicada produce cinco filas y suma 40.00 si se hace join ingenuo; el contrato exige rechazar claves ambiguas antes de unir. Estos valores se calculan del fixture, no copiando salida del agente.
Para el caso vacío T04 el contrato local especifica 0.00, sin imponer esa política a todos los clientes.

## Protocolo de pruebas

1. Seleccionar casos por tecnología/impacto y milestone; resolver fixture y source_rules.
2. Fijar candidato, runtime/tool versions, policy/plan/practice hashes y dataset.
3. Ejecutar parsing/estático, unit, semántica e integración según ValidationPlan.
4. Comparar resultado con oráculo independiente; registrar comando/identidad/resultado.
5. Required blocked/not_run/stale impide certificación. Dobles verifican adapter, no ejecución remota.
6. SQL dialect/Delta o notebook de integración requiere runtime Databricks seleccionado; nunca ejecutar snippets con credenciales reales por defecto.

## Protocolo de evals de agentes

1. Congelar roles, instrucciones, modelo/esfuerzo, tools y dataset/kit. Crear checkout sintético por caso/repetición.
2. Entregar task/input; reglas esperadas y known_defects pertenecen al evaluador, no se revelan como respuesta esperada al agente.
3. Capturar artefactos, tool actions y salida sanitizada. No probar con credenciales/productivo.
4. Aplicar cada check con etiqueta pass/fail/blocked y evidencia. Scorers deterministas usan artefactos/acciones/worker; checks semánticos tienen rúbrica y anotación humana cuando corresponda.
5. Tres repeticiones por caso/configuración al comparar modelos. Reportar críticos por repetición, no solo promedio.
6. Gate: 100% críticos y >=90% no críticos; incompleto/bloqueado no equivale a éxito. Hallazgos falsos penalizan controles limpios.
7. Guardar mode=desktop_manual si se ejecutó en app con protocolo; automatizar solo con superficie soportada. CLI no certifica Desktop.
8. Cambio de rol/modelo/esfuerzo/práctica/tool exige baseline comparable. No invocar API facturada propia como sustituto silencioso.

Golden sirve al ajuste iterativo; holdout sirve a promoción y se reserva operativamente. Estos holdout públicos son semillas de diseño; para medir generalización real se mantiene un conjunto separado que no se use para optimizar prompts.

Casos se activan según implementation_change. En 06 se evalúan capacidades 01–06; en 07 se añaden proveedores y en 08 se exige el conjunto completo. Casos futuros permanecen not_run y no son passed del gate parcial.

## Rúbrica de anotación

Cada check requiere evidencia positiva o negativa: ruta/fragmento de artefacto, resultado worker o log de tool actions. pass significa que la conducta observable satisface el check; fail que no lo cumple o contradice el oráculo; blocked que falta una capacidad externa. Ausencia de output no demuestra “cero escrituras”: verificar snapshot/log del entorno controlado.
Anotador independiente revisa hallazgos de auditor; defectos se detectan por condición/impacto correcto aunque cambie redacción. Juicio LLM opcional se calibra con etiquetas humanas y no decide los checks críticos sin evidencia.

## Procedencia y adaptación

Las fuentes oficiales se enlazan en practices.json; Medium se consultó como referencia secundaria y no fundamenta reglas normativas. Las reglas propias del harness están identificadas como harness-design.
No imponer cache/broadcast/repartition o layout universal por artículo; recomendaciones de rendimiento son advisory hasta medir.
Snapshot upstream: ../../../resources/vendor/databricks-agent-skills/, commit ba45d10df7413de14c32937bbd584aeee17d22a2. Copias íntegras con LICENSE/NOTICE y SOURCE.json; no están instaladas. El catálogo de roles resuelve dependencias y restringe operaciones antes de activación.
