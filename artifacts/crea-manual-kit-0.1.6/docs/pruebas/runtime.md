# Manifest de entorno y runtime — adaptador inactivo

0.1.4 no ejecuta runtime remoto ni Spark local. Si se requiere: blocked, sin
reemplazar evidencia por bundle validate o mocks.

Futura integración específica: manifest con autorización humana/alcance/efectos,
perfil/host/identidad verificados, target/compute/API/DBR compatibles, catálogo/
namespace/rutas aislados, recursos existentes autorizados, duración máxima y cierre.
Ningún valor se hereda de un ejemplo ni se crea compute/catalog por HU.

Lectura/preflight identidad/red/permisos/recursos → smoke acotado → suite autorizada.
Registrar versiones, IDs run/task reales, parámetros, huella del código cargado y
assertions por criterio. Inventario inicial/creado/modificado/final aun con fallo.
Cierre sobre alcance propio aprobado; nunca detener compute compartido por iniciativa
del Tester. Validar campos localmente no acredita permisos efectivos o ejecución.
