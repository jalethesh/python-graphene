import celery
from numpy import generic
import requests
from items_factory import highest_card
from models.data_models import db, ItemCollections, RealItems
from models.data_models import GenericItems, Offers, OffersHistory, Conditions, CollectionHistory, \
    MerchantsConditionMultiplier, LatestOffers, LatestOffersHistory
import os
from datetime import datetime
from collections import defaultdict
from sqlalchemy import desc, tuple_
import time
import json
from loggers import get_logger
from sqlalchemy.sql import ClauseElement   
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from sqlalchemy import exc
import pickle
celery_logger = get_logger("celery")
celery_logger.debug(f"creating tasks level logger with name celery")


def process_set(mtg_set):
    print("processing", mtg_set)
    print("updating mtgset")
    update_mtgban(mtg_set)
    print("completed mtgset update")
    return mtg_set

def time_string():
    now = datetime.now()
    return now.strftime("%d/%m/%Y %H:%M:%S")

def get_one_or_create(model, create_method='', 
    create_method_kwargs=None, create_flag=False, **kwargs):
    toc = time.time()
    try:
        if create_flag: #dont query, just create
            raise NoResultFound

        (instance, ) = db.session.query(model).filter_by(**kwargs).one(),
        celery_logger.debug(f"{model.__tablename__} entry was found")
        
        # Returns the first result and False because no entry was created
        return instance, False
    
    except NoResultFound:
        celery_logger.debug(f"{model.__tablename__} Warning: Errored out NoResultFound. Time: {time.time()-toc:2f}")
        # Create a new entry
        kwargs.update(create_method_kwargs or {})
        created = getattr(model, create_method, model)(**kwargs)
        
        try:
            db.session.add(created)
            db.session.commit()
            #Return the new entry and True because an entry was created
            celery_logger.debug(f"{model.__tablename__} entry created")
            return created, True
        
        except exc.IntegrityError as e:
            # Return the best-match entry (Most likely None) and False becasue no entry was created
            db.session.rollback()
            celery_logger.debug(f"ERROR: {model.__tablename__} could not be created. {e}")
            return db.session.query(model).filter_by(**kwargs).one_or_none(), False

    except MultipleResultsFound as e:
        celery_logger.debug(f"{model.__tablename__} Warning: Errored out MultipleResultFound. Returning first result: {e}")
        
        if model == GenericItems:
            return db.session.query(model).filter_by(**kwargs).filter(model.name!="UPDATE ME").first(), False
        else:
            #TODO model.last_updated is hardcoded | and not universal
            res = db.session.query(model).filter_by(**kwargs).order_by(model.last_updated.desc()).first()
            
            return res, False
        
    except Exception as e:
        celery_logger.debug(f"{model.__tablename__} ERROR: {str(e)[:120]}")
        return None, False

    finally:
        tic = time.time()


def create_offer(scryfall_id, fetched_item):
    # Add new offer to the database
    try:
        offers = Offers(scryfall_card_id=scryfall_id, 
                        item_index=fetched_item.item_index,
                        last_updated=datetime.now(), 
                        item=fetched_item, 
                        condition='NM')
        db.session.add(offers)
        db.session.commit()
        celery_logger.debug(f"created offer for {fetched_item}")
        return offers

    except Exception as ex:
        db.session.rollback()
        now = time_string()
        print(f"{now} Error inserting offer on: {str(ex)[:120]}")
        celery_logger.debug((f"{now} Error inserting offer on: {str(ex)[:120]}"))
        return None


def get_latest_offer(scryfall_id, fetched_item):
    # search for latest offer (if exists) and update, otherwise create new latestOffer
    # each generic item has the foil / non foil information, but we also need to specify condition
    try:
        latest_offer_matches = db.session.query(LatestOffers).filter_by(item_id=fetched_item.id, condition='NM').all()
        if len(latest_offer_matches) == 0:
            latest_offer = LatestOffers(scryfall_card_id=scryfall_id, item_index=fetched_item.item_index,
                                        last_updated= datetime.now(), item=fetched_item, condition='NM')
            celery_logger.debug(f"Created latest offer for {fetched_item}")
        elif len(latest_offer_matches) > 1:
            celery_logger.debug(f"multiple latest offers found for {fetched_item}. Using the first one")
            print(f"Error found multiple latest offer matches for {fetched_item.id}")
            latest_offer = latest_offer_matches[0]
        else: #Else only one is found
            latest_offer = latest_offer_matches[0]
            latest_offer.last_updated =  datetime.now()
        db.session.add(latest_offer)
        db.session.commit()
        return latest_offer

    except Exception as ex:
        db.session.rollback()
        now = time_string()
        print(f"{now} Error inserting or getting latest offers on: {str(ex)[:120]}")
        return None

def transpose(self, dct):
    d = defaultdict(dict)
    for key1, inner in dct.items():
        for key2, value in inner.items():
            d[key2][key1] = value
    return d

class BuyList():
    # Takes in a json response object and builds the dictionary with it.

    # To filter out 
    def __init__(self, mtg_set, testing=False, limit=None) -> None:
        self.limit = limit
        self.buy_dict = self.get_buylist(mtg_set, testing=testing)
        self.get_scryfall_ids()
        self.MTGBAN_SIG = os.getenv("MTGBAN_SIG")
        if self.MTGBAN_SIG is None:
            celery_logger.debug('MTGBAN_SIG not set')
        self.mtg_set = mtg_set
        self.pm_count = 0
        
    def get_offers(self):
        return self.transpose(self.buy_dict)
    
    def transpose(self, dct):
        d = defaultdict(dict)
        for key1, inner in dct.items():
            for key2, value in inner.items():
                d[key2][key1] = value
        return d

    def get_buylist(self, mtg_set, testing=False):
        # Function to get the buylists from MTGBAN API using a mtg_set query
        now = time_string()
        celery_logger.debug(f"Starting get_buylist for {mtg_set}")
        MTGBAN_SIG = os.getenv("MTGBAN_SIG")
        if MTGBAN_SIG is None:
            celery_logger.debug('ERROR: MTGBAN_SIG not set')
        mtgban_buylist_url = f"https://www.mtgban.com/api/mtgban/buylist/{mtg_set}.json?sig="
        constructed_url = mtgban_buylist_url + MTGBAN_SIG + "&id=scryfall"
        print(mtg_set, constructed_url)

        if testing:
            #Try loading 'tests/ced_buy_list.pkl'
            try:
                with open(f'tests/{mtg_set}_buy_list.pkl', 'rb') as f:
                    buy_list = pickle.load(f)
                    celery_logger.debug("CED Buylist loaded")
            except Exception:
                buy_list = {
                    'testing-scryfall-id': {
                        'PM': {
                            'regular': 0.5
                        },
                    }
                }
                celery_logger.debug("Loading Backup test buy_list")

        else:
            try:
                r = requests.get(constructed_url)
                if r.status_code == 200:
                    buy_list = r.json()['buylist']
                    print("Buylist items total count: " + str(len(buy_list)))
                else:
                    print(f"ERROR: in getting buylist for {mtg_set}")
                    celery_logger.debug(f"ERROR: in getting buylist for {mtg_set}")
                    return None
            except Exception as ex:
                print(f"ERROR: in retreiving buy list from {constructed_url}:" +str(ex))
                celery_logger.debug(f"Error in retreiving buy list from {constructed_url}:" +str(ex))
                return None

            if self.limit is not None and isinstance(self.limit, int):
                # Limit the number of items in the buy list
                buy_list = dict(list(buy_list.items())[:self.limit])
                celery_logger.debug(f"Buylist items limited to: {str(len(buy_list))}")

        
        #nm_condition_object = Conditions.query.filter_by(us_code="NM").first()
        #print(f"nm_condition_object: {nm_condition_object}")
        return buy_list

    def get_scryfall_ids(self):
        # Returns the scryfall IDs for buy_list
        self.scryfall_ids = list(self.buy_dict.keys())
        return self.scryfall_ids

    def get_offers(self, scryfall_id):
        # Returns the offers for buy_list
        # Offers are returned as a dictionary of {Foil_type: {Merchant_id: {offer_amount} }}
        return self.transpose(self.buy_dict[scryfall_id])

    def get_foil_types(self, scryfall_id):
        # Returns the foil types for a particular scryfall_id
        return self.get_offers(scryfall_id).keys()
    
    def get_merchants(self, scryfall_id, foil_type=None):
        # Returns the merchants for a particular scryfall_id and foil_type
        # If foil_type is not specified, returns all merchants for the scryfall_id
        if foil_type is None:
            merchant_set = set()
            for foil_type in self.get_foil_types(scryfall_id):
                merchant_set.update(self.get_offers(scryfall_id)[foil_type].keys())
            return list(merchant_set)

        return self.get_offers(scryfall_id)[foil_type].keys()

    @staticmethod
    def is_foil(regular_or_foil):
        # Takes in a string value and is expecting either
        # regular or foil
        if regular_or_foil == "regular":
            return False
        elif regular_or_foil == 'foil':
            return True
        else:
            return False
    
    def get_offer_amount(self, scryfall_id, foil_type, merchant):
        # Returns the highest offer for a particular scryfall_id, foil_type, and merchant
        return self.get_offers(scryfall_id)[foil_type][merchant]

    def update_mtgset(self):
        now = datetime.now()
        celery_logger.debug("Begin update MTGban")
        success_flag = True
        scryfall_id_count = 0
        if self.buy_dict is None:
             # Was not able to get the buy list from mtgban
            print("Buy list was not able to be retrieved from mtgban")
            celery_logger.debug("ERROR: Buy list was not able to be retrieved from mtgban")
            return False
        
        for scryfall_id in self.scryfall_ids:
            ret_val = self.update_by_scryfall_id(scryfall_id, now)
            if ret_val is False:
                celery_logger.debug(f"ERROR updating {scryfall_id}")
                success_flag = False
                continue
            else:
                scryfall_id_count += 1
        
        if success_flag:
            celery_logger.debug(f"Succesfully updated ALL entries under: {scryfall_id} | Acc PM Entries: {self.pm_count}")
        else:
            celery_logger.debug(f"Successfully updated {scryfall_id_count} under {scryfall_id} | Failed: {len(self.scryfall_ids)-scryfall_id_count} | Acc PM Entries: {self.pm_count}")
        return True

    def update_by_scryfall_id(self, scryfall_id, now=datetime.now()):
        offer = self.get_offers(scryfall_id)
        celery_logger.debug(f"Iterating over ID {scryfall_id} in offers: {offer}")
        
        for foil_type in offer.keys():
            self.highest_offer = 0 #Reset each loop of each new card and of each foil_type
            celery_logger.debug(f"Iterating over foil_type:{foil_type} in offers: {offer}")
            is_foil = self.is_foil(foil_type)

            #Get or Create a Generic item if not found
            generic_item, ret_val = get_one_or_create(GenericItems,
                scryfall_card_id = scryfall_id, 
                foil = is_foil,
                nonfoil = not(is_foil), 
                create_method_kwargs = {
                    'item_index': scryfall_id+'foilflag_'+str(is_foil),
                    'name': "UPDATE ME",
                    'set': self.mtg_set.lower(), 
                    'scryfall_set_id':"1234567890"
                })

            #Specific Debug logging
            if ret_val:
                celery_logger.debug(f"Create new Generic Item Entry {generic_item}") 
            elif not ret_val and generic_item is None:
                celery_logger.debug(f"ERROR: Generic Item Entry {generic_item} was not found and not created")
            elif not ret_val and generic_item is not None:
                celery_logger.debug(f"Generic Item Entry {generic_item} was found")
            
            if generic_item is None:
                celery_logger.debug("ERROR. Generic Item not found")
                return False #EARLY EXIT

            my_offer = create_offer(scryfall_id, generic_item)
            if my_offer is None:
                celery_logger.debug(f"ERROR creating offer for {scryfall_id}")
                db.session.flush()
                continue
  
            # Retrieve the latest offer based on the generic_item and current scryfall_card_id
            latest_offer, ret_val = get_one_or_create(LatestOffers, 
                item_id=generic_item.id, condition='NM',
                create_method_kwargs={
                'scryfall_card_id':scryfall_id, 
                'item_index':generic_item.item_index,
                'last_updated': now,
                'item':generic_item
                })

            if ret_val is False and latest_offer is not None:
                #Update the latest_offer
                latest_offer.last_updated = now
                db.session.commit()

            elif latest_offer is None:
                celery_logger.debug(f"ERROR getting latest offer for {scryfall_id} Skipping {foil_type} in offer {offer}")
                continue
                
            ## Update the offer
            for merchant in self.get_merchants(scryfall_id, foil_type):
                ## Prepare offer parameters
                offer_amount = self.get_offer_amount(scryfall_id, foil_type, merchant)
                rounded_offer = round(offer_amount, 2)

                ## Merchant Specific Condtiions
                # Omit these merchants
                omit_merchants = ['HA', 'TCGMkt', 'CS']
                include_merchants = ['SCG', 'ABU', 'CK', 'CSI', 'MS']

                # for AB we will reduce their offer due to price inflation
                if merchant == 'ABU':
                    matching_offer = 0.8*rounded_offer
                else:
                    matching_offer = rounded_offer

                if matching_offer > self.highest_offer and merchant in include_merchants:
                    self.highest_offer = matching_offer

                # Update the tables with the parameters
                ret_val = self.update_by_merchant(merchant, scryfall_id, foil_type, rounded_offer, 
                    my_offer, latest_offer, generic_item, now=now)
            
            ret_val = self.update_pm_offers(scryfall_id, foil_type, my_offer, latest_offer, generic_item, now=now)
            celery_logger.debug(f"Successfully updated scryfall_id: {scryfall_id} with types {foil_type} | PM Entries made/updated{self.pm_count}")
        
        return True

    def update_pm_offers(self, scryfall_id: int, foil_type: str, my_offer: Offers, 
            latest_offer: LatestOffers, generic_item: GenericItems, now=datetime.now()):
        
        merchant = "PM"
        source = "Purplemana"
        try:
            #Create a new PM offer_history                 
            offers_history, ret_val = get_one_or_create(OffersHistory,
                    scryfall_card_id=scryfall_id, 
                    last_updated = now, 
                    offers=my_offer,
                    card_type=foil_type,
                    condition="NM", 
                    source=source,
                    merchant=merchant, 
                    amount=self.highest_offer,
                    create_flag=True
                    )
            if ret_val is False and offers_history is not None:
                celery_logger.debug(f"WARNING Unintended behavior caught in PM OffersHistory.  \
                    Present Offer history \n MERCHANT: {merchant} \n SOURCE:{source} \n SCRY_ID: {scryfall_id} \n was found.")
            elif ret_val is False and offers_history is None:
                celery_logger.debug(f"ERROR Unable to insert PM offerHistory for \
                    ID:{scryfall_id} | Merchant:{merchant} | offer={self.highest_offer}")
            elif ret_val is True:
                celery_logger.debug(f"Inserted PM offers_history for ID:{scryfall_id} | Merchant:{merchant} | Offer:{self.highest_offer}")

            # Create a PM listing in LatestOffersHistory
            latest_offer_history, ret_val = get_one_or_create(LatestOffersHistory, 
                offers_id=latest_offer.database_id, 
                merchant=merchant,
                source=source,
                create_method_kwargs= {
                    'scryfall_card_id':scryfall_id,
                    'last_updated':now,
                    'amount': self.highest_offer,
                    'card_type': foil_type,
                    'condition':"NM"},
                )

            if ret_val is False and latest_offer_history is not None: #Entry was found. Update the latestOfferHistory
                latest_offer_history.last_updated = now
                latest_offer_history.amount = self.highest_offer
           
            
            db.session.add(latest_offer_history)
            db.session.commit()
            celery_logger.debug(f"Inserting PM LatestOfferHistory for Merchant:{merchant} | Offer:{self.highest_offer} for ID:{scryfall_id} on Generic item_index: {generic_item.item_index}")
            
        except Exception as ex:
            db.session.rollback()
            now = time_string()
            celery_logger.debug(f"ERROR inserting {merchant} offers history", ex)
            print(f"Some Error inserting PM offers history", ex)
            return False
        
        celery_logger.debug(f"Successfully updated PM offers and OffersHistories for {scryfall_id} | {latest_offer.database_id}")
        return True

    def update_by_merchant(self, merchant: str, scryfall_id: int, foil_type: str, rounded_offer: float, 
        my_offer: Offers, latest_offer: LatestOffers, generic_item: GenericItems, now=datetime.now()):
        
        celery_logger.debug(f"Iterating over Merchant: {merchant}")                
        # Create the OffersHistory & LatestOffersHistory row for each merchant
        source = 'MTGBAN'
        try:
            #Check if the offer_history is there, if not, insert a new one.                
            offers_history, ret_val = get_one_or_create(OffersHistory,
                    scryfall_card_id=scryfall_id, 
                    last_updated = now, 
                    offers=my_offer,
                    card_type=foil_type,
                    condition="NM", 
                    source=source,
                    merchant=merchant, #Changes
                    amount=rounded_offer, #Changes
                    create_flag=True
                    )
            if ret_val is False and offers_history is not None:
                celery_logger.debug(f"WARNING Unintended behavior caught in OffersHistory.  \
                    Present Offer history \n MERCHANT: {merchant} \n SOURCE:{source} \n SCRY_ID: {scryfall_id} \n was found.")
            elif ret_val is False and offers_history is None:
                celery_logger.debug(f"ERROR Unable to insert offerHistory for \
                    ID:{scryfall_id} | Merchant:{merchant} | offer={rounded_offer}")
            elif ret_val is True:
                celery_logger.debug(f"Inserted offers_history for ID:{scryfall_id} | Merchant:{merchant} | Offer:{rounded_offer}")

            # pull the latestOffersHistory related to the latestOffer, or create a new one if none are found
            # foil vs non foil is informing the card_type, which should be handled with the generic item ref
            latest_offer_history, ret_val = get_one_or_create(LatestOffersHistory, 
                offers_id=latest_offer.database_id, 
                merchant=merchant,
                create_method_kwargs= {
                    'scryfall_card_id':scryfall_id,
                    'last_updated':now,
                    'amount': rounded_offer, 'card_type': foil_type,
                    'condition':"NM", 'source':"MTGBAN"}
                )

            if ret_val is False: #Entry was found. Update the latestOfferHistory
                latest_offer_history.last_updated = now
                latest_offer_history.amount = rounded_offer
            
            db.session.add(latest_offer_history)
            db.session.commit()
            celery_logger.debug(f"Inserting LatestOfferHistory for Merchant:{merchant} | Offer:{latest_offer_history.amount} for ID:{scryfall_id} on LastestOfferID:{latest_offer.database_id}")
            celery_logger.debug("------------------------------------------")
            celery_logger.debug(f"Generic item_index: {generic_item.item_index} Highest Offer: {rounded_offer}")
            
        except Exception as ex:
            db.session.rollback()
            now = time_string()
            celery_logger.debug(f"ERROR: Some error inserting {merchant} offers history", ex)
            print(f"Some Error inserting PM offers history", ex)
            return False
        
        celery_logger.debug(f"Successfully updated offers and OffersHistories for {scryfall_id} | {latest_offer.database_id} | {merchant}")
        return True

def update_mtgban(mtg_set, testing=False, limit=None):
    celery_logger.debug(f"Beginning update_mtgban; Test:{testing}")

    try:
        buy_list = BuyList(mtg_set=mtg_set, testing=testing, limit=limit)
        ret_val = buy_list.update_mtgset()
        if ret_val:
            celery_logger.debug(f"Successfully updated mtgban for {mtg_set}")
            return True
        else:
            return False
    except Exception as e:
        celery_logger.debug(f"Error updating mtgban for {mtg_set}: {e}")
        return False 

def check_generic_items():
    start = time.time()
    generic_items = db.session.query(GenericItems).filter(GenericItems.foil == None)\
        .filter(GenericItems.nonfoil == None)\
        .with_entities(GenericItems.name, GenericItems.scryfall_card_id, GenericItems.foil, GenericItems.nonfoil,
                      GenericItems.games)\
        .all()
    items = [x for x in generic_items]
    for i, item in enumerate(items):
        if i%1000==0:
            print(f"{i}/{len(items)}")
        # if item.foil != item.foil and item.nonfoil != item.nonfoil:
        print(item.name, item.scryfall_card_id, item.foil, item.nonfoil, item.games)
    end = time.time()
    print(f"processing generic items took {end-start} s")


# takes a list of sorted offers_history objects corresponding to a single generic item (scryfall_id + foil/nonfoil)
# returns float of best guess at price
# condition is string, multipliers is dict of (condition:multiplier) pairs from MerchantConditionMultipliers table
# first searches for data matching on condition, return latest result if found
# if no condition matches, combines up to 3 most recent results by multiplying by condition ratios and averaging
def estimate_price(offers_history, condition, multipliers):
    condition_matches = [x for x in offers_history if x.condition == condition]
    if len(condition_matches) > 0:
        return condition_matches[0].amount
    matches = offers_history[:3]
    estimate = 0
    for i, match in enumerate(matches):
        condition_multiplier = multipliers[condition]
        match_multiplier = multipliers[match.condition]
        transformed_value = match.amount * condition_multiplier / match_multiplier
        print(f"estimating transformed value of {transformed_value} for match {i}/{len(matches)}")
        estimate += transformed_value
    estimate /= len(matches)
    return estimate


def snapshot_collections():
    collections = db.session.query(ItemCollections).all()
    condition_multipliers = db.session.query(MerchantsConditionMultiplier).filter_by(merchant='PM').all()
    condition_multipliers = {x.condition_id: x.multiplier for x in condition_multipliers}
    for collection in collections:
        try:
            new_history = CollectionHistory()
            real_items = db.session.query(RealItems).filter(RealItems.item_collections_id == collection.database_id)\
                .filter(RealItems.status == 'PUBLISH').all()
            new_history.number_of_items = len(real_items)
            if new_history.number_of_items > 10:
                print(f"processing {collection.name} found {new_history.number_of_items} real items")
            else:
                continue
            new_history.retail_value = 0
            generic_item_ids = [x.item_id for x in real_items]
            print('generic item ids', generic_item_ids[:10])
            # all offers that match some item in the collection
            offers = db.session.query(Offers).filter(Offers.item_id.in_(generic_item_ids)).all()
            offers_ids = [x.id for x in offers]
            print('offers', offers_ids[:10], offers[:10])
            # all offerHistories that match some offer in offers / match some item in the collection
            offer_histories = db.session.query(OffersHistory).filter(OffersHistory.offers_id.in_(offers_ids))\
                .order_by(desc(OffersHistory.last_updated)).all()
            print(offer_histories[:10])
            for real_item in real_items:
                print(f"searching for data for {real_item.item_id} in condition {real_item.condition}")
                # should pick up all offers for a given card, since some of them do not have the matching card condition
                card_offers = [x.id for x in offers if x.item_id == real_item.item_id]
                offer_history = [x for x in offer_histories if x.merchant == 'PM' and x.offers_id in card_offers]
                print(f"found {len(card_offers)} offers, {len(offer_history)} offersHistory")
                if len(offer_history) < 1:
                    continue
                try:
                    pm_offer = estimate_price(offer_history, real_item.condition, condition_multipliers)
                except Exception as ex:
                    print(f"unhandled in estimate_price: {ex}")
                    continue
                new_history.retail_value += pm_offer
                print(f"real item {real_item.database_id} has value {pm_offer}, total at {new_history.retail_value}")
            new_history.timestamp = datetime.now()
            new_history.collectionId = collection.database_id
            db.session.add(new_history)
            db.session.commit()
        except Exception as ex:
            print(f"unhandled {ex}")
            db.session.rollback()

def check_offers():
    # lets use the cards from Ankurs collection as the testbed
    real_items = db.session.query(RealItems).filter_by(item_collections_id=666).all()
    for item in real_items[:5]:
        generic_item: GenericItems = db.session.query(GenericItems).filter_by(id=item.item_id).first()
        latest_offers: LatestOffers = db.session.query(LatestOffers).filter_by(scryfall_card_id=generic_item.scryfall_card_id).first()
        latest_offers_history = db.session.query(LatestOffersHistory).filter_by(offers_id=latest_offers.database_id, merchant='PM').first()
        print(generic_item.scryfall_card_id, item.item_id, generic_item.item_index)
        print('latest', latest_offers_history.amount, latest_offers_history.last_updated)
        offers: Offers = db.session.query(Offers).filter_by(scryfall_card_id=generic_item.scryfall_card_id).order_by(desc(Offers.last_updated)).first()
        offers_history = db.session.query(OffersHistory).filter_by(offers_id=offers.id, merchant='PM').first()
        print('all', offers_history.amount, offers_history.last_updated)
    print(len(real_items))

