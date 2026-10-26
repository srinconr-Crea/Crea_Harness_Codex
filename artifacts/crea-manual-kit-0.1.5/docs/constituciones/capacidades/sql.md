# Reglas SQL iniciales

Estado: active
Revisión: 1

### CREA-SQL-001
Aplicación: cambios de joins o agregaciones SQL.
Obligación: explicitar grano, claves y semántica antes de optimizar; conservar criterios aprobados.
Fundamento: una optimización no debe cambiar el indicador o multiplicar filas inadvertidamente.
Evidencia: criterios del cambio y casos pertinentes de unicidad, nulos y reconciliación.
Comprobación: review
Excepciones: cambiar semántica requiere aprobación del alcance, no excepción implícita.

Fundamento local y ejemplos técnicos: docs/buenas-practicas/sql.md. Los parámetros de funciones,
planes de consultas, perfiles y valores de ambiente permanecen en las referencias del proyecto.
