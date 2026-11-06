# Practicas por herramienta

## 1. Uso
Leer general.md y solo los documentos de las herramientas afectadas. Reglas sintetizadas
tras abrir las fuentes del inventario local; no son una coleccion de enlaces.

## 2. Catalogo
general.md; databricks.md; sql.md; python.md; spark.md; infraestructura.md; agentes.md;
gobierno-datos.md. El ultimo amplia la categoria Databricks con Unity Catalog.

## 3. Procedencia y limites
docs/fuentes.json registra la lista original, ampliaciones, fecha y resultado de acceso.
El indice Databricks es un mapa de temas; no se le atribuyen detalles de sus paginas hijas.
El articulo Medium se leyo y se contrasto, pero las recomendaciones tecnicas se apoyan en
documentacion primaria. La ruta GitHub del snapshot fallo en web; el contenido se inspecciono
en la copia local identificada por commit y LICENSE/NOTICE.
docs/skills-procedencia.json identifica copias de skills; kit-manifest.json registra sus bytes.

## 4. Configuracion y extensiones
Agregar una herramienta como nuevo archivo con las mismas cinco secciones y registrarla
en docs/proyecto.json → practices y en file_types cuando corresponda. Mantener fuente,
fundamento y evidencia esperada por regla. El inventario original de practicas no exigia
esta separacion de documentos; es una adaptacion manual de Crea.
