# Preparación C — proyecto ya configurado

Después de clonar y abrir el checkout en Codex, pedir `$crea-preparar-desarrollador`.
La skill está en `.agents/skills/Crea/preparar-desarrollador/SKILL.md` y no necesita
el prompt extenso del paquete. A configura un proyecto; B actualiza el kit; C prepara
tu máquina y tu identidad. Elegir una entrada, sin ejecutar A/B por seguir C.

## Inspección inicial

Desde la raíz, usar un Python existente y preparado:

```powershell
python -B scripts/crea/preparar-desarrollador.py inspect --repo .
```

El modo inicial es offline y no escribe. Contrasta checkout/revisión, configuración,
OpenSpec, consumidores, herramientas y dependencias. Un setup compartido incompleto
queda blocked; C no lo arregla ni marca setup_complete. Dependencias ausentes dejan
diagnóstico útil sin instalarlas; ejecuta de nuevo con un intérprete preparado cuando exista.
Las dependencias de validación están en [requirements-validation.txt](../requirements-validation.txt).
Se comprueban el Python elegido y el que ejecuta el diagnóstico; una instalación requiere
alcance autorizado. Se puede indicar directamente otro intérprete existente, sin instalarlo.
ready solo cubre prerrequisitos aplicables observados. partial enumera pendientes;
blocked impide la continuación dependiente. Códigos: 0 completado, 3 intervención
humana pendiente, 4 error de inspección. No son una autorización para publicar.

## Entorno propio

Si el proyecto adopta `execution.local_environment_path=".crea/local.json"`,
`python_executable` compartido es null. Elige tu intérprete absoluto existente,
por ejemplo `.venv/Scripts/python.exe`, sin activar el entorno. Sustituye la ruta
del ejemplo por la real antes de ejecutar:

```powershell
python -B scripts/crea/preparar-desarrollador.py bind --repo . --python "C:/ruta real/.venv/Scripts/python.exe"
```

Eso presenta before/after. Añade `--apply-local` solo para aplicar ese cambio local
autorizado. `--databricks-profile` permite un alias personal si Databricks aplica;
no modifica host/target compartidos. El binding no admite credenciales, comandos,
catálogo, ramas, modelos o permisos. Si ya es equivalente no cambia bytes ni fecha.
Un proyecto legacy sin esta opción conserva su Python absoluto anterior.

Plan, run, attempts y gate resuelven el mismo binding; intérprete, ubicación y
paquetes efectivos forman la identidad del entorno. Cambiarlo durante una HU puede
invalidar evidencia: conservar intentos y reconciliar la ejecución, sin migrarlos.
Registrar esa decisión y su efecto en `docs/hu/<change>/evidencia.md` y un handoff nuevo,
sin sobrescribir el intento anterior o afirmar que el nuevo entorno ya pasó las pruebas.
Evidencia de otra máquina puede leerse como historia, no trasplantarse como ejecución actual.

## Autenticación y conexión

La persona realiza Git/GCM, MFA, Azure y Databricks aplicables. No guardar tokens en
el binding, el diagnóstico o Git. No usar el login de otra persona ni cambiar defaults
globales. Las conexiones usan lecturas explícitas con credenciales disponibles:

```powershell
python -B scripts/crea/preparar-desarrollador.py inspect --repo . --online
```

El diagnóstico diferencia verified de unverified/not_run y no infiere permisos de
escritura desde una lectura. No Boards sin HU/fase, pipelines, PR, jobs o datos de prueba
remotos. No actualizar skills, inicializar OpenSpec, activar hooks o instalar servicios.

Con `--out .crea/diagnosticos/<id>.json` exporta a una ruta nueva después de reemplazar
el ID. Si falta una herramienta, acordar la instalación concreta o dejarla pendiente.
En Windows se pueden usar `openspec.cmd` y `npm.cmd`; no hay que cambiar ExecutionPolicy.

Las exclusiones de binding, diagnóstico y temporales vienen desde A. Un archivo que
ya esté versionado seguirá rastreado: informar y proponer corrección al responsable,
sin `git rm` automático. Modelos/perfiles y reglas compartidos se conservan.
