# Contrato Silver personalizable

Estado: template
Revisión: 1

Completar con el responsable antes de activar. No se supone una PK, deduplicación universal,
normalización o retención real del cliente.

| Decisión necesaria | Qué precisar y qué evidencia conservar |
| --- | --- |
| Propósito | Datos depurados/intercambiados y consumidores; criterios funcionales explícitos. |
| Granularidad | Unidad resultante y cardinalidad; casos sintéticos de unicidad. |
| Transformaciones permitidas | Normalización, tipado y enriquecimientos autorizados, sin inventar negocio. |
| Identidad | Claves y reglas reales para duplicados/nulos; pruebas de preservación de identidad. |
| Errores | Tipos inválidos, referencias faltantes y tratamiento aprobado; resultados observables. |
| Conservación | Historización, reejecución, borrados y conservación conforme a política real. |

Convertir decisiones en reglas `PROY-SILVER-...` con condición, obligación, fundamento,
evidencia, modo de comprobación y excepciones. En una HU Silver/Spark solo se seleccionan
Silver, Spark y comunes pertinentes. Gold y otras capacidades no se cargan automáticamente.
