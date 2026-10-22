# Buenas practicas de Databricks y notebooks

## 1. Alcance
Aplicar a las partes de la HU que usen esta herramienta. Sintesis revisada el 2026-10-16;
comprobar compatibilidad con las versiones del proyecto. Las fuentes son referencia tecnica;
las convenciones Crea se identifican aparte. No son transcripciones de los articulos.

## 2. Practicas y fundamento

- Versionar notebooks y extraer logica reutilizable a modulos: facilita pruebas y reduce
  dependencias del orden de ejecucion interactivo. Declarar dependencias compatibles con DBR. [1]
- Mantener la entrada del notebook breve y separar transformaciones de visualizacion y
  ejecucion programada. Validar la ejecucion completa, no solo celdas aisladas. [1]
- Para tablas nuevas, evaluar tablas administradas por Unity Catalog, optimizacion predictiva
  y liquid clustering segun disponibilidad y carga. No copiar ajustes heredados sin revisarlos. [2]
- No editar los Parquet internos de Delta directamente: el log transaccional gobierna su estado.
  Leer la tabla y aplicar filtros; no eludir el log leyendo rutas de particion como Parquet. [2]
- Evitar cache Spark indiscriminada sobre Delta; puede impedir skipping adicional y generar
  inconsistencias de acceso. Evaluar las optimizaciones disponibles antes de cachear. [2]


## 3. Aplicacion y evidencia Crea

Registrar runtime, perfil, target y catalog/schema antes de ejecucion remota. Para ingestas,
definir contrato de esquema, reejecucion, duplicados y evolucion como decisiones del proyecto.
La autenticacion local no autoriza por si sola desplegar o modificar datos.


## 4. Fuentes consultadas

- [1. Notebooks: ingenieria de software](https://learn.microsoft.com/es-es/azure/databricks/notebooks/best-practices).
- [2. Delta Lake](https://docs.databricks.com/aws/en/delta/best-practices).
- [Indice original de practicas](https://docs.databricks.com/aws/en/getting-started/best-practices): es un indice; sus paginas especializadas aportan el contenido tecnico.


## 5. Configuracion, excepciones y extensiones
Registrar excepciones justificadas en docs/contexto-proyecto.md, comandos en
docs/proyecto.json → validation.testing.policy_path (catalogo unico; required_checks solo IDs) y especialidades en extensions.
Agregar reglas propias aqui con fundamento y evidencia esperada. Una recomendacion
de rendimiento necesita medicion; no cambiar resultados funcionales para acelerarlos.
