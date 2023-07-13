from .util import get_users_item_collection, create_real_item, get_random_generic_item_id, \
    set_user_to_customer, test_logger, get_users_item_list
from tests.test_real_items import delete_real_item
from tests.graphql_example_requests.ex_conditions import query_conditions_read, mutate_condition_on_real_item
import json


def read_conditions(client):
    query = query_conditions_read
    url = f'http://localhost:5000/graphql-api?query={query}'
    res = client.post(url)
    data = json.loads(res.data.decode('utf-8'))
    test_logger.debug(f'read conditions returns {data}')
    result_ok = data['data']['conditions']
    assert result_ok
    return result_ok


def add_condition_to_real_item(client):
    test_logger.debug("adding condition to real item")
    set_user_to_customer(client)
    item_list = get_users_item_list(client)
    item_list_id = item_list['databaseId']
    generic_item_id = get_random_generic_item_id(client)
    test_logger.debug(f"item_list_id {item_list_id}, generic item id {generic_item_id}")
    real_item_id = create_real_item(client, generic_item_id, itemListId=item_list_id)
    mutation = mutate_condition_on_real_item
    test_logger.debug(f"item_list_id {item_list_id}, generic item id {generic_item_id}, real item id {real_item_id}")
    
    variables = {"databaseId": real_item_id, 'condition': 'HP'}
    url = f'http://localhost:5000/graphql-api?query={mutation}&variables={json.dumps(variables)}'
    res = client.post(url)
    data = json.loads(res.data.decode('utf-8'))
    test_logger.debug(f'update real item returns {data}')
    result_ok = data['data']['updateRealItem']['ok']
    assert result_ok

    delete_real_item(client, real_item_id)




