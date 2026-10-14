# Verificación de instalación y setup — cambio 09

La evidencia local usa clientes sintéticos y carpetas aisladas bajo `.test-data`.
No acredita descubrimiento en Codex, disponibilidad real de modelos, aislamiento
de agentes ni acceso Databricks. `certified=false`, `release_allowed=false` y
`publication_allowed=false` se conservan, junto con los pendientes de 06–08.

## Implementación y revisión

Cinco contratos adicionales y sus schemas publicados conservan v1. El alcance
positivo limita adaptadores propios y gates de HU. El plan padre contiene hijos
o recetas congeladas, hashes, accesos técnicos y efectos externos. Apply/status/
recover reutilizan journals y autorización ligada a la revisión.

La revisión identificó herramientas privadas sin conectar, índice ajeno en el
commit local, expansión del hijo tras clone, verificación tardía de artefactos y
ejecución de código instalado modificado. Las correcciones incluyen selección
absoluta, rechazo de staging ajeno, recetas verificadas y ownership previo a
Python. Una segunda revisión encontró CLI registrada incompatible y artefactos
sin lease en instalación diferida; ambas correcciones quedaron cerradas por
inspección y cuatro regresiones reales pasaron. La revisión final acotada no
encontró defectos residuales; no sustituyó ejecución de pruebas.

## Protocolos locales observados

- Instalación offline desde el comando documentado, sin runtime del producto
  previo, con rutas con espacios y Python compatible reutilizado.
- Git 2.51.0, Node 22.20.0, OpenSpec 1.13.2 y Databricks 0.292.0 preparados desde
  artefactos fijados. Sondas absolutas, timeout y telemetría desactivada.
- Interrupción de instalación seguida de recuperación en runtime nuevo; restos
  parciales conservados. Repetición intacta y actualización en otra raíz pasaron.
- Invocador sin cwd cliente: verifica hashes y bloquea código del wheel modificado
  antes de iniciar Python; su control positivo y la prueba de rechazo pasaron.
- Smoke del wheel instalado: ocho roles, setup local, commit revisado, baseline
  limpia, status e idempotencia. Reportó `local_prepared` y `local_clean`, con
  `skill_discovery_pending` y `remote_not_checked`.
- Dos clientes, AGENTS y TOML personalizados, aislamiento de bindings/estado y
  recuperación antes/después de efectos se comprobaron con fixtures locales.
- Cancelación OAuth y permiso denegado se comprobaron con dobles; salida sensible
  descartada y preparación local conservada. No hubo OAuth real ni jobs/deploy.

El protocolo repetible está en `scripts/verify_installed_setup.py`. La guía y
los cuatro ejemplos sintéticos están en `docs/one-command-setup.md` y
`docs/examples/setup`. El ejemplo completo no repite preguntas; el parcial queda
bloqueado por decisiones faltantes. Sus contratos se validaron.

## Pruebas y empaquetado

Comandos de construcción:

```powershell
.venv/Scripts/python.exe scripts/generate_schemas.py
.venv/Scripts/python.exe scripts/generate_setup_examples.py
.venv/Scripts/python.exe scripts/prepare_distribution.py
.venv/Scripts/python.exe scripts/prepare_installation.py
.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider
openspec validate --specs --strict
openspec validate 09-one-command-install-and-guided-setup --strict
```

El kit incluye seis wheels de dependencias, cinco artefactos de herramientas,
lock npm de 70 paquetes, licencias y el guard Windows. El wheel y ZIP usan fechas
fijas. Dos construcciones consecutivas de un candidato intermedio produjeron
hashes idénticos del manifiesto y ZIP. La construcción definitiva y su repetición
también fueron idénticas:

- Manifiesto SHA256: `791fe2ec116f4b442205790a1ce3ff6ab48cdde1505e665f4530cc16f1ebe47a`.
- ZIP SHA256: `fc2199b8b5c9c8ac36b8134dd1c5089178581bf704c840f32f1925177e4b1719`.
- Candidato incluido en el wheel: `f4b663c22b615fe38a314829a122133f7414402dd135a77b3e5e068fbccab3aa`.

La regresión definitiva, sin construcción ni instalación concurrente, terminó con
**623 passed in 1295.27s**, código 0. Incluye distribución, onboarding, contratos,
HU, Desktop, dos clientes y personalizaciones. Se ejecutó con permisos necesarios
para procesos Git en Windows; las pruebas no acreditan observaciones Desktop.

El kit definitivo se instaló en `.test-data/v 9`, con Skill en `.test-data/vs9`,
desde Python compatible y sin runtime previo del producto en esa raíz. Registró
Git 2.51.0, Node 22.20.0, OpenSpec 1.13.2 y Databricks 0.292.0. Desde el wheel
instalado, este comando terminó con `status=passed`, código 0:

```powershell
& '.test-data/v 9/runtime/Scripts/python.exe' -I -B scripts/verify_installed_setup.py --installation-record "$PWD/.test-data/v 9/installation.json" --scratch "$PWD/.test-data/definitive-customer09"
```

Confirmó ocho roles, commit local revisado, `local_prepared`, `local_clean`,
status e idempotencia. Conservó `skill_discovery_pending`, `remote_not_checked`
y los tres gates en falso. Los logs locales son `09-regression-definitive.log`,
`09-build-definitive.log`, `09-build-repeat.log`, `09-installed-definitive.json`
y `09-wheel-protocol-definitive.json`, bajo `.test-data` (no se versionan).
La recuperación, repetición y actualización aisladas constan respectivamente en
`09-recovered-short.json`, `09-repeat-short.json` y `09-updated-short.json`;
las tres reportaron `prepared`.

Pruebas focalizadas observadas: 31 de contratos/alcance/HU/CLI, 18 de setup,
13 de instalación/compatibilidad y cuatro de integración/recuperación aisladas.
Las regresiones de revisión incluyen rechazo de Databricks 0.277.0 y comprobación
Windows de que el ZIP aprobado no admite escritura durante extracción.

Una corrida concurrente tuvo 614 correctas, dos fallos y tres errores de
preparación/integración. No se contabiliza como aceptación. Los casos aislados
pasaron; se añadieron diagnósticos NTSTATUS y se redujeron las reservas de memoria
en lecturas de herramientas. La corrida definitiva posterior pasó las 623 pruebas.

Las dos specs nuevas están sincronizadas; la validación estricta de las 19 specs
principales pasó.

## Pendiente autorizado

5.3 permanece `not_run`: no existe otro equipo Windows disponible. El usuario
autorizó expresamente archivar con ese pendiente el 14 de octubre de 2026.
El archivo administrativo y push de código no satisfacen ese protocolo ni
desbloquean certificación, promoción o publicación histórica.
