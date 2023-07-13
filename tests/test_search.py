import click
from click.testing import CliRunner
import os 
import sys
import pytest
topdir = os.path.join(os.path.dirname(__file__), "..")
sys.path.append(topdir)
from app import create_app
sys.path.append('search/')
from search.fuzz_search_cli import main
from flask import session, url_for, template_rendered, request, Response
from loggers import fuzzy_search_logger
import re
from flask import jsonify
from .util import set_user_to_customer
from search_factory import import_ebay_listing, predict_ebay_listing, predict_ebay_listing_multi, get_status_code
from models.data_models import db, EbayListing, ListingFeedback 
from contextlib import contextmanager
from click.testing import CliRunner
import multiprocessing
import math
import re
from .util import set_user_to_admin, set_user_to_customer, extract_value_from_b64, test_logger
from tests.graphql_example_requests.ex_listings import *
from tests.graphql_example_requests.ex_genericItems import *


search_logger = fuzzy_search_logger
GRAPHQL_URL = "http://localhost:5000/graphql"

def test_search_cli():
    runner = CliRunner()
    inputs = '\n'.join(['x4 Dragons Rage Channeler - MTG English 121/303 MH2 Uncommon'])
    result = runner.invoke(main, input=inputs)
    assert result.exit_code == 0
    result = result.stdout_bytes.decode('utf-8')

    #Find the string that has 'MATCHED CARD ID'
    card_id = int(re.findall("MATCHED CARD ID: (\d+)",result)[0])
    card_name = re.findall('MATCHED CARD NAME: "(.+)"',result)[0]
    
    assert card_id == 778597
    assert card_name == "Dragon's Rage Channeler [Foil] [121]"


def test_search_cli_multi():
    runner = CliRunner()
    inputs = ["--input", "Meditate Tempest NM Blue Rare MAGIC THE GATHERING MTG CARD",'--multi','3']
    joined_inputs = '\n'.join(inputs)
    result = runner.invoke(main, args=inputs)
    assert result.exit_code == 0
    result = result.stdout_bytes.decode('utf-8')

    #Find the string that has 'MATCHED CARD ID'
    card_ids = re.findall("MATCHED CARD ID: (\d+)",result)
    card_names = re.findall('MATCHED CARD NAME: "(.+)"',result)
    
    assert '212133' in card_ids
    assert '295804' in card_ids
    assert "Circle of Protection: Blue" in card_names
    assert "Meditate" in card_names


@pytest.fixture
def client():
    app = create_app()
    app_context = app.test_request_context()
    app_context.push()

    @app.route('/session/userid/<ID>')
    def set_user_id(ID):
        search_logger.debug("setting userid "+str(ID))
        session['user_id'] = int(ID)
        session['username'] = 'dylans-test-user'
        session['roles'] = ['guest']
        return jsonify({"message": "ID was set"})

    @app.route('/session/wordpressid/<ID>')
    def set_wordpress_id(ID):
        search_logger.debug("setting wp id "+str(ID))
        session['ID'] = int(ID)
        return jsonify({"message": "ID was set"})

    @app.route('/session/roles/<role>')
    def set_roles(role):
        search_logger.debug("setting roles "+role)
        session['roles'] = role
        return jsonify({"message": "role was set"})

    @app.route('/testing/users/logout')
    def logout():
        search_logger.debug("logging out")
        session.clear()
        return jsonify({"message": "logged out"})

    with app.test_client() as client:
        # with app.app_context():
        #     init_db()
        yield client


# Returns both a app context instance and a cli runner instance    
@pytest.fixture
def cli_client():
    app = create_app()
    app_context = app.test_request_context()
    app_context.push()
    with app.test_client() as client:
        yield CliRunner(), client


def test_search_query(client):
    # Inside app context
    input =  'x4 Dragons Rage Channeler - MTG English 121/303 MH2 Uncommon'
    #make get request to search_query
    #check if the response is 200   
    #data = client.get(url_for('search_query', search_query=input))
    data = client.get('/search_query', query_string={'search_query': input})
    assert data.status_code == 200
    assert data.get_json()['id'] == '778597'


def test_predict_ebay_listing(cli_client):
    number=3
    #Run one prediction on a listing
    result = cli_client[0].invoke(predict_ebay_listing ,['--number', str(number)])
    #Parse the result.output
    print(f'Result Output: {result.output}')
    predicted_ids = re.findall('Predicted result id: (\d+)', result.output)
    listing_ids = re.findall('Modified listing ID: (\d+)', result.output)
    assert len(predicted_ids) == number
    
    query = db.session.query(EbayListing.predicted_generic_id).filter(EbayListing.database_id.in_(listing_ids)).all()   
    stored_predicted_ids = [int(x[0]) for x in query]    #Check if the ebay_listing has been updated with the 
    assert stored_predicted_ids.sort() == list(map(int, predicted_ids)).sort()


def test_predict_ebay_listing_multi(cli_client):

    number=6
    num_processors = 10
    result = cli_client[0].invoke(predict_ebay_listing_multi ,['--number', str(number),'-p',str(num_processors),'-m','5'])
    listing_ids = re.findall('Modified listing ID: (\d+)', result.output)
    predicted_ids = re.findall('Predicted result id: (\d+)', result.output)
    # assert len(listing_ids) == int(num_processors*math.ceil(number/num_processors)) \
    #     == int(num_processors*math.ceil(number/num_processors))
     # Check if the ebay_listing has been updated with the new predicted_generic_id
    query = db.session.query(EbayListing.predicted_generic_id).filter(EbayListing.database_id.in_(listing_ids)).all()   
    stored_predicted_ids = [int(x[0]) for x in query]

    assert stored_predicted_ids.sort() == list(map(int, predicted_ids)).sort()


@contextmanager
def get_context_variables(app):
    recorded = []

    def record(sender, template, context, **extra):
        recorded.append(context)
    template_rendered.connect(record, app)
    try:
        yield iter(recorded)
    finally:
        template_rendered.disconnect(record, app)


def logout_user(client):
    client.get("http://localhost:5000/testing/users/logout")


def test_for_validation(client):
    set_user_to_customer(client)
    response = client.get(url_for('search.for_validation'))
    assert response.status_code == 200
    # Write a regex finall to find the string after "MATCH CARD ID"
    images = re.findall('(?:img src=).*', response.data.decode('utf-8'))
    urls = [x.split('=')[1].strip('"').replace('"','').strip() for x in images]

    # Check if the images are valid
    pool = multiprocessing.Pool(processes=5)
    result = pool.map(get_status_code, urls)
    pool.close()
    assert any(200 == x for x in result) # Photo found


class ValidateListingTest:
    def __init__(self, listing_id, generic_id, comment):
        self.listing_id = listing_id
        self.generics_id = generic_id
        self.comment = comment

def test_validate_listing(client):
    test_validate_params= [
    {'listing_id': 13834, 'generic_id': 273264, 'comment': 'This is a Match Test Comment', 'is_match':True},
    {'listing_id': 13834, 'generic_id': None, 'comment': 'This is a Wrong Test Comment', 'is_match':False}
    ]

    for test_param in test_validate_params:
        #Unpack testing parameters
        test_listing_id = test_param['listing_id']
        test_generic_id = test_param['generic_id']
        test_comment = test_param ['comment']
        test_is_match = test_param['is_match']

        set_user_to_customer(client)
        response = client.post(url_for('search.validate_listing'), 
            data={'listing_id': test_listing_id, 
                'user_selected_generic_id': test_generic_id,
                'user_comment': test_comment,
                'is_match': test_is_match})

        #Query the database for all comments for the listing
        feedback = db.session.query(ListingFeedback).filter(
            ListingFeedback.listing_id == test_listing_id,
            ListingFeedback.user_id == 10,
            ListingFeedback.user_selected_generic_id == test_generic_id,
            ListingFeedback.user_comment == test_comment).all()

        if len(feedback) == 0 and test_generic_id != None:
            raise AssertionError(f'No feedback found for listing {test_listing_id}')
        
        if test_generic_id == None and len(feedback) >= 1:
            raise AssertionError(f'Predicted Generic ID found for listing {test_listing_id} but was intentionally set to None')
        
        #Double check that the user_approval column has been updated
        listing = db.session.query(EbayListing).filter(EbayListing.database_id == test_listing_id).first()
        assert listing.user_approved == 1


GRAPHQL_URL = "http://localhost:5000/graphql-api"

def test_ebay_listing_query(client):
    set_user_to_customer(client) #Setup
    response = client.post(GRAPHQL_URL, json={'query': query_ebay_listing})
    response_body = response.json
    assert response.status_code == 200
    assert len(response_body['data']['ebayListing']) >= 100
    assert response_body['data']['ebayListing'][0]['winningBid'] is not None or ""
    assert list(response.json['data']['ebayListing'][0].keys()) ==  ['title', 'winningBid', 'predictedGenericId', 'databaseId']


def test_listing_feedback_query(client):
    set_user_to_customer(client) #Setup
    response = client.post(GRAPHQL_URL, json={'query': query_listing_feedback})
    assert response.status_code == 200
    assert list(response.json['data']['listingFeedback'][0].keys()) == ['userId', 'userComment', 'dateCreated']
    
def test_update_listing_feedback_mutation(client):
    set_user_to_customer(client)
    response = client.post(GRAPHQL_URL, json={'query': mutation_update_listing_feedback})
    assert response.status_code == 200
    assert response.json['data']['createUpdateListingFeedback']['ok'] == True
    feedback_id = int(re.findall(r'\d+', response.json['data']['createUpdateListingFeedback']['debug'])[0])
    
    #Check if the entry exists
    listing_feedback = db.session.query(ListingFeedback).filter(ListingFeedback.database_id == feedback_id).first()
    assert listing_feedback.as_dict()['user_comment'] == 'General Kenobi wrote this comment'
    #Assert that this entry was made between now and and the last 30minutes
    # datetime
    # assert listing_feedback.date_created >= datetime.datetime.now() - datetime.timedelta(hours=48)
    # assert listing_feedback.date_created <= datetime.datetime.now()

def test_ebay_listing_with_id_query(client):
    set_user_to_customer(client) #Setup
    response = client.post(GRAPHQL_URL, json={'query': query_listing_feedback_id})
    assert response.status_code == 200
    assert len(response.json['data']['ebayListing']) == 1
    assert response.json['data']['ebayListing'][0]['predictedGenericId'] is not None or ""
    assert response.json['data']['ebayListing'][0]['predictedGenericId'] == 219471
    assert list(response.json['data']['ebayListing'][0].keys()) ==  ['title', 'winningBid', 'predictedGenericId', 'databaseId']

def test_generic_items_with_id_query(client):
    set_user_to_customer(client) #Setup
    response = client.post(GRAPHQL_URL, json={'query': query_generic_items_with_id})
    assert response.status_code == 200
    assert len(response.json['data']['genericItems']) == 1
    assert response.json['data']['genericItems'][0]['id'] == 'R2VuZXJpY0l0ZW1PYmplY3Q6MTA0ODM2OQ=='
    assert list(response.json['data']['genericItems'][0].keys()) ==  ['id', 'name', 'scryfallCardId']

def test_generic_items_with_no_id_query(client):
    set_user_to_customer(client) #Setup
    response = client.post(GRAPHQL_URL, json={'query': query_genericItems_1})
    assert response.status_code == 200
    assert len(response.json['data']['genericItems']) >= 20
    assert list(response.json['data']['genericItems'][0].keys()) ==  ['id', 'imageUriPng', 'itemIndex']

def test_generic_items_with_id_list_query(client):
    set_user_to_customer(client) #Setup
    response = client.post(GRAPHQL_URL, json={'query': query_generic_items_with_id_list})
    assert response.status_code == 200
    assert len(response.json['data']['genericItems']) == 3
    assert list(response.json['data']['genericItems'][0].keys()) ==  ['id', 'name','scryfallCardId', 'itemIndex']

def test_import_ebay_listing(cli_client):
    csv_file = ['--csv_file','search/datasets/ebay_listing_part_2.xlsx']
    result = cli_client[0].invoke(import_ebay_listing ,['--csv_file','search/datasets/ebay_listing_part_2.xlsx'])

    assert result.exit_code == 0

def test_ebay_listing_query_with_sort(client):
    set_user_to_customer(client) #Setup
    response = client.post(GRAPHQL_URL, json={'query': query_ebay_listing_ex_1})
    assert response.status_code == 200
    assert sorted(list(response.json['data']['ebayListing'][0].keys())) ==  sorted(['predictedGenericId','title', 'predictedGenericIdList','winningBid'])

    #assert that none of them are None
    for listing in response.json['data']['ebayListing']:
        assert listing['predictedGenericId'] is not None or ""
        assert listing['winningBid'] is not None or ""


