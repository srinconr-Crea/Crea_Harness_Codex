# Matriz operativa 0.1.6

| Familia | Actor y alcance |
| --- | --- |
| boards work-item show | Planner/Reviewer, un ID de HU, organización fija; validar ID, URL y System.TeamProject canónico. Sin --project. |
| devops invoke | Solo GET wit/comments, mismo ID validado y project_id fijo; API preview explícita y paginación. No invoke genérico. |
| repos show; repos pr list/show/create | Principal, exclusivamente entrega previa y sus aprobaciones. pr show no admite --project ni --repository; validar respuesta. |
| boards query, area, iteration, relations | Fuera del incremento; enlaces se registran sin seguirlos. |
| work-item create/update/delete; --discussion | Deshabilitado, referencia futura. |
| pipelines y subgrupos | Solo catálogo documental; ninguna consulta, ejecución ni instalación habilitada. |
| merge, votos, vínculos nuevos, cambios de estado | Deshabilitado. |

Crear PR conserva `docs/entrega-git.md`, aprobación concreta y verificación. No usar
`--work-items`, `--transition-work-items`, auto-complete ni bypass-policy.
Una petición de escritura puede producir un borrador local; esta versión no la ejecuta.
