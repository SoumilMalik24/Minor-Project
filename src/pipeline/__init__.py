from src.database import db_connection
from src.utils import *
from src.logger import logging


def final_pipeline():
    logging.info("Entered Pipeline")
    missing = fetch_missing_startups()
    print(f"There are {len(missing)} Startups that are added")
    logging.info("checked for Missing startups in the articles db done")

    try:
        for startup_id, startup_name in missing:
            logging.info(f"Fetching news for: {startup_name} (id={startup_id})")
            process_and_store_initial_articles(startup_id,startup_name)

    finally:
        all_startups = fetch_startups()
        missing_id = {stid for stid,_ in missing}
        present_startups = [(stid,name) for stid,name in all_startups if stid not in missing_id]
        logging.info('checked for not missing values')

        for startup_id,startup_name in present_startups:
            logging.info('working on single day fetching')
            process_and_store_daily_articles(startup_id,startup_name)





