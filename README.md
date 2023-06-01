Repository for Neos API coding challenge

## Table of Contents

- [Background](#background)
- [Architecture](#architecture)
- [Testing](#testing)
- [Run Locally](#run-locally)
- [TO-DO](#to-do)
- [Maintainers](#maintainers)
- [License](#license)

## Background

### Problem

Integrating with multiple 3rd party APIs can be challenging for the data team due to the unique and diverse nature of each API. One of the APIs the team is currently working with is NeoWs, also known as Near Earth Object Web Service. This API, provided by NASA, offers RESTful web service information on near-earth asteroids. To ensure proper data management, we need to store all our data in a database. We will only pull data with a start date of 1982-12-10, convert all epochs to an ISO8601 timestamp (GMT), and only store imperial measurements (feet, miles). Furthermore, we will treat the neo_reference_id as PII by storing only the last 4 digits.

### Solution

Our data has been successfully stored in mongodb. We chose this platform because it's perfect for storing JSON files, which is exactly what we receive from the API. To keep our data organized, we created two collections: full_neoWs_info, which contains the entire JSON document from the API, and neos, which contains individual NEO records from each JSON. After extracting data from the API starting from December 10th, 1982, we explored the data and found that the schema remained consistent throughout. Therefore, we manually identified and converted all dates to ISO8610 timestamp, removed non-imperial measurements, and kept only the last four digits of the neo_reference_id due to PII concerns.

## Architecture
![Architecture of API Challenge](https://github.com/vjkaza32/neoWs_API/blob/main/api_archirecture_diagram.drawio.png?raw=true)

## Testing
See [Run Locally](#run-locally)

TODO: Implement more tests in tests folder

Install missing test requirements by running:
```sh
pip install -r test-requirements.txt
```
Then run
```sh
pytest --junitxml=pytest-report.xml -s tests
```
and see if all the tests pass.

## Run Locally
First, fill the .env file with your values for the environment variables

Next, install missing requirements by running:
```sh
pip install -r requirements.txt
```

Then we will run our app by first either [creating a virtual environment](https://code.visualstudio.com/docs/python/environments#_creating-environments) and running the application in there:
```sh
(venv) device_username /path_to_repo/neoWs_API/api_connection.py
```
OR by running our local install of python with the application
```sh
/opt/homebrew/bin/python3.10 /path_to_repo/neoWs_API/api_connection.py
```

## TO-DO
- Implement more tests in test_app.py and any other unit tests
- Implement replication depending upon necessity of data
- Implement check to see how long parsing API is taking and quit if it is taking too long
- Implement a way to store logs and errors (key-value database works well here)

## Maintainers

This project is maintained by me

## License

[MIT](LICENSE)