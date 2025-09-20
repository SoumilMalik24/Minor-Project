from apscheduler.schedulers.blocking import BlockingScheduler
from src.pipeline import final_pipeline

def run_pipeline():
    print("------------------------")
    print("Starting pipeline job...")
    print("------------------------")
    final_pipeline()
    print("------------------------------")
    print("Pipeline finished successfully.")
    print("------------------------------")

if __name__ == "__main__":
    scheduler = BlockingScheduler()

    scheduler.add_job(run_pipeline, 'cron', hour='6,12,18')

    print("Scheduler started. Waiting for jobs...")
    scheduler.start()
