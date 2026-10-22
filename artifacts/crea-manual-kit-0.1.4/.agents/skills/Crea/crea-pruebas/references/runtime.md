# Entorno mínimo y runtime

| Necesidad observable | Entorno mínimo que puede probarla |
|---|---|
| Parsing/contrato puro, esquemas JSON, AST, SAST | Python/herramienta local configurada |
| Transformación DataFrame sin servicios de plataforma | Spark local compatible, datos sintéticos y esquema explícito |
| API/semántica DBR, dbutils, Unity Catalog, ADLS o permisos | Integración remota en entorno aprobado |
| Job desplegado y dependencias operativas | Ejecución controlada del recurso del candidato, con autorización |

Spark local prueba ejecución Spark; no prueba UC/ADLS/identidad remota. Un mock prueba
contrato local, no semántica Spark. Bundle validate verifica configuración, no datos.
No crear un clúster/catalogo por cada HU: usar un entorno aprobado disponible cuando
sea suficiente, con aislamiento por schema/ruta/run_id y límites de tiempo/costo.
SQL puede usar warehouse existente autorizado; no demuestra una ruta Python/RDD.

Antes de cualquier ejecución remota, obtener o comprobar: perfil/host/identidad,
target, versiones efectivas, APIs necesarias, compute compatible, catálogo/schema,
rutas permitidas y efectos, duración/presupuesto y procedimiento de inventario/cierre.
RDD exige compatibilidad explícita; no asumir que serverless/standard soportan la
misma API que un compute dedicado. No copiar IDs/rutas de ejecuciones de referencia al kit.

Planificar primero comprobaciones de lectura; smoke corto de carga de módulos y
guardas antes de una suite larga. Crear fixtures solo dentro del alcance aprobado.
Comprobar límites de URI y evitar tocar directorios ancestro de tablas UC. No ocultar
errores de permisos como «ruta no encontrada». No reutilizar un namespace con estado
desconocido ni borrar recursos previos para hacer pasar el test.

El notebook/runner recibe un manifiesto aprobado de entorno y lo valida antes de
efectos. Guardas, managed/external roots, serialización y preflight son infraestructura
de pruebas reutilizable; regresiones reales de ella se conservan como tests locales.

Recibo runtime: ID de run/task, estado terminal, SHA del código/notebook cargado,
DBR/Spark/Delta/Python, parámetros, catálogo/schema/root, assertions por criterio y
referencia a autorización. Resultado completo sin aserciones faltantes ni skips de
escenarios requeridos. No declarar «pasó» porque el notebook no lanzó excepción.

Inventario incremental aun ante fallo: recurso creado/preexistente, ID/ruta, estado,
persistencia y limpieza acordada. Terminar solo compute propio autorizado; conservar
recibos reales. No detener warehouse/clúster compartido por defecto. Borrar tablas,
schemas o catálogo requiere alcance específico; un test no concede permiso de limpieza.

Respetar la regla vigente del cliente sobre pruebas de runtime Spark.
Refinarla por requisitos de plataforma es cambio de política revisado,
no una excepción que decide Tester para ahorrar tiempo.

Referencias técnicas a verificar según versiones:
- https://spark.apache.org/docs/3.5.9/api/python/getting_started/testing_pyspark.html
- https://learn.microsoft.com/en-us/azure/databricks/notebooks/testing
- https://learn.microsoft.com/en-us/azure/databricks/compute/serverless/limitations
- https://learn.microsoft.com/en-us/azure/databricks/compute/standard-limitations
