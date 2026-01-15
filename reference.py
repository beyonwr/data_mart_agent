from typing import Dict
import requests
import pandas as pd 
from io import BytesIO

load_dotenv()

portal_url = os.getenv("DATA_MART_URL")
user_id = os.getenv("USER_ID")
program_id = os.getenv("PROGRAM_ID")
job_id = os.getenv("JOB_ID")

def get_token(user_id: str):
    authentication = {"user_id": user_id}

    r = requests.post(portal_url + "/v1/signin", json=authentication)
    if r.json()["code"] == 200:
        return r.json()["data"]
    else:
        return r.json()["message"]

def get_data(program_id:str, token: str):
    headers = {"Content-Type": "application/json", "Authentication": f"Bearer {token}"}

    r = requests.get(portal_url + "/v1/info/join_file/" + program_id, headers=headers)
    if r.json()["code"] != 200:
        temp_df = {r.json()["message"]}
        return pd.DataFrame(temp_df)

    file_url = r.json()["data"]["file_url"]
    r2 = requests.get(file_url, verify=False)
    data = BytesIO(r2.content)
    
    temp_df = pd.read_parquet(data)

    return temp_df

def get_sync_data(program_id: str, token: str, filters: Dict[str, str] = {}):

    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}

    body = {
        "programid": program_id,
    }

    if len(filters) > 0:
        body["filters"] = filters
    
    print(portal_url + "/v1/datas/join/dynamic/exporter")
    r = requests.post(
        portal_url + "/v1/datas/join/dynamic/exporter", json=body, headers=headers
    )

    print(r.json())

    if r.json()["code"] == 200:
        return r.json()["data"]
    else:
        return r.json()["message"]


def get_sync_file_data(program_id: str, token: str, filters: Dict[str, str] = {}):
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}

    body = {
        "programid": program_id,
    }

    if len(filters) > 0:
        body["filters"] = filters
    print(portal_url + "v1/datas/join/dynamic/exporter")
    r = requests.post(
        portal_url + "v1/datas/join/dynamic/exporter", json=body, headers=headers
    )
    print(r.json())
    if r.json()["code"] == 200:
        return r.json()
    else:
        return r.json()["message"]

def get_metadata(program_id: str, token: str, filters: Dict[str, str] = {}):

    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}

    body = {
        "programid": program_id,
    }

    if len(filters) > 0:
        body["filters"] = filters
    
    print(portal_url + "/v1/datas/join/dynamic/exporter")
    r = requests.post(
        portal_url + "/v1/datas/join/dynamic/exporter", json=body, headers=headers
    )

    print(r.json())

    if r.json()["code"] == 200:
        return r.json()["columns"]
    else:
        return r.json()["message"]



token = get_token(user_id)
print(token)




from typing import Literal
from enum import Enum 

class DataCatalogOperators(Enum):
    EQUAL = "EQ" # equal to
    IN = "IN" # in
    NOT_IN = "NOT IN" # not in
    BETWEEN = "BETWEEN" # value between
    NOT_NULL = "NN" # not null
    IS_NULL = "NY" # is null
    GREATER_THAN = "GT" # greater than
    GREATER_THAN_OR_EQUALL = "GTE" # greater than or equal to
    LOWER_THAN = "LT" # lower than
    LOWER_THAN_EQUAL = "LTE" # lower than or equal to
    NOT_EQUAL = "NE" # not equal
    LIKE = "LIKE" # like, LIKE operator for sql
    NOT_LIKE = "NOT LIKE" # not like

class DatCatalogDtypes(Enum):
    VARCHAR = "VARCHAR"
    DOUBLE = "DOUBLE"
    BIGINT = "BIGINT"
    DATE = "DATE"
    TIMESTAMP = "TIMESTAMP"

def make_filter(
    column_name: strm value, data__type: DatCatalogDtypes, data_operator: DataCatalogOperators, base_filter = {}
):

    if (type(value) in [list, tuple, set]) and (data_operator in [DataCatalogOperators.IN, DataCatalogOperators.NOT_IN]):
        value = "|".join(value)

    base_filter[column_name] = {
        "data_value": value,
        "data_type": data_type.value,
        "data_operator": data_operator.value,
    }

    return base_filter



program_id = "JN00000"
f1 = {}
f1 = make_filter("x.lot_compt_date_time", "2026-01-01 00:00:00|2026-01-01 00:05:00", DatCatalogDtypes.TIMESTAMP, DataCatalogOperators.BETWEEN, f1)

print("FILTER", f1)

data = get_sync_data(program_id, token, f1)
df = pd.DataFrame.from_records(data)

