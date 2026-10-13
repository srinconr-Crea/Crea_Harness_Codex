# Databricks notebook source
"""Reviewed single-task sandbox protocol; installation is a separate operator action.

Inputs are only the pinned synthetic fixture and validation request. This notebook
never reads a customer table. Delta writes use a unique directory below the selected
managed volume, and cleanup deletes exactly that directory in a finally block.
"""
import hashlib
import json
import uuid
from decimal import Decimal


def canonical(value):
    return json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def run_protocol(spark,dbutils):
    for name in ('harness_request','harness_fixture','harness_mode','harness_volume','harness_synthetic','harness_candidate'):
        dbutils.widgets.text(name,'')
    request=json.loads(dbutils.widgets.get('harness_request'))
    fixture_text=dbutils.widgets.get('harness_fixture')
    fixture=json.loads(fixture_text)
    mode=dbutils.widgets.get('harness_mode')
    source=dbutils.widgets.get('harness_candidate')
    source_hash=sha(source.encode()) if source else None
    if source_hash!=request['source_sha256']: raise ValueError('candidate source hash mismatch')
    volume=dbutils.widgets.get('harness_volume')
    if dbutils.widgets.get('harness_synthetic')!='true' or not volume.startswith('/Volumes/'):
        raise ValueError('synthetic sandbox required')
    if '..' in volume.split('/') or len(volume.rstrip('/').split('/'))!=5:
        raise ValueError('volume rejected')
    if sha(fixture_text.encode())!=request['data_sha256'] or fixture['fixture_id']!='synthetic-sales-v1':
        raise ValueError('fixture hash mismatch')
    runtime=spark.conf.get('spark.databricks.clusterUsageTags.sparkVersion')
    if runtime!=request['runtime']: raise ValueError('runtime mismatch')
    from pyspark.sql.types import StructType,StructField,IntegerType,StringType,DecimalType
    schema=StructType([StructField('order_id',IntegerType(),False),StructField('customer_id',StringType(),False),
        StructField('amount',DecimalType(18,2),True)])
    rows=[(r['order_id'],r['customer_id'],Decimal(r['amount']) if r['amount'] is not None else None) for r in fixture['orders']]
    orders=spark.createDataFrame(rows,schema)
    name='harness_'+uuid.uuid4().hex
    orders.createOrReplaceTempView(name)
    owned_path=volume.rstrip('/')+'/'+name
    delta_path=None
    try:
        # SQL/PySpark behavior, explicit decimal/null/empty contracts and duplicate guard.
        totals=spark.sql(f'SELECT count(*) AS rows, sum(amount) AS total, count(amount) AS non_null FROM {name}').first()
        assert totals.rows==3 and totals.total==Decimal('30.00') and totals.non_null==2
        assert orders.schema==schema
        customers=spark.createDataFrame([(x['customer_id'],x['segment']) for x in fixture['customers_unique']],['customer_id','segment'])
        joined=orders.join(customers,'customer_id')
        assert joined.count()==3 and joined.groupBy().sum('amount').first()[0]==Decimal('30.00')
        duplicate=[x['customer_id'] for x in fixture['customers_duplicate']]
        assert len(duplicate)!=len(set(duplicate)) # negative oracle, never run naive production join
        empty=spark.createDataFrame([],schema)
        assert empty.count()==0 and (empty.groupBy().sum('amount').first()[0] or Decimal('0.00'))==Decimal('0.00')
        # Clean-session notebook negative; a hidden global cannot satisfy this check.
        try: exec('result = clean_df',{})
        except NameError: pass
        else: raise AssertionError('clean session oracle')
        if mode=='delta':
            from delta.tables import DeltaTable
            delta_path=volume.rstrip('/')+'/'+name
            orders.limit(0).write.format('delta').save(delta_path)
            table=DeltaTable.forPath(spark,delta_path)
            for _ in range(2):
                table.alias('target').merge(orders.alias('source'),'target.order_id = source.order_id').whenMatchedUpdateAll().whenNotMatchedInsertAll().execute()
            final=spark.read.format('delta').load(delta_path)
            assert final.count()==3 and final.groupBy().sum('amount').first()[0]==Decimal('30.00')
        elif mode not in ('sql','notebook','job'):
            raise ValueError('unsupported sandbox mode')
        actual={'rows':3,'sum':'30.00'}
        if source:
            # Customer permissions must be bounded externally to selected sandbox resources.
            # A new job cluster provides a fresh interpreter for every request.
            namespace={'__name__':'__candidate__'}
            exec(compile(source,'candidate.py','exec'),namespace)
            actual=namespace['run_validation'](spark,fixture,owned_path)
        identity=spark.sql('SELECT current_user() AS identity').first().identity
        fields=('plan_sha256','test_id','client_id','run_id','attempt','candidate_sha256','plan_revision',
            'practice_pack_sha256','data_sha256','runtime','runtime_sha256','tool_sha256','request_key','command','source_sha256')
        return dict(result=actual,request={k:request[k] for k in fields},runtime=runtime,
            execution_identity=identity,data_sha256=sha(fixture_text.encode()),source_sha256=source_hash,result_sha256=sha(canonical(actual)))
    finally:
        spark.catalog.dropTempView(name)
        # The only resource removed is this freshly generated owned path, including
        # anything the selected candidate wrote there before an exception.
        if owned_path!=volume.rstrip('/')+'/'+name or not name.startswith('harness_'): raise ValueError('cleanup rejected')
        dbutils.fs.rm(owned_path,True)


if __name__=='__main__':
    dbutils.notebook.exit(json.dumps(run_protocol(spark,dbutils)))
