import json
from tests.graphql_example_requests.ex_genericItems import query_genericItems_1
from tests.graphql_example_requests.ex_itemCollections import mutation_itemCollections_create, \
    mutation_itemCollections_delete, query_itemCollections_1
from tests.graphql_example_requests.ex_item_lists import query_itemLists_read
from tests.graphql_example_requests.ex_realItems import add_real_item, single_real_item
import time
from base64 import urlsafe_b64decode

from loggers import test_logger


def set_user_to_customer(client, log_string=''):
    # 10 - 714 is the dylans_pleb guest roled user
    client.get("http://localhost:5000/session/userid/10")
    client.get("http://localhost:5000/session/wordpressid/714")
    client.get("http://localhost:5000/session/roles/guest")
    test_logger.debug("setting userid to 10. wp id to 714. role to guest "+log_string)


def set_user_to_admin(client, log_string=''):
    test_logger.debug("setting userid to 4. wp id to 714. role to admin")
    client.get("http://localhost:5000/session/userid/4")
    client.get("http://localhost:5000/session/wordpressid/701")
    client.get("http://localhost:5000/session/roles/administrator")
    test_logger.debug("setting userid to 4. wp id to 701. role to admin "+log_string)


def extract_value_from_b64(b64_encoded_string):
    item_base64 = b64_encoded_string
    return urlsafe_b64decode(item_base64).decode('utf-8').split(':')[1]


def get_random_generic_item_id(client):
    generic_item_query = query_genericItems_1
    url = f'http://localhost:5000/graphql-api?query={generic_item_query}'
    res = client.post(url)
    data = json.loads(res.data.decode('utf-8'))
    single_generic_item_id_encoded = data['data']['genericItems'][0]['id']
    itemId = extract_value_from_b64(single_generic_item_id_encoded)
    return itemId


def create_item_collection(client):
    now = str(int(time.time()))
    url = f'http://localhost:5000/graphql-api?query={mutation_itemCollections_create.replace("7", now)}'
    res = client.post(url)
    data = json.loads(res.data.decode('utf-8'))
    return data['data']['createCollection']['collection']['databaseId']


def get_users_item_collection(client):
    url = f'http://localhost:5000/graphql-api?query={query_itemCollections_1}'
    res = client.post(url)
    data = json.loads(res.data.decode('utf-8'))
    test_logger.debug(f" item collections query 1 {query_itemCollections_1}")
    test_logger.debug(f"found these collections {data}")
    return data['data']['itemCollections'][0]


def get_users_item_list(client):
    url = f'http://localhost:5000/graphql-api?query={query_itemLists_read}'
    res = client.post(url)
    data = json.loads(res.data.decode('utf-8'))
    test_logger.debug(f"itemLists read query {query_itemLists_read}")
    test_logger.debug(f"found these itemLists {data}")
    return data['data']['itemLists'][0]


def delete_item_collection(client, collection_id):
    url = f'http://localhost:5000/graphql-api?query={mutation_itemCollections_delete.replace("29", str(collection_id))}'
    res = client.post(url)
    data = json.loads(res.data.decode('utf-8'))
    print("deleted items", data)


def create_real_item(client, genericItemId, itemListId=0, collectionId=None, return_object=False):
    mutation = add_real_item
    variables = {"itemId": genericItemId, "itemListId": itemListId}
    url = f'http://localhost:5000/graphql-api?query={mutation}&variables={json.dumps(variables)}'
    res = client.post(url)
    data = json.loads(res.data.decode('utf-8'))
    print('create real item returns', data)
    id = int(data['data']['createRealItem']['realItem']['databaseId'])
    assert id > 0
    if return_object:
        return data['data']['createRealItem']['realItem']
    return id


def get_real_item(client, user_id=0):
    mutation = single_real_item
    variables = {"userId": user_id}
    url = f'http://localhost:5000/graphql-api?query={mutation}&variables={json.dumps(variables)}'
    res = client.post(url)
    data = json.loads(res.data.decode('utf-8'))
    return data['data']['realItems'][0]
