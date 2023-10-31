'''
TITLE: MONTHLY PIPELINE DAG
DAG ID: monthly_dag_pipeline
SCHEDULE_INTERVAL: EVERY LAST DAY OF THE MONTH AT 11PM
DESCRIPTION:
This DAG runs the monthly pipeline for the last month. 

AUTHOR: SARTAJ
'''

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator

from monthly_scripting_kafka_consumer import MonthlyScrapingConsumer
from monthly_scripting_kafka_producer import MonthlyScrapingProducer

from monthly_script import MonthlyScript

default_args = {
    'owner': 'Sartaj',
    'depends_on_past': False,
    'retry': 1,
    'retry_delay': timedelta(minutes=1)
}

RAW_DATA_SOURCE = "s3://raw_data_source"
RAW_DATA_DESTINATION = "s3://raw_data_destination"

PROCESSED_DATA_SOURCE = "s3://processed_data_source"
PROCESSED_DATA_DESTINATION = "s3://processed_data_destination"
PROCESSED_DATA_BACKUP_DESTINATION = "s3://processed_data_backup_destination"

def monthly_pipeline_start():
    print("Pipeline started at {}".format(datetime.now()))

def run_consumer():
    print("Consumer awoken at {}".format(datetime.now()))
    monthly_scraping_consumer_obj = MonthlyScrapingConsumer()
    monthly_scraping_consumer_obj.runner()

def run_producer():
    print("Producer awoken at {}".format(datetime.now()))
    monthly_scraping_producer_obj = MonthlyScrapingProducer()
    monthly_scraping_producer_obj.runner()

def spark_data_processing_job():
    print("Spark job started at {}".format(datetime.now()))
    monthly_script_obj = MonthlyScript()
    monthly_script_obj.runner()

def trigger_monthly_dashboard():
    print("Dashboard triggered at {}".format(datetime.now()))

with DAG(
    default_args=default_args,
    dag_id="monthly_dag_pipeline",
    schedule_interval='0 23 L * *', # Last day of every month at 11pm  
    start_date=datetime(2022, 10, 12),  
    catchup=False,
) as dag:
    task0= PythonOperator(
        task_id='monthly_pipeline_start',
        python_callable=monthly_pipeline_start
    )

    task1 = PythonOperator(
        task_id='consumer_awoken',
        python_callable=run_consumer
    )
    
    task2 = PythonOperator(
        task_id='producer_awoken',
        python_callable=run_producer
    )

    task3 = BashOperator(
        task_id='backup_raw_data',
        bash_command=f's3_backup_script.sh {RAW_DATA_SOURCE} {RAW_DATA_DESTINATION}',
    )

    task4 = PythonOperator(
        task_id='spark_data_processing_job',
        python_callable=spark_data_processing_job
    )

    task5 = BashOperator(
        task_id='backup_processed_data',
        bash_command=f's3_backup_script.sh {PROCESSED_DATA_SOURCE} {PROCESSED_DATA_BACKUP_DESTINATION}',
    )

    task6 = BashOperator(
        task_id='export_cleaned_data',
        bash_command=f'ec2_to_s3_load_script.sh {PROCESSED_DATA_SOURCE} {PROCESSED_DATA_DESTINATION}',
    )
    
    task7 = PythonOperator(
        task_id='trigger_monthly_dashboard',
        python_callable=trigger_monthly_dashboard
    )

    task8 = BashOperator(
         task_id='pipeline_housekeeping',
        bash_command=f'pipeline_housekeeping.sh path/to/localEC2/folder/',
    )
    # Pipeline
    task0 >> [task1, task2] >> task3 >> task4 >> [task5, task6] >> task7 >> task8
  