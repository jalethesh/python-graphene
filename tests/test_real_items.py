
import json
from tests.graphql_example_requests.ex_realItems import del_real_item, mutate_update, real_items_by_status
from .util import test_logger, set_user_to_customer, get_random_generic_item_id, create_real_item, get_users_item_list


def update_real_item(client, id, do_assert=True):
    mutation = mutate_update
    variables = {"databaseId": id, 'condition': 'NM'}
    url = f'http://localhost:5000/graphql-api?query={mutation}&variables={json.dumps(variables)}'
    res = client.post(url)
    data = json.loads(res.data.decode('utf-8'))
    test_logger.debug(f'update real item returns {data}')
    result_ok = data['data']['updateRealItem']['ok']
    if do_assert:
        assert result_ok
    return result_ok


def delete_real_item(client, id):
    mutation = del_real_item
    variables = {"databaseId": id}
    url = f'http://localhost:5000/graphql-api?query={mutation}&variables={json.dumps(variables)}'
    res = client.post(url)
    data = json.loads(res.data.decode('utf-8'))
    test_logger.debug(f'delete real item returns {data}')
    result_ok = data['data']['deleteRealItem']['ok']
    assert result_ok
    return result_ok


def read_filters(client):
    print("starting read filtering tests")
    mutation = real_items_by_status
    variables = {"status": "NEW"}
    url = f'http://localhost:5000/graphql-api?query={mutation}&variables={json.dumps(variables)}'
    res = client.post(url)
    data = json.loads(res.data.decode('utf-8'))
    result_ok = True
    for item in data['data']['realItems']:
        if item['status'] != 'NEW':
            result_ok = False
    if len(data['data']['realItems']) < 1:
        result_ok = False
    assert result_ok
    return result_ok


def crud_real_items(client):
    # setup - create collection
    set_user_to_customer(client)
    item_list = get_users_item_list(client)
    item_list_id = item_list['databaseId']
    generic_item_id = get_random_generic_item_id(client)

    # setup - fix session data for tests
    set_user_to_customer(client)

    # create
    print(f"using {item_list_id} item list")
    real_item_id = create_real_item(client, generic_item_id, itemListId=item_list_id)
    print('create real item result', real_item_id)

    update_success = update_real_item(client, real_item_id)
    test_logger.debug(f'update real item result {update_success}')

    # delete
    success = delete_real_item(client, real_item_id)
    test_logger.debug(f'delete real item result {success}')

    # read filtering tests
    read_filters(client)


def newly_created_real_item_has_lp_condition(client):
    test_logger.debug("checking that newly created real item has LP condition")
    set_user_to_customer(client)
    item_list = get_users_item_list(client)
    item_list_id = item_list['databaseId']

    generic_item_id = get_random_generic_item_id(client)
    print(f"item_list id {item_list_id}, generic item id {generic_item_id}")
    real_item = create_real_item(client, generic_item_id, itemListId=item_list_id, return_object=True)
    assert real_item['condition'] == 'LP'
    delete_real_item(client, real_item['databaseId'])
