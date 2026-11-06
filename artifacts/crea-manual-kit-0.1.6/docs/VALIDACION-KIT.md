# Validación local del kit portable 0.1.6

## Procedencia y alcance
La fuente es el árbol real personalizado 0.1.5, incluido su prompt. La baseline externa por bytes registra 0.1.3/0.1.4/0.1.5 y sus ZIP/hashes. No confundir esta entrada con certificación de identidad del árbol personalizado respecto al ZIP histórico.

El empaquetador scripts/package_manual_016.py solo admite 0.1.6. Verifica fuentes preservadas, manifiesto completo y equivalencia árbol/ZIP. Las comprobaciones estructurales usan scripts/crea/validar-kit.py, con --original para bytes de distribución y sin ese parámetro después de personalizar.

## Evidencia de esta entrega
Los resultados exactos están en el informe externo crea-manual-kit-0.1.6.zip.validation.json y en docs/evidence/portable-aitools-devops del repositorio fuente. Incluyen distribución, selección AITools, hooks con fixtures y contexto Azure con dobles. La evidencia previa de 0.1.5 no se reutiliza como resultado de archivos nuevos.

## Límites
No se ejecutó lectura Azure remota ni login, pipelines, escritura de work items, publicación Git, Spark, deploy o piloto de cuatro roles. Los hooks permanecen incluidos/inactivos: un fixture no prueba confianza ni observación real del host Desktop. La auditoría de neutralidad histórica no certifica los recursos upstream actualizados; se informa por separado. Los helpers y las reglas no impiden que herramientas externas eludan el procedimiento.

## Resultado local de 6 de noviembre de 2026
Suite conjunta: 66 pruebas aprobadas, 1 omitida por privilegio de symlink físico y 9 subtests aprobados. El rechazo de enlaces también está cubierto con doble independiente. Validación adicional: 14 schemas y 5 TOML. Revisión independiente completada; fallo de relations:null corregido con pruebas de lectura inicial y recheck. Los resultados detallados y comandos están en la evidencia externa referenciada.
