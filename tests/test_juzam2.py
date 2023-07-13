import pytest
from app import create_app
from flask import session
from flask import jsonify

from .graphql_example_requests.ex_genericItems import query_genericItems_1
from .graphql_example_requests.ex_itemCollections import query_itemCollections_1
from .graphql_example_requests.ex_sets import query_sets_1
from .test_logger import log_debug
from .test_conditions import add_condition_to_real_item, read_conditions
from .test_item_collections import read_item_collections, count_items_in_collection
from .test_media import crud_media
from .test_offers import offers_filter_by_generic_item_id
from .test_real_items import crud_real_items, newly_created_real_item_has_lp_condition
from .test_transactions import CRUD_transactions, normal_sequence, approved_transaction_items_should_not_be_updateable
from .test_file_upload import _upload
from .test_multipliers import show_multipliers
from .test_item_lists import crud_item_lists

import json
from .util import test_logger


@pytest.fixture
def client():
    app = create_app()
    app_context = app.test_request_context()
    app_context.push()

    @app.route('/session/userid/<ID>')
    def set_user_id(ID):
        test_logger.debug("setting userid " + str(ID))
        session['user_id'] = int(ID)
        session['username'] = 'dylans-test-user'
        session['roles'] = ['guest']
        return jsonify({"message": "ID was set"})

    @app.route('/session/wordpressid/<ID>')
    def set_wordpress_id(ID):
        test_logger.debug("setting wp id " + str(ID))
        session['ID'] = int(ID)
        return jsonify({"message": "ID was set"})

    @app.route('/session/roles/<role>')
    def set_roles(role):
        test_logger.debug("setting roles " + role)
        session['roles'] = role
        return jsonify({"message": "role was set"})

    return app.test_client()


def test_graphql_endpoint(client):
    graphiql = client.get("http://localhost:5000/graphql-api")
    test_logger.debug(f"get request to api endpoint {graphiql}")


def test_loggers():
    log_debug()


def test_item_collections(client):
    test_logger.debug("starting CRUD operations as customer user")
    read_item_collections(client)
    count_items_in_collection(client)


def test_real_items(client):
    test_logger.debug("starting tests for real items")
    crud_real_items(client)
    newly_created_real_item_has_lp_condition(client)

def test_item_lists(client):
    test_logger.debug("starting tests for item lists")
    crud_item_lists(client)


def test_transactions(client):
    CRUD_transactions(client)
    normal_sequence(client)
    approved_transaction_items_should_not_be_updateable(client)


# def test_offers(client):
#     offers_filter_by_generic_item_id(client)


def test_crud_media(client):
    test_logger.debug("starting create/delete test for media")
    crud_media(client)


def test_conditions_on_real_items(client):
    test_logger.debug("integration test for real items + conditions")
    add_condition_to_real_item(client)
    read_conditions(client)


def test_multipliers(client):
    test_logger.debug("testing merchants condition multipliers")
    show_multipliers(client)

# def test_upload(client):
#     _upload(client)


