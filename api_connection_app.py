import requests
import json
import jsonschema
import os
import logging
import urllib.parse

from datetime import datetime
from tenacity import retry, stop_after_attempt, retry_if_exception_type, wait_fixed
from jsonschema import validate
from dotenv import load_dotenv
from pathlib import Path
from pymongo import MongoClient

logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

current_directory = os.path.dirname(os.path.abspath(__file__))
dotenv_path = Path(f"{current_directory}/.env")
load_dotenv(dotenv_path=dotenv_path)

DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")
NEOS_COLLECTION_NAME = os.getenv("NEOS_COLLECTION_NAME")
RAW_NEOS_COLLECTION_NAME = os.getenv("RAW_NEOS_COLLECTION_NAME")
API_URL = os.getenv("API_URL")
API_TOKEN = os.getenv("API_TOKEN")
INSERT_RAW = True


def validate_json(jsonData, check_against_schema):
    try:
        validate(instance=jsonData, schema=check_against_schema)
        logger.info("Validated Schema")
    except jsonschema.exceptions.ValidationError as err:
        raise jsonschema.exceptions.ValidationError(
            "This json does not match with what we expected. Exiting now."
        )
    return True


@retry(
    stop=stop_after_attempt(4),
    wait=wait_fixed(20),
    retry=retry_if_exception_type(TimeoutError),
)  # We retry 4 times if there is a TimeoutError to try and send the data since it might be a temporary issue
def get_neos(start_date= datetime.now().strftime("%Y-%m-%d"), end_date=None):
    if end_date == None:
        end_date = start_date
    try:
        response = requests.get(
            f"{API_URL}?start_date={start_date}&end_date={end_date}&api_key={API_TOKEN}"
        )  # API will assume end_date to be 7 days after the start date (8 total days of data) if none is given
    except requests.exceptions.Timeout:
        raise TimeoutError("There was a timeout error.")
    except requests.exceptions.HTTPError as e:
        raise requests.exceptions.HTTPError(f"Invalid HTTP Response. {e}")
    except requests.exceptions.ConnectionError as e:
        raise ConnectionError(f"Network Error. {e}")
    except requests.exceptions.RequestException as e:
        raise SystemExit(f"Error: {e}")

    return response.json()


def process_neos(data):
    client = connect_to_mongo()
    for date in data["near_earth_objects"]:
        logger.info(f"We are currently processing {date}'s neos")
        neo_list = data["near_earth_objects"][date]
        for neo in neo_list:
            # We store only the last 4 digits due to PII concerts
            neo["neo_reference_id"] = neo["neo_reference_id"][-4:]

            # Remove non imperial measurements
            del neo["estimated_diameter"]["kilometers"]
            del neo["estimated_diameter"]["meters"]

            close_approach_data = neo["close_approach_data"]
            for approach in close_approach_data:
                # Convert epochs to ISO8601 timestamp (GMT)
                approach["close_approach_date"] = datetime.strptime(
                    approach["close_approach_date"], "%Y-%m-%d"
                ).isoformat()
                approach["close_approach_date_full"] = datetime.strptime(
                    approach["close_approach_date_full"], "%Y-%b-%d %H:%M"
                ).isoformat()

                # Remove non imperial measurements
                del approach["miss_distance"]["astronomical"]
                del approach["miss_distance"]["lunar"]
                del approach["miss_distance"]["kilometers"]
                del approach["relative_velocity"]["kilometers_per_second"]
                del approach["relative_velocity"]["kilometers_per_hour"]
            insert_into_mongo(neo, client)

        logger.info(f"We have finished processing {date}'s neos")
    close_mongo_connection(client)
    return data


@retry(
    stop=stop_after_attempt(4),
    wait=wait_fixed(20),
    retry=retry_if_exception_type(TimeoutError),
)  # We retry 4 times if there is a TimeoutError to try and send the data since it might be a temporary issue
def connect_to_mongo():
    escaped_db_user = urllib.parse.quote_plus(DB_USER)
    escaped_db_pw = urllib.parse.quote_plus(DB_PASSWORD)
    escaped_db_host = urllib.parse.quote_plus(DB_HOST)
    try:
        logger.info("Attempting to connect to client")
        client = MongoClient(
            f"mongodb+srv://{escaped_db_user}:{escaped_db_pw}@{escaped_db_host}/?retryWrites=true&w=majority"
        )
    except requests.exceptions.Timeout:
        raise TimeoutError("There was a timeout error.")
    except requests.exceptions.ConnectionError as e:
        raise ConnectionError(f"Network Error. {e}")
    except requests.exceptions.RequestException as e:
        raise SystemExit("Error: {e}")

    logger.info("Connected to client")
    return client


@retry(
    stop=stop_after_attempt(4),
    wait=wait_fixed(20),
    retry=retry_if_exception_type(TimeoutError),
)  # We retry 4 times if there is a TimeoutError to try and send the data since it might be a temporary issue
def insert_into_mongo(data, client, collection_name=NEOS_COLLECTION_NAME):
    db = client[DB_NAME]
    collection = db[collection_name]
    try:
        collection.insert_one(data)
    except requests.exceptions.Timeout:
        raise TimeoutError("There was a timeout error.")
    except requests.exceptions.ConnectionError as e:
        raise ConnectionError(f"Network Error. {e}")
    except requests.exceptions.RequestException as e:
        raise SystemExit("Error: {e}")


def close_mongo_connection(client):
    client.close()
    logger.info("Mongo connection has been closed.")


if __name__ == "__main__":
    json_path = os.path.join(
        current_directory, "schemas", "sample_schema.json"
    )  # TO-DO Update the current neos.json to reflect the neos schema and replace the sample_schema.json with the neos.json
    with open(json_path) as file:
        sample_schema = json.load(file)

    start_date = datetime(1982, 12, 10).strftime("%Y-%m-%d")
    end_date = datetime(1982, 12, 12).strftime("%Y-%m-%d")
    data = get_neos(start_date, end_date)

    validate_json(data, sample_schema)
    data = process_neos(data)

    if INSERT_RAW:
        client = connect_to_mongo()
        insert_into_mongo(data, client, RAW_NEOS_COLLECTION_NAME)
        close_mongo_connection(client)
