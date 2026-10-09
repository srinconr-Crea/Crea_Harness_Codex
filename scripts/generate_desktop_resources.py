"""Generate project-scoped, passive first-party templates; never install them."""
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1] / 'src/harness_local/desktop_kit'
root.mkdir(exist_ok=True)
(root / 'agents').mkdir(exist_ok=True)
(root / 'harness-hu').mkdir(exist_ok=True)
roles = [
    ('principal', 'Coordina alcance, delegación y presentación a la persona.', 'HU y límites autorizados', 'Decisión de alcance y assignments', 'assigned-only', 'Solo cuando impacto o especialización requieren otro rol.', ['GEN-01', 'GEN-02', 'GEN-04']),
    ('analyst', 'Enriquece HU con criterios observables sin inventar reglas cliente.', 'HU y contexto seleccionado', 'Criterios, preguntas y supuestos explícitos', 'none', 'Devuelve al principal; no subdelega.', ['GEN-01', 'GEN-03']),
    ('impact-analyzer', 'Traza consumidores, grano, null policy y riesgos del cambio.', 'Diff y fixture sintético', 'Rutas afectadas y pruebas necesarias', 'none', 'Devuelve al principal; no subdelega.', ['GEN-01', 'GEN-03', 'SQL-01']),
    ('planner', 'Descompone alcance en tareas y verificaciones revisables.', 'HU enriquecida e impacto', 'Plan con rutas, ownership y pruebas', 'none', 'Devuelve al principal; no subdelega.', ['GEN-01', 'GEN-02']),
    ('developer', 'Implementa tareas en las rutas asignadas como único escritor.', 'Tarea, plan y assignment', 'Candidato y evidencia de pruebas', 'assigned-only', 'Solicita al principal revisión independiente; no subdelega.', ['GEN-02', 'GEN-04']),
    ('tester', 'Ejecuta controles negativos y limpios sobre fixtures autorizados.', 'Candidato y criterios', 'Resultados, defectos y controles limpios', 'assigned-only', 'Solo escribe tests asignados; devuelve al principal.', ['GEN-03', 'GEN-04']),
    ('auditor', 'Revisa candidato sin editarlo y calibra hallazgos verificables.', 'Candidato inmutable y contrato', 'Hallazgos con evidencia y prioridad', 'none', 'Devuelve al principal; no edita ni subdelega.', ['GEN-01', 'GEN-04']),
    ('verifier', 'Contrasta requisitos, escenarios y evidencia sin editar candidato.', 'Specs, candidato y evidencia', 'Completitud, corrección, coherencia y checks pendientes', 'none', 'Devuelve al principal; no edita ni subdelega.', ['GEN-01', 'GEN-04']),
]
entries = []
for id, responsibility, input, output, scope, delegation, practices in roles:
    tools = [dict(schema_version=1, id='local-files', kind='local', purpose='Leer el contexto seleccionado.', required=True),
             dict(schema_version=1, id='git', kind='cli', purpose='Inspeccionar candidato y estado sin efectos remotos.', required=True),
             dict(schema_version=1, id='databricks', kind='mcp', purpose='Fases Databricks explícitamente seleccionadas; ausente no se sustituye.', required=False)]
    entries.append(dict(schema_version=1, id=id, responsibility=responsibility, inputs=[input], outputs=[output],
        write_scope=scope, sandbox='read-only' if scope == 'none' else 'workspace-write', delegate_when=delegation,
        max_delegation_depth=1 if id == 'principal' else 0, tools=tools, practice_ids=practices,
        activated=False, model=None, effort=None))
    instructions = (f'Rol: {id}. {responsibility}\nEntrada acotada: {input}. Salida acotada: {output}.\n'
        f'Delegación: {delegation}\nConsultar practices.json del paquete harness_local.quality_kit con load_quality(); reglas: {", ".join(practices)}.\n'
        'Consultar la Skill de proyecto harness-hu. Mantener cliente y checkout seleccionados. No usar datos productivos.\n'
        'Nunca declarar passed para not_run/blocked ni usar archivos como evidencia Desktop.\n'
        'Asignaciones deben incluir write_paths e isolation; check_assignments rechaza colisiones y profundidad/concurrencia excedidas.\n'
        + ('No editar el candidato. Pedir sandbox read-only y comprobar permisos efectivos; instrucciones no restringen herramientas.\n' if scope == 'none' else
           'Escribir únicamente rutas asignadas; un escritor por ruta. Pedir aislamiento para tareas que se solapan.\n'))
    (root / 'agents' / (id + '.md')).write_text(instructions, encoding='utf-8', newline='\n')
catalog = dict(schema_version=1, catalog_version='1.0.0', practice_pack_version='0.1.0-design', max_concurrent=4, roles=entries)
(root / 'roles.json').write_text(json.dumps(catalog, ensure_ascii=False, indent=2)+'\n', encoding='utf-8', newline='\n')
(root / 'AGENTS.md').write_text('''<!-- harness-desktop-v1 -->
## Desarrollo supervisado con Harness

Usar la Skill de proyecto harness-hu para iniciar una HU. Mantener las reglas
cliente precedentes. El principal puede resolver una HU pequeña sin lanzar
todos los roles. Delegar según impacto; validar assignments y un escritor por
ruta con harness_core.desktop.check_assignments. Máximo cuatro assignments
concurrentes y un nivel de delegación. Revisores no editan el candidato.

Las prácticas se resuelven del paquete harness_local.quality_kit/practices.json
con load_quality(); instrucciones y herramientas recomendadas no conceden
permisos ni autorizan efectos remotos. Comprobar modelo/esfuerzo, sandbox y
herramientas en Desktop antes de declarar certificado.
<!-- /harness-desktop-v1 -->
''', encoding='utf-8', newline='\n')
(root / 'harness-hu/SKILL.md').write_text('''---
name: harness-hu
description: Iniciar una HU supervisada con roles de proyecto y prácticas de Harness, sin activar coordinación completa ni acciones remotas.
---

1. Seleccionar cliente, checkout, HU y límites autorizados; leer AGENTS cliente.
2. Consultar harness_local.quality_resources.load_quality(); practices.json es
   recurso empaquetado pasivo. No ejecutar scripts upstream ni instalar globalmente.
3. Consultar harness_local.desktop_resources.load_desktop(). Perfiles activados
   necesitan selección explícita de modelo/esfuerzo y disponibilidad de cuenta;
   ausencia bloquea, nunca sustituir silenciosamente.
4. Para HU pequeña usar principal. Para mayor impacto asignar analyst,
   impact-analyzer o planner con entradas/salidas acotadas. Registrar role,
   write_paths, isolation y delegation_depth; llamar check_assignments antes
   de delegar. No exceder cuatro assignments ni un nivel de delegación.
5. Developer es único escritor del candidato. Tester escribe solo tests asignados.
   Auditor/verifier reciben candidato inmutable y permisos efectivos read-only.
6. Required ausente => blocked; optional ausente => unavailable/not_checked.
   Configuración TOML no prueba sandbox/MCP/hook efectivo. No habilitar hooks
   sin evento observado; registrar cobertura por evento y versión.
7. Emitir evidencia sintética con versión app/motor, configuración efectiva y
   referencia sanitizada. Files/CLI => not_checked. E03/E04 requieren protocolo
   Desktop manual con anotación humana y tres repeticiones antes de passed.
8. Presentar resultado y pendientes. La coordinación HU/gates completa llega
   en 04; configurar no autoriza publicar, conectar producción ni ejecutar remoto.
''', encoding='utf-8', newline='\n')
manifest = {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob('*')) if p.is_file() and p.name != 'manifest.json'}
(root / 'manifest.json').write_text(json.dumps(dict(schema_version=1, files=manifest), indent=2)+'\n', encoding='utf-8', newline='\n')
