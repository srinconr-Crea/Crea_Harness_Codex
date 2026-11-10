# Crea — candidato portable 0.1.9

Evolución para sesiones independientes de desarrolladores. Configuración aprobada, reglas,
OpenSpec y catálogo compartidos por Git; preparación personal separada y compatibilidad
informativa con el destino del PR. No coordinador central ni integración automática.

El prompt A/B/C está en esta distribución: A configura una vez, B actualiza mediante diff,
C prepara otra máquina. Elegir una entrada. La composición deja prompt y LEEME fuera del
cliente; cada clon conserva AGENTS, la skill crea-preparar-desarrollador y su guía.

Leer [equipo](docs/equipo.md), [preparación C](docs/preparar-desarrollador.md),
[compatibilidad](docs/compatibilidad.md) y [composición](docs/composicion-kit.md).
Conservar licencias, NOTICE, procedencia, perfiles, scripts, schemas y tests/crea.
Modelos/esfuerzos existentes se preservan; el kit no necesita instalar harness_local.

Feature nace de project.base_branch; PR usa delivery.pr_target_branch o fallback a base.
quality/test quedan para el proceso del equipo. Azure Services conserva CLI con aprobación;
GitHub/Server conservan formulario manual. Archive/push no autorizan por sí solos crear PR.
Sin merge, auto-complete, deploy, promoción, pipelines o escrituras Boards nuevas.

Deriva de 0.1.8 preservada. Contexto opcional se introdujo en 0.1.7 y lifecycle en 0.1.8;
no se activan por esta entrega. Manifest contiene bytes originales, no personalizaciones.
Validar --original solo en el paquete íntegro; cliente instalado/personalizado sin ese flag.
Ver [validación y límites](docs/VALIDACION-KIT.md). Configurar archivos no certifica agentes,
hooks, runtime o permisos de otra máquina.
