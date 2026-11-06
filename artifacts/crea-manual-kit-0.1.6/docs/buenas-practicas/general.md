# Buenas practicas comunes

## 1. Alcance
Aplicar a las partes de la HU que usen esta herramienta. Sintesis revisada el 2026-10-16;
comprobar compatibilidad con las versiones del proyecto. Las fuentes son referencia tecnica;
las convenciones Crea se identifican aparte. No son transcripciones de los articulos.

## 2. Practicas y fundamento

- Definir entradas, salidas y criterios antes de implementar. En datos, documentar grano,
  claves, tipos y tratamiento de errores; evita que codigo correcto resuelva otro problema.
- Vincular pruebas al candidato revisado y conservar su resultado real. Una prueba no
  ejecutada permanece not_run; falta de entorno/permisos se registra como blocked.
- Mantener codigo, configuracion y documentacion en control de versiones; revisar diffs
  pequenos y preservar cambios ajenos. No introducir secretos en evidencia ni en fixtures.
- Probar primero unidades de logica y despues la integracion pertinente. Tener sintaxis
  valida o un plan legible no demuestra comportamiento correcto en el entorno objetivo.
- Separar el contexto de negocio del procedimiento reutilizable. Leer solo las referencias
  necesarias para la tarea y mantener una fuente de verdad para rutas y comandos.


## 3. Aplicacion y evidencia Crea

Planner define checks concretos; Developer implementa; Tester ejecuta y registra
recibos; Reviewer contrasta codigo, cobertura y criterios sin repetir la bateria por rutina.
El registro docs/hu/<change>/evidencia.md es manual y no constituye un control tecnico de permisos.


## 4. Fuentes consultadas

- [CI/CD Databricks](https://docs.databricks.com/aws/en/dev-tools/ci-cd/flows): control de versiones y pruebas por etapa.


## 5. Configuracion, excepciones y extensiones
Registrar excepciones justificadas en docs/contexto-proyecto.md, comandos en
docs/proyecto.json → validation.testing.policy_path (catalogo unico; required_checks solo IDs) y especialidades en extensions.
Agregar reglas propias aqui con fundamento y evidencia esperada. Una recomendacion
de rendimiento necesita medicion; no cambiar resultados funcionales para acelerarlos.

## Reglas de proyecto
Las obligaciones activadas y sus IDs se mantienen en docs/constituciones/README.md y documentos seleccionados; esta guía conserva ejemplos y referencias técnicas. No duplicar políticas de cliente ni activar capacidades por disponibilidad.
