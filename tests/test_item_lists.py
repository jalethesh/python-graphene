from cgi import test
from tests.graphql_example_requests.ex_item_lists import query_itemLists_read, mutation_create_itemLists, mutation_update_itemLists, mutation_delete_itemLists
from .util import test_logger, set_user_to_customer
import json  

def create_item_list(client, do_assert=True):
    mutation = mutation_create_itemLists
    variables = {"name": "Cringe list"}
    url = f'http://localhost:5000/graphql-api?query={mutation}&variables={json.dumps(variables)}'
    res = client.post(url)
    data = json.loads(res.data.decode('utf-8'))
    test_logger.debug(f'creating item list name returns {data}')
    result_ok = data['data']['createItemList']['ok']
    global id
    id = int(data['data']['createItemList']['itemList']['databaseId'])
    if do_assert:
        assert result_ok
    return result_ok

def update_item_list(client, do_assert=True):
    mutation = mutation_update_itemLists
    variables = {"databaseId" : id, "name": "Based list"}
    url = f'http://localhost:5000/graphql-api?query={mutation}&variables={json.dumps(variables)}'
    res = client.post(url)
    data = json.loads(res.data.decode('utf-8'))
    test_logger.debug(f'updating item list name returns {data}')
    result_ok = data['data']['updateItemList']['ok']
    if do_assert:
        assert result_ok
    return result_ok

def delete_item_list(client, do_assert=True):
    mutation = mutation_delete_itemLists
    variables = {"databaseId" : id}
    url = f'http://localhost:5000/graphql-api?query={mutation}&variables={json.dumps(variables)}'
    res = client.post(url)
    data = json.loads(res.data.decode('utf-8'))
    test_logger.debug(f'deleting item list name returns {data}')
    result_ok = data['data']['deleteItemList']['ok']
    if do_assert:
        assert result_ok
    return result_ok

def crud_item_lists(client):
    test_logger.debug("Set user to customer")
    set_user_to_customer(client)
    
    create = create_item_list(client)
    print("Create item list:", create)
    test_logger.debug(f'create item list result: {create}')

    update = update_item_list(client)
    print("Update item list:", create)
    test_logger.debug(f'update item list result: {update}')
    
    delete = delete_item_list(client)
    print("Delete item list:", create)
    test_logger.debug(f'delete item list result: {delete}')
