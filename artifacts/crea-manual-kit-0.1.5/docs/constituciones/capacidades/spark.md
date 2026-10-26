# Reglas Spark iniciales

Estado: active
Revisión: 1

### CREA-SPARK-001
Aplicación: cambios que dependen de semántica de ejecución Spark.
Obligación: identificar versión/entorno compatible y aportar evidencia adecuada al comportamiento.
Fundamento: un mock local no demuestra ejecución distribuida o semántica específica de runtime.
Evidencia: criterios y plan con entorno, versión y recibos de la ejecución requerida.
Comprobación: review
Excepciones: si falta runtime/adaptador requerido, registrar blocked; no sustituirlo por un mock.

Fundamento local y ejemplos: docs/buenas-practicas/spark.md. No fijar números universales de
particiones o tolerancias sin contrato del proyecto. Runtime/Spark permanece inactivo de fábrica.
