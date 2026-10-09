# Procedencia del kit OpenSpec

Los recursos proceden del paquete instalado `@fission-ai/openspec` 1.13.2,
distribuido bajo MIT; se conserva su LICENSE. Se generaron dos fixtures Windows
con `node <package>/bin/openspec.js init TARGET --tools codex --profile custom
--no-animation`. La configuración aislada establece `delivery: skills` y los
workflows explore, propose, update, apply, verify, sync y archive.

Reproducción: `.venv/Scripts/python.exe scripts/verify_openspec_generation.py`.
El script aísla HOME, USERPROFILE, CODEX_HOME, APPDATA, LOCALAPPDATA y XDG en
fixtures descartables bajo `.test-data`. Desactiva telemetría y comprobación de
actualizaciones. Compara las salidas de ambas ejecuciones y hashes antes/después
de las ubicaciones originales de Skills/prompts y configuración/datos OpenSpec.
No toma una copia del HOME completo ni de las bases de datos activas de Codex.

La evidencia real está en `docs/evidence/openspec-generation.json`. Se excluyen
los dos `.gitkeep` y `.openspec-target` generados por upstream: no están en la
allowlist de preparación de este incremento. El manifiesto incluye exactamente
la configuración, las siete Skills y la licencia. Runtime verifica los hashes
sin invocar OpenSpec ni instalar dependencias. La prueba de recursos altera y
elimina una Skill, y comprueba el rechazo previo a la planificación.
