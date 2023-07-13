import pytest
from app import create_app
import json
from tests.graphql_example_requests.ex_media import add_media, del_media, upd_media
from flask import session
from flask import jsonify
from base64 import urlsafe_b64decode

from tests.util import get_real_item
from .util import set_user_to_admin, set_user_to_customer, extract_value_from_b64, test_logger


def create_media(client):
    mutation = add_media
    real_item = get_real_item(client)
    variables = {"mediaUrl": 'https://purplemana-media.s3.amazonaws.com/12/262294/zz__34-AP-122820-front-ebay.jpg',
                 "realItemId": real_item['databaseId'], "label": "testing-label-string", "type": "testing-type-string"}
    url = f'http://localhost:5000/graphql-api?query={mutation}&variables={json.dumps(variables)}'
    res = client.post(url)
    data = json.loads(res.data.decode('utf-8'))
    test_logger.debug(f'create media returns {data}')
    id = int(data['data']['createMedia']['media']['databaseId'])
    assert id > 0
    return id


def update_media(client, id):
    mutation = upd_media
    variables = {"databaseId": id, "label": "updated-testing-label-string", "type": "updated-testing-type-string"}
    url = f'http://localhost:5000/graphql-api?query={mutation}&variables={json.dumps(variables)}'
    res = client.post(url)
    data = json.loads(res.data.decode('utf-8'))
    test_logger.debug(f'update media returns {data}')
    result_ok = data['data']['updateMedia']['ok']
    assert result_ok
    return result_ok


def delete_media(client, id):
    mutation = del_media
    variables = {"databaseId": id}
    url = f'http://localhost:5000/graphql-api?query={mutation}&variables={json.dumps(variables)}'
    res = client.post(url)
    data = json.loads(res.data.decode('utf-8'))
    test_logger.debug(f'delete media returns {data}')
    result_ok = data['data']['deleteMedia']['ok']
    assert result_ok
    return result_ok


def crud_media(client):
    # setup - fix session data for tests
    set_user_to_customer(client)

    # create
    media_id = create_media(client)
    print(media_id)

    update_success = update_media(client, media_id)
    test_logger.debug(f'update media result {update_success}')

    # delete
    success = delete_media(client, media_id)
    test_logger.debug(f'update media result {success}')


