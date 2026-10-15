<!-- harness-desktop-v1 -->
## Desarrollo supervisado con Harness

Usar la Skill de proyecto harness-hu para iniciar una HU. Mantener las reglas
cliente precedentes. El principal puede resolver una HU pequeña sin lanzar
todos los roles. Delegar según impacto; validar assignments y un escritor por
ruta con harness_core.desktop.check_assignments. Máximo cuatro assignments
concurrentes y un nivel de delegación. Revisores no editan el candidato.

Codex es el coordinador nativo: resolver runtime/binding de setup, conducir
work preview/start/status/resume y generar contratos sin JSON manual obligatorio.
Presentar SHA y alcance positivo antes de registrar aprobación. Comprobar perfiles,
delegación y aislamiento efectivos; usar supervised_single_agent solo explícitamente
y conservar bloqueada toda revisión que exija independencia no observada. Registrar
referencias reales de tareas, nunca inferir agentes ejecutados desde configuración.
Reanudar desde hu.sqlite3/journals; respetar escritor único y dos correcciones.
Consultar activity report sin escrituras. Duraciones no son tokens; consumo ausente
queda null con motivo. Hooks confiados son opcionales y de cobertura parcial.

Las prácticas se resuelven del paquete harness_local.quality_kit/practices.json
con load_quality(); instrucciones y herramientas recomendadas no conceden
permisos ni autorizan efectos remotos. Comprobar modelo/esfuerzo, sandbox y
herramientas en Desktop antes de declarar certificado.
<!-- /harness-desktop-v1 -->
