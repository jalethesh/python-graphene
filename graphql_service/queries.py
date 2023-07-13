import json
import os

import requests

from loggers import get_logger
from models.data_models import *
from security import user_is_logged_in
from flask import session
from sqlalchemy import func, or_, desc, asc,nullslast
from graphql_service.util import paginate
from .util import ShippoQuote

def get_offers(query, scryfall_card_id, generic_item_id):
    if scryfall_card_id:
        query = query.filter(Offers.scryfall_card_id == scryfall_card_id)
    if generic_item_id:
        query = query.filter(Offers.item_id == generic_item_id)
    query = query.order_by(desc(Offers.last_updated))
    return query.limit(1)


def get_latest_offers(query, scryfall_card_id, generic_item_id):
    if scryfall_card_id:
        query = query.filter(LatestOffers.scryfall_card_id == scryfall_card_id).order_by(desc(LatestOffers.last_updated))
    if generic_item_id:
        query = query.filter(LatestOffers.item_id == generic_item_id).order_by(desc(LatestOffers.last_updated))
    return query.limit(1)


search_logger = get_logger("search")


def get_generic_items(query, database_id, set_code, set_name, scryfall_card_id, item_index, partial_name, page, per_page):
    white_listed_sets = ['ced','cei'] #TODO: Hardcoded for now
    
    query = query.filter(or_(func.lower(GenericItems.games).contains('paper'), GenericItems.set.in_(white_listed_sets)))

    try:
        search_logger.debug(f"{session['user_id']} {partial_name}")
    except:
        search_logger.debug(f"{partial_name}")

    if isinstance(database_id, int):
        query = query.filter(GenericItems.id == database_id)
    elif isinstance(database_id, list):
        query = query.filter(GenericItems.id.in_(database_id))

    if scryfall_card_id:
        query = query.filter(GenericItems.scryfall_card_id == scryfall_card_id)
    if set_code:
        query = query.filter(GenericItems.set == set_code)
    if set_name:
        query = query.filter(GenericItems.set_name == set_name)
    if item_index:
        query = query.filter(GenericItems.set == item_index)
    if partial_name:
        pieces = partial_name.split(' ')
        for user_filter in pieces:
            query = query.filter(func.lower(GenericItems.item_hash).contains(user_filter.lower()),)

    return paginate(query, GenericItems.id, page, per_page)


def get_item_collections(query, user_id, name, trashed, collection_id, order_status, page, per_page):
    if user_id > 0:
        query = query.filter(ItemCollections.user_id == user_id)
    else:
        query = query.filter(ItemCollections.user_id == session["user_id"])
    if name:
        query = query.filter(ItemCollections.name == name)
    if trashed is not None:
        print("hitting trashed filter")
        query = query.filter(ItemCollections.trashed == trashed)
    if collection_id:
        query = query.filter(ItemCollections.database_id == collection_id)
    if order_status:
        query = query.filter(ItemCollections.order_status == order_status)

    return paginate(query, ItemCollections.database_id, page, per_page)


def get_item_lists(query, user_id, name, item_list_id, page, per_page):
    key = -ItemLists.database_id
    conditions = []
    if item_list_id:
        query = query.filter(ItemLists.database_id == item_list_id)
        return paginate(query, key, page, per_page)
    if user_id > 0:
        conditions.append(ItemLists.user_id == user_id)
    else:
        conditions.append(ItemLists.user_id == session["user_id"])
    if name:
        conditions.append(ItemLists.name == name)
    if 'roles' in session and 'administrator' in session['roles'] and session['username'] != 'ngoc-them-dev':
        conditions.append(ItemLists.database_id == 296)

    query = query.filter(or_(*conditions))
    return paginate(query, key, page, per_page)


def get_ranked_item_lists(query):
    item_lists = query.all()
    admins = db.session.query(Users).filter_by(security_role="admins").all()
    admin_ids = [x.database_id for x in admins]
    user_lists = [x for x in item_lists if x.user_id not in [admin_ids]]
    user_lists.sort(key=lambda x: -x.count)
    return user_lists


def unfiltered_get_real_items(query, real_item_id, collection_id, status, user_id, item_list_id, partial_name, sort_key,
                   sort_reverse, page, per_page):
    if real_item_id:
        query = query.filter(RealItems.database_id == real_item_id)
        return paginate(query, RealItems.database_id, page, per_page)
    if collection_id:
        query = query.filter(RealItems.item_collections_id == collection_id)
    if status:
        query = query.filter(RealItems.status == status)
    if user_id:
        query = query.filter(RealItems.owner == user_id)
    if item_list_id:
        query = query.filter(RealItems.item_list_id == item_list_id)
    if partial_name:
        pieces = partial_name.split(' ')
        for item_filter in pieces:
            query = query.filter(func.lower(RealItems.item_hash).contains(item_filter.lower()),)

    if sort_key == 'fmv':
        key = RealItems.fmv
    elif sort_key == 'item_hash':
        key = RealItems.item_hash
    else:
        key = RealItems.database_id
    return paginate(query, key, page, per_page, sort_reverse=sort_reverse)


def get_real_items(query, real_item_id, collection_id, status, user_id, item_list_id, partial_name, sort_key,
                   sort_reverse, page, per_page):
    if real_item_id:
        query = query.filter(RealItems.database_id == real_item_id)
        return paginate(query, RealItems.database_id, page, per_page)
    if collection_id:
        query = query.filter(RealItems.item_collections_id == collection_id)
    if status:
        query = query.filter(RealItems.status == status)
    if user_id:
        query = query.filter(RealItems.owner == user_id)
    elif 'user_id' in session:
        query = query.filter(RealItems.owner == session['user_id'])
    if item_list_id:
        query = query.filter(RealItems.item_list_id == item_list_id)
    if partial_name:
        pieces = partial_name.split(' ')
        for item_filter in pieces:
            query = query.filter(func.lower(RealItems.item_hash).contains(item_filter.lower()),)

    if sort_key == 'fmv':
        key = RealItems.fmv
    elif sort_key == 'item_hash':
        key = RealItems.item_hash
    else:
        key = RealItems.database_id
    if sort_reverse:
        key = -key
    return paginate(query, key, page, per_page)


def get_sets(query, set_code, partial_name, page, per_page):
    if set_code:
        query = query.filter(SetModel.code == set_code)
    if partial_name:
        query = query.filter(func.lower(SetModel.name).contains(partial_name.lower()))
    return paginate(query, SetModel.id, page, per_page)


@user_is_logged_in
def private_get_user(query, user_id):
    if user_id:
        query = query.filter(Users.database_id == user_id)
    elif 'user_id' in session:
        query = query.filter(Users.database_id == session["user_id"])
    return query.first()


def get_user(query, user_id):
    if user_id:
        query = query.filter(Users.database_id == user_id)
    elif 'user_id' in session:
        query = query.filter(Users.database_id == session["user_id"])
    else:
        raise Exception("no user specified")
    return query.first()


def get_activities(query, page, per_page):
    return paginate(query, Activities.database_id, page, per_page)


def get_subscriptions(query):
    return query.all()


def get_media(query, real_item_id, page, per_page):
    if real_item_id:
        query = query.filter(Media.realitem_id == real_item_id)
    return paginate(query, Media.database_id, page, per_page)


def get_defects(query, real_item_id, page, per_page):
    query = query.filter(Defects.real_item_id == real_item_id)
    return paginate(query, Defects.database_id, page, per_page)


def get_conditions(query):
    return query.all()


def get_transactions(query, transaction_id, user_id, status, status_array, sort_option, sort_mode, page, per_page):
    if transaction_id:
        query = query.filter(Transactions.database_id == transaction_id)
    if user_id:
        query = query.filter(or_(Transactions.left_owner == user_id, Transactions.right_owner == user_id))
    elif 'roles' in session and 'administrator' in session['roles']:
        pass
    elif 'user_id' in session:
        query = query.filter(or_(Transactions.left_owner == session['user_id'], Transactions.right_owner == session['user_id']))
    elif not transaction_id:
        raise Exception("no transaction set was specified")
    if status:
        query = query.filter(Transactions.status == status)
    if status_array:
        query = query.filter(Transactions.status.in_(status_array))
    key = Transactions.database_id
    mode = desc
    if sort_mode:
        if sort_mode == 'asc':
            mode = asc
        else:
            mode = desc
    if sort_option:
        # dateCreated, dateUpdated, rightCredit
        if sort_option == 'dateCreated':
            key = Transactions.date_created
        elif sort_option == 'dateUpdated':
            key = Transactions.date_updated
        elif sort_option == 'rightCredit':
            key = Transactions.right_credit
    return paginate(query, mode(key), page, per_page)


def get_transaction_items(query, transaction_id, page, per_page):
    if transaction_id:
        query = query.filter(TransactionItems.transaction_id == transaction_id)
    return paginate(query, -TransactionItems.trade_in_value, page, per_page)

def get_transaction_logs(query, transaction_id, page, per_page):
    if transaction_id:
        query = query.filter(TransactionLogs.transaction_id == transaction_id)
    return paginate(query, -TransactionLogs.database_id, page, per_page)
  
def get_merchant_condition_multipliers(query):
    return query.all()

def get_ebay_listing(query, database_id, has_prediction, winning_bid_sort, page, per_page):
    query = query.filter(EbayListing.title != None)

    if database_id:
        query = query.filter(EbayListing.database_id == database_id)
    
    if has_prediction:
        query = query.filter(or_(EbayListing.predicted_generic_id != None, EbayListing.predicted_generic_id_list!=None))
    
    if winning_bid_sort:
        query = query.order_by(nullslast(-EbayListing.winning_bid))

    return paginate(query, -EbayListing.database_id, page, per_page)

def get_listing_feedback(query, user_id, page, per_page):
    #query 
    if user_id:
        query = query.filter(ListingFeedback.user_id == user_id)
    return paginate(query, ListingFeedback.database_id, page, per_page)


def get_shippo_quotes(user):
    url = "https://api.goshippo.com/shipments/"
    test_token = os.getenv('SHIPPO_TOKEN')
    headers = {"Authorization": f"ShippoToken {test_token}", "Content-Type": "application/json"}

    content = {
        "address_from": {
            "name": f"{user.real_name}",
            "street1": f"{user.address_line_one}",
            "street2": f"{user.address_line_two}",
            "city": f"{user.address_city}",
            "state": f"{user.address_state}",
            "zip": f"{user.address_zipcode}",
            "country": f"{user.address_country}"
        },
        "address_to": {
            "name": "Ankur Pansari",
            "street1": "PMB #143 1459 18TH ST",
            "street2": "Purplemana",
            "city": "San Francisco",
            "state": "CA",
            "zip": "94107",
            "country": "USA"
        },
        "parcels": [{
            "length": "6",
            "width": "4",
            "height": "2",
            "distance_unit": "in",
            "weight": "2",
            "mass_unit": "oz"
        }],
        "extra": {
            "signature_confirmation": "ADULT"
        },
        "async": "false"
    }

    res = requests.post(url, data=json.dumps(content), headers=headers)
    data = json.loads(res.text)
    print(data.keys(), data['rates'][0].keys())
    quotes = []
    for item in data['rates']:
        details = item['servicelevel']
        print(item['amount'], item['estimated_days'], item['provider'], details['name'], details['token'])
        quote = ShippoQuote()
        quote.amount = item['amount']
        quote.estimated_days = item['estimated_days']
        quote.provider = item['provider']
        quote.name = details['name']
        quote.token = details['token']
        quotes.append(quote)
    return quotes