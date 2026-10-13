"""Candidate protocol for a selected Spark worker or synthetic job."""
from decimal import Decimal


def run_validation(spark,fixture,scratch_path):
    from pyspark.sql.types import StructType,StructField,IntegerType,DecimalType
    schema=StructType([StructField('order_id',IntegerType(),False),StructField('amount',DecimalType(18,2),True)])
    rows=[(row['order_id'],Decimal(row['amount']) if row['amount'] is not None else None) for row in fixture['orders']]
    frame=spark.createDataFrame(rows,schema)
    assert frame.schema==schema
    return {'rows':frame.count(),'sum':str(frame.groupBy().sum('amount').first()[0] or Decimal('0.00'))}
