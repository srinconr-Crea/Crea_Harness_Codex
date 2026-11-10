# Distribución, proyecto y estado local

`kit-composition.json` describe superficies; `composicion.py --root <kit>` devuelve
la selección sin copiar, instalar o modificar cliente. A revisa esa selección y combina
solo recursos necesarios con los existentes. B usa diff y conserva personalizaciones.

| Superficie | Decisión inicial |
| --- | --- |
| Cliente compartido | AGENTS, skills, perfiles, schemas, reglas, guías, scripts, recursos, catálogo y tests/crea |
| Procedencia | Manifest original, composición, locks, licencias y NOTICE; no reescribir hashes con el cliente personalizado |
| Solo distribución | Prompt_configurar-kit-proyecto.txt y LEEME-CREA.md |
| Solo mantenedor | Empaquetadores, ZIP/hash e informes de empaquetado/historia |
| Local | Binding, diagnósticos, temporales, entornos, cachés y credenciales |

El clon conserva [la entrada C](preparar-desarrollador.md) aunque no tenga el prompt.
Tests/crea siguen disponibles para regresiones de herramientas y no son pruebas de
negocio por defecto. VALIDACION conserva alcance y límites útiles. No reducir archivos
eliminando licencias, recursos referenciados o schemas para ocultar problemas.

`.gitignore` omite untracked locales, no retira lo versionado. Las exclusiones de
contexto limitan lectura, no visibilidad de cambios Git. Composición define copia, no
autorización de publicación. Stage/publicación usan rutas aprobadas explícitas.
Los recibos y logs requeridos de docs/hu se conservan según sus contratos, sanitizados;
no hay exclusión global de docs, openspec, .codex, .agents o *.log.

A incorpora/combina exclusiones de `.crea/local.json`, `.crea/diagnosticos/` y
`.crea/tmp/` desde el primer setup. Si un cliente anterior rastrea esos archivos u otros
ahora solo de distribución, proponer migración por archivo y sus consumidores. No git rm,
limpieza o borrado automático. La configuración compartida y la evidencia se preservan.

`validar-kit.py --original` comprueba la distribución íntegra. Después de personalizar
o instalar solo el perfil cliente, validar sin original. Un manifest copiado acredita
procedencia, no igualdad de todos los bytes del proyecto respecto al ZIP.
