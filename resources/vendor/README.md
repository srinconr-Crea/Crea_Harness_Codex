# Recursos upstream Databricks

Snapshot solicitado para diseñar el harness, sin instalación ni activación.
Fuente: https://github.com/databricks/databricks-agent-skills
Commit: ba45d10df7413de14c32937bbd584aeee17d22a2.
Se conservan nueve Skills y todos sus archivos del manifiesto upstream, además de LICENSE/NOTICE/README/manifest.

SOURCE.json fija URLs, bytes y SHA-256 de los 110 archivos descargados. Copias originales íntegras; el cambio 01 incluye una copia pasiva íntegra en el wheel; no son Skills activas. La Databricks License se conserva y aplica al uso conectado a sus servicios; no se relicencia como MIT/Apache.

Skills: databricks-core, databricks-dabs, databricks-dbsql, databricks-jobs, databricks-python-sdk, databricks-pipelines, databricks-synthetic-data-gen, databricks-mlflow-evaluation y databricks-docs.

Selección por rol, dependency closure, compatibilidad y confianza se resuelven en 01/02 antes de instalar. Algunas Skills sugieren crear/ejecutar recursos: wrappers exigirán política/alcance propios. No ejecutar scripts/instaladores durante planificación.

Actualizar requiere nueva revisión en staging, manifiesto, revisión del diff y evals; no descargar main en runtime.
