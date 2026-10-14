# Tasks

## 1. Contratos y alcance positivo

- [x] 1.1 Añadir contratos/esquemas versionados InstallationRecord, SetupInput, AccessScope, SetupPlan y SetupReport sin modificar v1; verificar round-trip, campos desconocidos rechazados, identidad/URL y snapshots de los contratos publicados.
- [x] 1.2 Implementar canonicalización y evaluación de read_allow/write_allow/deny intersectadas con política v1 y plan; probar lectura permitida, escritura denegada, deny prevalente, ADS, traversal, nombres reservados, alias Windows y reparse points sin efectos.
- [x] 1.3 Conectar el alcance a los adaptadores propios de lectura/escritura y gates de HU, declarando accesos técnicos y de integración exactos; verificar rechazo antes del efecto y que cambios externos fuera de alcance bloqueen el gate.
- [x] 1.4 Documentar formato adicional, procedencia y regeneración de binding al mover máquina; comprobar ejemplos genéricos completos y parciales con validadores, sin permisos abiertos por defecto ni secretos.

## 2. Entrada de instalación y dependencias

- [x] 2.1 Añadir manifiesto/lock de artefactos oficiales fijados, plataforma y efectos de instalación por usuario; verificar hashes/licencias, dependencia transitiva ausente y rechazo de versión/plataforma inesperada con fixtures offline.
- [x] 2.2 Implementar install-harness.ps1 con runtime aislado, reutilización de Python compatible y preparación per-user oficial cuando falte; probar un entorno sin Python del producto, ruta con espacios y que PATH/configuración global no cambien.
- [x] 2.3 Añadir preparación opcional de Git portátil, Node/OpenSpec y CLI Databricks dentro del alcance del plan; probar detección de versiones, checksum erróneo, red ausente y ejecución del binario absoluto esperado con dobles y kit fijado.
- [x] 2.4 Registrar ownership/journal/lock y recuperación por fase del instalador, reutilizando protección Windows; verificar instalación repetida, interrupción, recurso ajeno, personalización local y conservación de estado/evidencias de clientes.
- [x] 2.5 Documentar el comando único de kit local/online, preview, efectos per-user, prerrequisitos Codex y ruta offline; ejecutar el comando documentado contra un kit candidato aislado y comparar snapshots del preview sin descargas/escrituras.

## 3. Skill inicial e importación guiada

- [x] 3.1 Empaquetar y registrar harness-setup en ámbito de usuario soportado con resolución validada del runtime; verificar invocación sin cliente/cwd específico, colisiones, update/recover y skill_discovery_pending cuando solo existe el archivo.
- [x] 3.2 Implementar entrevista/importación con procedencia para descriptor/política/binding/URL/alcance/capacidades; probar insumos completos sin preguntas repetidas, contradicción owner/repo, binding de otra máquina y redacción/rechazo de secretos.
- [x] 3.3 Actualizar renderer/integración de Skills, ocho roles y AGENTS con detección de formato soportado; probar TOML válido, preservación de instrucciones personalizadas y rechazo/adaptación explícita de formatos incompatibles.
- [x] 3.4 Documentar la conversación inicial y diagnóstico de descubrimiento/modelos/permisos; validar ejemplos con CLI y protocolo Desktop que distingue preparado de observado sin afirmar aislamiento.

## 4. Plan compuesto y preparación

- [x] 4.1 Implementar setup interview/preview y exportación exclusiva del plan padre que referencia planes hijos y todos los efectos; probar snapshots sin clonar, instalar, autenticar, crear SQLite ni modificar target/estado/configuración de usuario.
- [x] 4.2 Implementar setup apply/status con autorización ligada a revisión, revalidación por etapa y preparación/clonación seleccionada; probar un único alcance autorizado, drift, checkout ambiguo/sucio y recursos existentes sin sobrescritura.
- [x] 4.3 Implementar setup recover/reanudación mediante journals propios y tratamiento del commit local revisado para baseline limpia; probar fallos antes/después de etapa, conservación de personalizaciones y ausencia de push implícito.
- [x] 4.4 Integrar guía OAuth/perfil nativos y comprobaciones remotas de lectura explícita; probar login cancelado, credenciales redactadas, permiso denegado y prepared local conservado sin ejecutar jobs/deploy ni mutar datos.
- [x] 4.5 Producir el informe por capacidad con evidencia/versiones/vigencia y códigos estructurados; probar recurso presente no observado, aislamiento fallido, remote_not_checked y gates certified/release/publicación conservados.
- [x] 4.6 Documentar setup, errores, recuperación y entrega de interfaces a 10; ejecutar ejemplos completos con insumos sintéticos y revisar que no incorporen configuración ni reglas reales de clientes al producto.

## 5. Verificación integral del incremento

- [x] 5.1 Ejecutar pruebas relevantes de distribución, onboarding, contratos, HU y Desktop tras las pruebas nuevas; entregar evidencia con comandos/resultados y compatibilidad v1 sin convertir dobles en aceptación real.
- [x] 5.2 Construir un kit candidato reproducible y verificar instalación/setup desde el wheel instalado en entorno aislado; comprobar hashes, recursos empaquetados y que se conserva el aviso de release no certificado.
- [ ] 5.3 Ejecutar protocolo real en otra máquina Windows: comando de instalación sin runtime previo, Skill descubierta antes de cliente, setup con insumos completos/parciales, OAuth guiado o bloqueo explícito y reporte de HU admisible; adjuntar evidencia por paso y dejar not_run/blocked aquello que no se observe.
- [x] 5.4 Verificar dos clientes y un cliente con AGENTS/TOML personalizados, actualización y recuperación; comprobar aislamiento de binding/estado, instrucciones preservadas y conservación de los pendientes históricos de 06–08 antes de declarar aceptación del nuevo flujo.
