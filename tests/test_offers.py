# imports
from tests.graphql_example_requests.ex_offers import query_offers_by_generic_item
import json
from models.data_models import db, LatestOffersHistory
from flask import session
from tests.test_search import client

# filter offers by genericItemId
def offers_filter_by_generic_item_id(client):
    mutation = query_offers_by_generic_item
    variables = {"genericItemId": 211039}
    url = f'http://localhost:5000/graphql-api?query={mutation}&variables={json.dumps(variables)}'
    res = client.post(url)
    data = json.loads(res.data.decode('utf-8'))
    print(data)
    # check returned offer for correct itemId matching genericItemId
    returned_id = int(data['data']['offers'][0]['itemId'])
    assert returned_id == 211039
    # check returned offersHistory match the returned offer
    returned_scryfall_id = data['data']['offers'][0]['scryfallCardId']
    offers_history_scryfall_id = data['data']['offers'][0]['offersHistory']['edges'][0]['node']['scryfallCardId']
    assert returned_scryfall_id == offers_history_scryfall_id


from offers_factory import get_all_pm_offers, EditPmPrice
def test_modify_pm_prices(client):

    # Select a random generic_item:
    generic_item_index = 'TOR__Alter Reality'
    
    # Query the offer, the offer history, latest_offers and latest_offers_history
    results = get_all_pm_offers(generic_item_index)
    latest_offers = [ result.LatestOffers.__dict__ for result in results ]
            
    latest_offers_history = [ result.LatestOffersHistory.__dict__ for result in results ]
    for index, latest_offer_history in enumerate(latest_offers_history):
        if latest_offer_history['merchant'] == 'PM':
            latest_offers_history_id = latest_offer_history['database_id']
            latest_offers_id = latest_offers[index]['database_id']
            original_amount = latest_offer_history['amount']

            break
    
    #Modify the price to a test value
    submission_form = {
        'generic_item_index' : generic_item_index,
        'new_price' : 3.14,
        'latest_offers_id' : latest_offers_id,
        'latest_offers_history_id' : latest_offers_history_id
    }

    #submit form to /edit_pm_price 
    res = client.post('/edit_pm_price', data=submission_form)


    # Query the db if the price has been updated
    latest_offers_history =  db.session.query(LatestOffersHistory).\
        filter_by(offers_id=latest_offers_id, merchant='PM').order_by(LatestOffersHistory.last_updated.desc()).first()

    assert latest_offers_history.amount == 3.14

    # Return the price to original amount
    submission_form = {
        'generic_item_index' : generic_item_index,
        'new_price' : original_amount,
        'latest_offers_id' : latest_offers_id,
        'latest_offers_history_id' : latest_offers_history_id
    }

    #submit form to /edit_pm_price
    res = client.post('/edit_pm_price', data=submission_form)
    latest_offers_history =  db.session.query(LatestOffersHistory).\
        filter_by(offers_id=latest_offers_id, merchant='PM').order_by(LatestOffersHistory.last_updated.desc()).first()
    assert latest_offers_history.amount == original_amount    
    
    

