from concurrent.futures import ThreadPoolExecutor, as_completed
from src.utils import (
    fetch_missing_startups,
    fetch_startups,
    process_and_store_initial_articles,
    process_and_store_daily_articles,
)
from src.logger import logging
import time
import psycopg2
import os
import json
from datetime import datetime


# --- Helper for retry logic ---
def run_with_retries(func, retries=2, delay=5, *args):
    """
    Runs a function with retry logic for transient errors.
    Retries on OperationalError or network-like failures.
    """
    attempt = 0
    while attempt <= retries:
        try:
            return func(*args)
        except (psycopg2.OperationalError, ConnectionError, TimeoutError) as e:
            attempt += 1
            if attempt > retries:
                raise
            logging.warning(f"Retrying ({attempt}/{retries}) after error: {e}")
            time.sleep(delay)
        except Exception:
            raise


# --- Startup Processing Functions ---

def process_missing(startup_id, startup_name):
    """Handles initial article fetching for new startups with retry logic."""
    start = time.time()
    try:
        def task():
            process_and_store_initial_articles(startup_id, startup_name)
        run_with_retries(task, retries=2, delay=5)

        duration = round(time.time() - start, 2)
        logging.info(f"[MISSING] Completed for {startup_name} in {duration}s")
        return {"name": startup_name, "phase": "missing", "status": "success", "time": duration}

    except psycopg2.OperationalError as e:
        duration = round(time.time() - start, 2)
        logging.error(f"[MISSING] DB connection lost for {startup_name}: {e}")
        return {"name": startup_name, "phase": "missing", "status": "db_error", "time": duration}

    except Exception as e:
        duration = round(time.time() - start, 2)
        logging.error(f"[MISSING] Failed for {startup_name}: {e}")
        return {"name": startup_name, "phase": "missing", "status": "failed", "time": duration}


def process_existing(startup_id, startup_name):
    """Handles daily article fetching for existing startups with retry logic."""
    start = time.time()
    try:
        def task():
            process_and_store_daily_articles(startup_id, startup_name)
        run_with_retries(task, retries=2, delay=5)

        duration = round(time.time() - start, 2)
        logging.info(f"[DAILY] Completed for {startup_name} in {duration}s")
        return {"name": startup_name, "phase": "daily", "status": "success", "time": duration}

    except psycopg2.OperationalError as e:
        duration = round(time.time() - start, 2)
        logging.error(f"[DAILY] DB connection lost for {startup_name}: {e}")
        return {"name": startup_name, "phase": "daily", "status": "db_error", "time": duration}

    except Exception as e:
        duration = round(time.time() - start, 2)
        logging.error(f"[DAILY] Failed for {startup_name}: {e}")
        return {"name": startup_name, "phase": "daily", "status": "failed", "time": duration}


# --- Save summary JSON file ---
def save_summary(results, total_time):
    os.makedirs("logs", exist_ok=True)
    summary_path = os.path.join("logs", f"pipeline_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    summary = {
        "run_at": datetime.now().isoformat(),
        "total_time_sec": total_time,
        "total_startups": len(results),
        "results": results,
    }
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)
    logging.info(f"Pipeline summary saved to {summary_path}")


# --- Main Pipeline ---
def final_pipeline(max_workers=None):
    start_time = time.time()
    results = []

    logging.info("=== PIPELINE STARTED ===")

    if not max_workers:
        cpu_count = os.cpu_count() or 4
        max_workers = max(2, min(10, cpu_count // 2))
        logging.info(f"Auto-set max_workers = {max_workers}")

    # Phase 1: Missing startups
    missing_startups = fetch_missing_startups()
    logging.info(f"Found {len(missing_startups)} missing startups")

    if missing_startups:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(process_missing, sid, sname): sname for sid, sname in missing_startups}
            for future in as_completed(futures):
                result = future.result()
                results.append(result)

    # Phase 2: Existing startups
    all_startups = fetch_startups()
    missing_ids = {sid for sid, _ in missing_startups}
    existing_startups = [(sid, sname) for sid, sname in all_startups if sid not in missing_ids]
    logging.info(f"Found {len(existing_startups)} existing startups")

    if existing_startups:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(process_existing, sid, sname): sname for sid, sname in existing_startups}
            for future in as_completed(futures):
                result = future.result()
                results.append(result)

    total_time = round(time.time() - start_time, 2)
    logging.info(f"=== PIPELINE COMPLETED in {total_time}s ===")
    save_summary(results, total_time)

    success_count = sum(1 for r in results if r["status"] == "success")
    failed_count = sum(1 for r in results if r["status"] != "success")
    logging.info(f"Summary: {success_count} succeeded | {failed_count} failed")

    return results
