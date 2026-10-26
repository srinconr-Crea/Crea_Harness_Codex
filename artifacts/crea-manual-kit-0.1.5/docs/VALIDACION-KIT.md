# Validación local del candidato manual Crea 0.1.5

Fecha: 2026-10-26. Fuente: árbol 0.1.4 preservado; nuevo staging versionado 0.1.5.
Este documento pertenece al kit manual. El motor Python histórico no se instala con el ZIP.

## Evidencia ejecutada

- Línea base copiada: 58 pruebas passed con el entorno de integración existente.
- Bloque de evidencia antes de integrar roles: 9 regresiones nuevas y 24 de adaptadores passed.
- Suite final del kit: 97 pruebas passed (unittest discover -s tests/crea -q desde la raíz del kit).
- Empaquetador del repositorio de desarrollo: 3 pruebas passed; guardas de destino 0.1.5,
  preservación de manifests/upstream y detección del ZIP anterior alterado.
- Plan/run/gate con procesos pytest/JUnit y Git reales en fixtures locales. Gate y transiciones
  no ejecutan suites. Referencia corregida a recibo real conserva plan y gate sin reejecutar.
- Equivalencia stage/commit, rechazo de staging parcial/ajeno y commits fuera del alcance,
  bytes de metadatos publicados, historia/predecesores, referencias tras Archive y períodos
  de escritura por rol; cambios de HEAD/rama/índice contrastados con acciones.
- Código 4/informe ilegible informativo no añade veto ni certifica; códigos y decisiones
  se consumen por transición, preservando gates y permisos previos. Reanudación focalizada.
- Selección Silver/Spark y documental sin capas; templates no activadas de fábrica.
- Draft2020-12 offline, config anterior compatible y rechazo de condiciones desconocidas.
- Objetos con estados independientes, transporte Unicode/Markdown del título/cuerpo de PR
  mediante pruebas locales y comparación del recibo normalizado, sin crear PR real.
- Revisión independiente de código: 6 hallazgos Important, 0 Critical, 0 Minor; corregidos
  en una pasada con regresiones. No se simuló la ejecución de los cuatro roles nativos.

## Integridad del candidato

El empaquetador 0.1.5 verifica ambos manifests anteriores y conserva skills upstream/licencias;
regenera inventario, manifest, ZIP, SHA-256 e informe de validación local. Los resultados exactos
están en kit-manifest.json, docs/NEUTRALIDAD.json y el archivo ZIP.validation.json externo.
La auditoría textual usa lista de identificadores externa; las revisiones de ejemplos/fuentes
públicas se vinculan a categoría/ruta/línea/hash completo. No se distribuyen esos inputs sensibles.

## Límites

Estas pruebas usan Git y procesos locales reales con datos sintéticos. No acreditan piloto
operativo de cuatro roles, descubrimiento nativo, autenticación/proveedor real, Spark/Databricks,
permisos del cliente, despliegue o publicación remota. Todo ello permanece not_run o no aplica
según la HU y los adaptadores configurados. El modo informativo no rebaja gates existentes.
Un JSON y referencias locales no autentican criptográficamente una aprobación humana.

El estado o las pruebas del motor histórico se documentan en el repositorio de desarrollo;
no se infieren como capacidades ni certificados de este kit. La migración es un diff revisado,
con herramientas/schema juntos y sin convertir recibos anteriores. No hay merge ni deploy.
