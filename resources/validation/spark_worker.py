"""Synthetic L1 worker callable; pinned image supplies Spark and Java."""
from decimal import Decimal


def total(fixture):
    from pyspark.sql import SparkSession
    from pyspark.sql.types import StructType,StructField,IntegerType,DecimalType
    spark=SparkSession.builder.master('local[1]').appName('synthetic-validation').config('spark.ui.enabled','false').getOrCreate()
    try:
        schema=StructType([StructField('order_id',IntegerType(),False),StructField('amount',DecimalType(18,2),True)])
        rows=[(row['order_id'],Decimal(row['amount']) if row['amount'] is not None else None) for row in fixture['orders']]
        frame=spark.createDataFrame(rows,schema)
        assert frame.count()<=32
        return dict(rows=[[r.order_id,str(r.amount) if r.amount is not None else None] for r in frame.orderBy('order_id').take(32)],
            schema=[dict(name=f.name,type=f.dataType.simpleString(),nullable=f.nullable) for f in frame.schema.fields],
            sum=str(frame.groupBy().sum('amount').first()[0] or Decimal('0.00')))
    finally:
        spark.stop()
