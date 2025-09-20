from apscheduler.schedulers.blocking import BlockingScheduler
from src.pipeline import final_pipeline


if __name__ == "__main__":
    print("------------------------")
    print("Starting pipeline job...")
    print("------------------------")
    final_pipeline()
    print("------------------------------")
    print("Pipeline finished successfully.")
    print("------------------------------")
