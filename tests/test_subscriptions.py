import pytest
from app import create_app
import json
from tests.graphql_example_requests.ex_subscriptions import create_sub, delete_sub
from flask import session
from flask import jsonify
from base64 import urlsafe_b64decode


@pytest.fixture
def client():
    app = create_app()

    @app.route('/session/userid/<ID>')
    def set_user_id(ID):
        print("setting userid", ID)
        session['user_id'] = int(ID)
        session['username'] = 'dylans-test-user'
        return jsonify({"message": "ID was set"})

    @app.route('/session/wordpressid/<ID>')
    def set_wordpress_id(ID):
        print("setting userid", ID)
        session['ID'] = int(ID)
        return jsonify({"message": "ID was set"})

    return app.test_client()


def set_user_to_customer(client):
    client.get("http://localhost:5000/session/userid/10")
    client.get("http://localhost:5000/session/wordpressid/714")


def extract_value_from_b64(b64_encoded_string):
    item_base64 = b64_encoded_string
    return urlsafe_b64decode(item_base64).decode('utf-8').split(':')[1]


def create_subscription(client):
    mutation = create_sub
    variables = {"subscriberId": 10, "userId": 10 }
    url = f'http://localhost:5000/graphql-api?query={mutation}&variables={json.dumps(variables)}'
    res = client.post(url)
    data = json.loads(res.data.decode('utf-8'))
    print('create subscriber returns', data)
    encoded_id = data['data']['createSubscription']['subscription']['id']
    id = int(extract_value_from_b64(encoded_id))
    assert id > 0
    return id


def delete_subscription(client, id):
    mutation = delete_sub
    variables = {"id": id}
    url = f'http://localhost:5000/graphql-api?query={mutation}&variables={json.dumps(variables)}'
    res = client.post(url)
    data = json.loads(res.data.decode('utf-8'))
    print('delete subscriber returns', data)
    result_ok = data['data']['deleteSubscription']['ok']
    assert result_ok
    return result_ok


def crud_subscription(client):
    # setup - fix session data for tests
    set_user_to_customer(client)

    # create
    subscription_id = create_subscription(client)
    print(subscription_id)
    # delete
    success = delete_subscription(client, subscription_id)
    print("delete subscription result", success)
