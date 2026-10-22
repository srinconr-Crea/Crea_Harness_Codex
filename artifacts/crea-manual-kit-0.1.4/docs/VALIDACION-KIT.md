# Validacion local del kit manual Crea 0.1.4

Fecha de autoría: 2026-10-21. Alcance: nueva distribución local; fuente 0.1.3
conservada. No se modificaron clientes ni se publicaron commits/PR/despliegues.
El motor Python histórico del repositorio no forma parte de este ZIP; sus pruebas
se informan por separado. Esta evidencia no es una HU de un producto cliente.

## Comprobaciones ejecutadas

- 58 tests del helper/adaptadores/neutralidad/configuración: passed.
- Recorrido sintético con Git real → plan → proceso pytest/JUnit → resultados →
  gate, comprobando que planificar/revisar no ejecuta la batería.
- Git por capas, índice distinto con worktree idéntico, untracked Unicode/espacios,
  rename/delete/conflictos, base inexistente/no ancestro y exclusiones declaradas.
- Desconocidos/fixtures/código/política/config invalidan; cero tests, skips,
  assertions faltantes, recibos ajenos/alterados y TTL vencido bloquean.
- argv revisado, entorno mínimo, logs acotados/redacción y timeout real.
- Cobertura por archivo/umbral, tipos de línea inválidos/JSON malformado; XML con
  entidades, contadores inconsistentes e IDs duplicados rechazados.
- JSON con claves duplicadas/NaN rechazado y date-time validado con dependencia
  explícita. Ejecución de CLI bloquea colisiones, incluso hardlinks, sin destruir
  resultados; configuración incorrecta devuelve bloqueo estructurado.
- Draft2020-12: 10 schemas y 6 instancias configuradas; plantillas adicionales
  también validadas. Cinco TOML y 25 skills con nombres/rutas comprobados.
- AST de 27 archivos Python y parseo de 18 YAML, sin ejecución remota.
- Paquete fuente: 8 schemas, 8 instancias, 4 enlaces, TOML/UI y AST válidos.
- Distribución fuente 0.1.3: verificador original pasó 254 comprobaciones.

Versiones de autoría: Python 3.13.14; jsonschema 4.26.0;
rfc3339-validator 0.1.4; PyYAML 6.0.3; pytest 9.1.1; coverage 7.16.2.
Dependencias preparadas solo en entorno virtual local.

## Revisión y escenarios de instrucciones

Evaluación independiente de las instrucciones originales encontró ambigüedad en
repetición de checks, vigencia y catálogo. La evaluación de las nuevas instrucciones
respondió conforme al contrato ante deadline/repetición rutinaria, fixture untracked,
runtime inactivo, inyección en diff con control legítimo, rondas globales y tareas
mixtas sin recibo. Se precisó qué evento cuenta como ronda. Es evaluación de
instrucciones; no demuestra cuatro perfiles nativos despachados.

Revisión de código independiente detectó defectos de coverage y colisión de salida.
Se reprodujeron mediante tests reales antes de corregir; sus regresiones pasan.
También se corrigió el preflight de configuración antes de inspeccionar sus campos.

## Integridad, personalización y empaquetado

scripts/crea/verificar-kit.ps1 delega validación estricta offline sin ejecutar
comandos de negocio. -OriginalDistribution comprueba tamaños/hashes/inventario;
sin esa opción valida estructura personalizada. El proceso de entrega comprueba
ambos modos, incluyendo una copia personalizada sintética sin llamadas remotas.

El manifest registra bytes reales de todos los archivos entregados, excluyendo su
propia entrada para evitar circularidad. El ZIP se compara entrada por entrada y
se acompaña de SHA256 y .zip.validation.json. Ese recibo contiene el resultado final
de integridad/auditoría; este documento no sustituye su ejecución.

Auditoría: herramienta original del paquete sobre árbol completo y ZIP, con lista
externa de identificadores. Coincidencias genéricas upstream se revisan por contexto
y se vinculan externamente a archivo/fecha/línea/hash; nunca se aceptan identificadores
externos. No se incluyen listas sensibles ni valores encontrados en la distribución.
Resumen: docs/NEUTRALIDAD.json; auditoría final ZIP acompaña al recibo de empaquetado.
Se conservan bytes de skills upstream y licencias; no se borran avisos obligatorios.

## Límites y siguientes pilotos

- Setup genérico pendiente: no hay política/criterios/comandos de un cliente listos.
- Helper puro no ejecuta Git, comandos o APIs; usar CLI integrada para la cadena
  estricta. Hashes/JSON no son firmas ni autentican por sí solos una ejecución.
- Entorno local vincula intérprete/plataforma/metadata, no todos los bytes de
  dependencias ni estado/permisos remotos. Revisar inputs, oráculos y cobertura.
- Runtime/Spark, SAST/Semgrep, mutation, evals de modelos, CI y adopción entre
  planes están inactivos y bloquean si se requieren. Hay contratos/procedimientos,
  sin presentarlos como adaptadores ejecutados. Herramientas por aplicabilidad.
- No se ejecutó Databricks/UC/ADLS/DBR, deploy, jobs/tablas, credenciales/permisos,
  merge o publicación. Bundle validate/Spark local no acreditan esas operaciones.
- El límite nativo de threads excluye principal; secuencialidad, no subdelegación
  y contador de correcciones son procedimientos, no aislamiento técnico por TOML.
- Pendiente piloto real en Codex con Planner → Developer → Tester → Reviewer,
  nueva solicitud humana de apply y cierre/publicación expresamente aprobados.
  Modelos, descubrimiento y permisos efectivos se comprueban en la cuenta destino.
- CI es opt-in: PR/checks sin deploy → merge humano → deploy autorizado del SHA
  → smoke → promoción; sin instalar workflows ni asumir ramas/triggers del cliente.

Cambios: docs/pruebas/CAMBIOS.md. Setup: docs/configuracion-manual.md.
