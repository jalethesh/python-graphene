import json
from tests.graphql_example_requests.ex_itemCollections import query_itemCollections_read, query_itemCollection_realItems_number_read
from .util import test_logger, set_user_to_customer, get_users_item_collection


def read_item_collections(client):

    set_user_to_customer(client)
    collection = get_users_item_collection(client)
    collection_id = collection['databaseId']
    test_logger.debug(f"created collection {collection_id}")
    mutation = query_itemCollections_read
    variables = {"collectionId": collection_id}
    url = f'http://localhost:5000/graphql-api?query={mutation}&variables={json.dumps(variables)}'
    res = client.post(url)
    data = json.loads(res.data.decode('utf-8'))
    test_logger.debug(f'read item collection returns {data}')
    collections = data['data']['itemCollections']
    assert len(collections) == 1
    assert collections[0]['databaseId'] == collection_id
    test_logger.debug(f"found collection with id {id}")


def count_items_in_collection(client):
    set_user_to_customer(client)
    collection = get_users_item_collection(client)
    collection_id = collection['databaseId']
    test_logger.debug(f"created collection {collection_id}")
    mutation = query_itemCollection_realItems_number_read
    variables = {
        "id": 10,
        "collectionId": collection_id
    }
    url = f'http://localhost:5000/graphql-api?query={mutation}&variables={json.dumps(variables)}'
    res = client.get(url)
    data = json.loads(res.data.decode('utf-8'))
    test_logger.debug(f'read item collection returns {data}')
    assert data['data']['itemCollections'][0]['count'] > 0
