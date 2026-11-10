# Validación del candidato portable 0.1.9

Fuente 0.1.8, sin modificar árboles, ZIP, manifests o hashes históricos. Esta entrega añade
resolución de destino independiente, entorno personal, preparación C y compatibilidad opt-in.
Contexto 0.1.7 y lifecycle 0.1.8 se reutilizan y mantienen sus estados y límites.

La evidencia de autoría/verificación está en el repositorio mantenedor, expediente
`docs/hu/habilitar-trabajo-multidesarrollador-kit/`. El informe externo del ZIP identifica
hash, número de archivos, validación y preservación de baseline. Las cifras históricas no
se presentan como pruebas de código nuevo. Un test local o doble no acredita un piloto real.

`python -B scripts/crea/validar-kit.py --root . --original` verifica distribución completa.
En cliente instalado/personalizado usar el mismo comando sin `--original`; no necesita
prompt ni LEEME. Nunca regenerar manifest para declarar el cliente idéntico al ZIP.
Validación estructural no ejecuta suites de negocio, instala dependencias o autentica.

Pruebas locales cubren rutas, binding, plan/run/gate, casos A-F, simulación aislada,
transiciones y composición/legacy. Sus resultados reales se registran en JUnit y recibos
por ejecución; no se deducen de esta guía. Validación original requiere intérprete preparado.

Remoto Azure, hooks nativos, runtime/Spark/Databricks, piloto de roles y dos desarrolladores
reales conservan estado no acreditado/not_run mientras no exista su evidencia autorizada.
Compatibilidad es una observación puntual; revisión humana/merge a quality y promoción a
 test pertenecen al equipo. No se activan capacidades inactivas para conseguir un pase.
