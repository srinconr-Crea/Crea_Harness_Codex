"""Prepare explicit not_run acceptance protocols; execute no clients/providers."""
import json
from pathlib import Path

from harness_core.distribution import PilotReport, PROTOCOLS
from harness_local.distribution import candidate_manifest, release_gate

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/evidence/distribution'


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    manifest=candidate_manifest()
    constraints=['synthetic_data_only','selected_isolated_resources','explicit_policy_binding',
        'no_production_access','no_cross_client_state','no_remote_write_without_current_gates']
    clients=[dict(client_id=c,repository='demo/'+c,branch_prefix='feature/'+c+'/',
        external_state='operator_selects_distinct_state_'+c,policy='operator_selects_policy_'+c,
        story_id='HU-SYNTHETIC-001',status='not_run',constraints=constraints) for c in ('alpha','beta')]
    protocols=[]
    steps={
        'predecessor_evals':['Importar 144 capturas reales y anotaciones humanas de 06/07 (dos perfiles Luna/medium).','Ejecutar eval report milestone=7 promotion con hashes vigentes.'],
        'compatible_sandbox':['Observar sandbox/modelos/herramientas de todos los roles seleccionados en Desktop.','desktop-check conserva conflicto o ausencia como no certificado.'],
        'harness_publication':['Seleccionar autorización/provider GitHub sintético y gates actuales.','pr preview, publish, interrumpir y reconcile; comprobar un único draft PR y misma rama.'],
        'alpha_hu':['Onboarding desde usuario nuevo: preview, revisión y apply.','HU start/plan/approve/candidate/validación/evidencia hasta PR autorizado.'],
        'beta_hu':['Repetir recorrido con política y estado externo propios.','Comprobar que aprobación/candidato alpha no sirven para beta.'],
        'client_isolation':['Comparar bindings, locks, HU/evidencias y aprobaciones alpha/beta.','Intentar usar plan/aprobación de otro checkout; exigir rechazo.'],
        'synthetic_client_pilot':['Seleccionar copia NaturaPet y HU/recursos sintéticos aprobados por el operador.','Recorrer harness con validación por impacto y PR draft autorizado; no usar piloto manual como aceptación.','Caso negativo: catálogo productivo en fixture bloquea sin crear permiso.'],
        'interrupt_resume':['Interrumpir HU, validación y publicación; conservar estado/evidencia.','Inyectar fallo de infraestructura y reconciliar sin duplicados ni falsos passed.'],
        'update_recover':['Editar recurso gestionado; preview debe producir conflict sin escritura.','Revisar nuevo plan con archivo intacto, apply con backups; recover restaura ownership y conserva estado.','Editar después de apply: recover bloquea y conserva contenido.'],
        'second_environment':['Usar otro equipo Windows limpio y usuario nuevo; registrar versiones/hashes.','Revisar launcher y lock, instalar candidato en venv nuevo; comprobar recursos y protocolos reales.'],
        'new_user_desktop':['Observar login y confianza como pasos explícitos.','Usuario nuevo completa onboarding y HU completa con roles/modelos/herramientas reales.']}
    for protocol in PROTOCOLS:
        protocols.append(dict(protocol=protocol,status='not_run',source='desktop_harness',
            required=True,steps=steps[protocol],candidate_sha256=manifest.manifest_sha256,
            evidence_required=['captura_real','anotacion_humana','versions_and_hashes','restricciones_y_limitaciones'],
            observed_result=None))
    value=dict(schema_version=1,candidate_sha256=manifest.manifest_sha256,clients=clients,protocols=protocols,
        constraints=constraints,synthetic_client_pilot=dict(status='not_run',resources=None,authorization=None,
            real_resource_reference_status='blocked',manual_pilot_is_precedent_only=True),
        required_predecessor_runs=144,actual_model_runs=0,certified=False,release_allowed=False)
    (OUT/'protocols.json').write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    pilot=PilotReport(schema_version=1,candidate_sha256=manifest.manifest_sha256,
        implementation_status='complete',receipts=[])
    (OUT/'pending-pilot-report.json').write_text(json.dumps(pilot.model_dump(),indent=2)+'\n',encoding='utf-8')
    result,code=release_gate(pilot)
    (OUT/'release-gate.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    assert code==1 and result['certified'] is False
    print(json.dumps(dict(protocols=len(protocols),actual_model_runs=0,release_gate='blocked')))


if __name__=='__main__': main()
