from items_factory import update_placeholder_items, update_generic_placeholder
from models.data_models import Users, SetModel, GenericItems, Offers, OffersHistory, Conditions, Merchants, Media, \
    Defects, MerchantsConditionMultiplier, LatestOffers, LatestOffersHistory
from ast import Assert
import sys, os
topdir = os.path.join(os.path.dirname(__file__), "..")
sys.path.append(topdir)
from app import create_app
from celery_service.tasks import *
from flask import g, session, url_for, template_rendered, request, Response, jsonify
from click.testing import CliRunner
import pytest
import ast
from loggers import get_logger
import csv


items_logger = get_logger("items")

@pytest.fixture
def client():
    app = create_app()
    app_context = app.test_request_context()
    app_context.push()

    @app.route('/session/userid/<ID>')
    def set_user_id(ID):
        celery_logger.debug("setting userid "+str(ID))
        session['user_id'] = int(ID)
        session['username'] = 'dylans-test-user'
        session['roles'] = ['guest']
        return jsonify({"message": "ID was set"})


    @app.route('/session/wordpressid/<ID>')
    def set_wordpress_id(ID):
        celery_logger.debug("setting wp id "+str(ID))
        session['ID'] = int(ID)
        return jsonify({"message": "ID was set"})

    @app.route('/session/roles/<role>')
    def set_roles(role):
        celery_logger.debug("setting roles "+role)
        session['roles'] = role
        return jsonify({"message": "role was set"})

    @app.route('/testing/users/logout')
    def logout():
        celery_logger.debug("logging out")
        session.clear()
        return jsonify({"message": "logged out"})

    with app.test_client() as client:
        yield client

def test_update_generic_placeholder(client):
    test_limits = [2] #Only one is really necessary

    for limit in test_limits:
        print(limit)
        for i in range(1,limit):
            generic_item_placeholder = db.session.query(GenericItems).filter_by(name='UPDATE ME').distinct(GenericItems.scryfall_card_id).first()
            generic_item_id_parameters = generic_item_placeholder.__dict__.copy()
            generic_item_id = generic_item_placeholder.id
            scryfall_id = generic_item_placeholder.scryfall_card_id

            # Get the card data to update with
            url = f'https://api.scryfall.com/cards/{scryfall_id}?format=json&pretty=true'
            card = requests.get(url).json()

            # Update the generic item with the card data
            ret_val = update_generic_placeholder(generic_item_placeholder, card)
            if ret_val is False:
                # This is assuming that there was a present GenericItem collsion with the same item_index
                # Make sure that this is indeed the case
                matches = db.session.query(GenericItems.id).filter_by(scryfall_card_id=scryfall_id).count()
                if matches >= 2:
                    #This is a collision
                    # No item was updated here so we should just continue the loop
                    continue 
                else: 
                    # This is an error apart from a collision
                    assert ret_val
        
            #Query again using the generic_item_id
            generic_item_placeholder = db.session.query(GenericItems).filter_by(id=generic_item_id).one()
            new_generic_parameters = generic_item_placeholder.__dict__

            difference_count = 0
            #Compare the new parameters with the old parameters
            for key in generic_item_id_parameters:
                if generic_item_id_parameters[key] != new_generic_parameters[key]:
                    difference_count += 1

            print(f"Parameters changed during updated: {difference_count} for {generic_item_placeholder.name}")
            assert difference_count >= 55 #Arbitrary number, but should more than 55-ish
            
            # Assert these columns are not null
            ess_columns = ['legalities','games','image_uris','oracle_id','name',
                'foil','nonfoil','lang','uri','oracle_text',
                'artist','collector_number','promo','set','set_name','set_type',
                'item_index','original_name',]

            # Assert that the columns are of the correct type from GenericItems
            for column in ess_columns:
                assert type(generic_item_placeholder.__dict__[column]) == GenericItems.__dict__[column].expression.type.python_type

            # Assert that each uri in image_uris will return a 200 status code.
            image_dict = ast.literal_eval(new_generic_parameters['image_uris'])
            for size, url in image_dict.items():
                if url:
                    r = requests.head(url)
                    assert r.status_code == 200
            items_logger.debug(f"Item: {generic_item_placeholder.name} | Updated Parameters: {difference_count}")
    
def test_update_generic_items():
    limit = 2
    runner = CliRunner()
    result = runner.invoke(update_placeholder_items, ['--limit',limit, '--csv_path', 'logs/generic_item.csv', '-s', 'klr', '-s', 'lea', '-s', 'cei'])
    assert result.exit_code == 0
    assert f'Finished updating {limit} items' in result.output

def test_write_updates_to_csv():
    limit = 2
    runner = CliRunner()
    result = runner.invoke(update_placeholder_items, ['--limit', limit, '--csv_path', 'logs/generic_item.csv'])
    assert result.exit_code == 0
    
    ## ASSERTIONS
    #Assert the header columns of the csv file has _old and _new appended to the end
    affixes = ['_new','_old']
    for affix in affixes:
        comparator = []
        with open(f'logs/generic_item{affix}.csv', 'r') as f:
            reader = csv.reader(f)

            # Just Checking if the columns are of the same name
            gen_item_cols = [col.name for col in GenericItems.__table__.columns]
            headers = next(reader)

            #Assert that the gen_item_cols and headers have the same length
            assert len(gen_item_cols) == len(headers)

#Have pytest skip this test
@pytest.mark.skip(reason="This test will take long")                    
def test_update_generic_items_all():
    limit = 1000
    runner = CliRunner()
    result = runner.invoke(update_placeholder_items, ['--limit',limit])
    assert result.exit_code == 0
