from ast import Assert
import sys, os
topdir = os.path.join(os.path.dirname(__file__), "..")
sys.path.append(topdir)
from app import create_app
from celery_service.tasks import *
from flask import g, session, url_for, template_rendered, request, Response, jsonify
import pytest
from loggers import get_logger
from datetime import timedelta
from sqlalchemy import and_
from click.testing import CliRunner
from celery_service.celery_factory import make_celery
from app import app
from models.data_models import db, SetModel

celery_logger = get_logger("celery")

@pytest.fixture
def client():
    app = create_app()
    if os.getenv('MTGBAN_SIG') is None:
        import sigvar
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

@pytest.mark.parametrize("testing", [True, False])
def test_update_scryfall_id_force_test(client, testing):
    buy_list = BuyList(mtg_set='ced', testing=testing)
    test_scry_id = 'fbe47ed7-33a9-4464-b720-d738af997159'
    ret_val = buy_list.update_by_scryfall_id(test_scry_id)

    celery_logger.debug(f"TEST test_update_scryfall_id Update Portion Succeded. Moving to Check")

    ## After the update operation, check if all expected rows are there
    buy_dict = buy_list.buy_dict
    
    # Check if the Expected Rows are there. Query using SCRY_ID and Foiltype
    offer = buy_list.get_offers(test_scry_id)
    one_day_interval_before = datetime.today() - timedelta(days=1)

    for foil_type in offer.keys():
        is_foil = buy_list.is_foil(foil_type)

        # Generic Item
        generic_item = db.session.query(GenericItems).filter_by(
            scryfall_card_id=test_scry_id, foil=is_foil, nonfoil=not(is_foil)).first()
        if generic_item is None:
            raise AssertionError("NO GENERIC ITEM FOUND")

        # Offer
        my_offer = db.session.query(Offers).filter_by(
            scryfall_card_id=test_scry_id,
            item_index=generic_item.item_index,
            item=generic_item,
            condition='NM').\
            filter(Offers.last_updated >= one_day_interval_before).order_by(Offers.id.desc()).first()
        
        if my_offer is None:
            raise AssertionError("NO OFFER FOUND")

        #Latest Offer
        latest_offer = db.session.query(LatestOffers).filter_by(
            item_id = generic_item.id,
            condition = 'NM',
            scryfall_card_id = test_scry_id,
            item_index = generic_item.item_index,
            item=generic_item).\
            filter(Offers.last_updated >= one_day_interval_before).first()

        if latest_offer is None:
            raise AssertionError("NO LATEST OFFER FOUND")

        highest_offer = 0
        for merchant in buy_list.get_merchants(test_scry_id, foil_type):
            offer_amount = buy_list.get_offer_amount(test_scry_id, foil_type, merchant)
            rounded_offer = round(offer_amount, 2)

            omit_merchants = ['HA', 'TCGMkt']# Omit these merchants
            if merchant == 'ABU':
                matching_offer = 0.8*rounded_offer
            else:
                matching_offer = rounded_offer
            
            if matching_offer > highest_offer and merchant not in omit_merchants:
                highest_offer = matching_offer

            offer = db.session.query(OffersHistory).filter_by(
                scryfall_card_id=test_scry_id,
                offers_id = my_offer.id,
                card_type=foil_type,
                condition='NM',
                amount=rounded_offer,
                merchant=merchant,
                source='MTGBAN'
            ).filter(Offers.last_updated >= one_day_interval_before).first()

            if offer is None:
                raise AssertionError("NO OFFERS HISTORY FOUND")

            #Latest Offer
            latestoffer = db.session.query(LatestOffersHistory).filter_by(
                offers_id= latest_offer.database_id,
                merchant = merchant,
                amount = rounded_offer,
                card_type = foil_type,
                condition = 'NM',
                source = 'MTGBAN'
            ).filter(Offers.last_updated >= one_day_interval_before).first()

            if latest_offer is None:
                raise AssertionError("NO LATEST OFFERS HISTORY FOUND")

        #Check for PM OffersHistory and LatestOfferHistory
        pm_offer_history = db.session.query(OffersHistory).filter_by(
            scryfall_card_id=test_scry_id,
            offers_id = my_offer.id,
            card_type=foil_type,
            condition='NM',
            amount=highest_offer,
            merchant='PM',
            source='Purplemana'
        ).filter(Offers.last_updated >= one_day_interval_before).first()

        if pm_offer_history is None:
            raise AssertionError("NO PM OFFER FOUND")

        #Latest Offer
        pm_latest_offer = db.session.query(LatestOffersHistory).filter_by(
            offers_id= latest_offer.database_id,
            merchant = 'PM',
            amount = highest_offer,
            card_type = foil_type,
            condition = 'NM',
            source = 'Purplemana'
        ).filter(Offers.last_updated >= one_day_interval_before).first()

        if pm_latest_offer is None:
            raise AssertionError("NO LATEST PM OFFER FOUND")

# Using actual live data
def test_update_scryfall_id(client):
    buy_list = BuyList(mtg_set='ced', testing=False)
    test_scry_id = 'fbe47ed7-33a9-4464-b720-d738af997159'
    ret_val = buy_list.update_by_scryfall_id(test_scry_id)
    
    assert ret_val == True
    celery_logger.debug(f"TEST test_update_scryfall_id Update Portion Succeded. Moving to Check")

    ## After the update operation, check if all expected rows are there
    
    # Check if the Expected Rows are there. Query using SCRY_ID and Foiltype
    offer = buy_list.get_offers(test_scry_id)
    one_day_interval_before = datetime.today() - timedelta(days=1)

    for foil_type in offer.keys():
        highest_offer = 0
        is_foil = buy_list.is_foil(foil_type)
        # Generic Item
        generic_item = db.session.query(GenericItems).filter_by(
            scryfall_card_id=test_scry_id, foil=is_foil, nonfoil=not(is_foil)).first()
        if generic_item is None:
            raise AssertionError("NO GENERIC ITEM FOUND")

        # Offer
        my_offer = db.session.query(Offers).filter_by(
            scryfall_card_id=test_scry_id,
            item_index=generic_item.item_index,
            item=generic_item,
            condition='NM').\
            filter(Offers.last_updated >= one_day_interval_before).order_by(Offers.id.desc()).first()
        
        if my_offer is None:
            raise AssertionError("NO OFFER FOUND")

        #Latest Offer
        latest_offer = db.session.query(LatestOffers).filter_by(
            item_id = generic_item.id,
            condition = 'NM',
            scryfall_card_id = test_scry_id,
            item_index = generic_item.item_index,
            item=generic_item).\
            filter(Offers.last_updated >= one_day_interval_before).first()

        if latest_offer is None:
            raise AssertionError("NO LATEST OFFER FOUND")

        for merchant in buy_list.get_merchants(test_scry_id, foil_type):
            offer_amount = buy_list.get_offer_amount(test_scry_id, foil_type, merchant)
            rounded_offer = round(offer_amount, 2)
            
            ## Merchant Specific Condtiions
            omit_merchants = ['HA', 'TCGMkt', 'CS']
            # for AB we will reduce their offer due to price inflation
            if merchant == 'ABU':
                    matching_offer = 0.8*rounded_offer
            else:
                matching_offer = rounded_offer
            if matching_offer > highest_offer and merchant not in omit_merchants:
                highest_offer = matching_offer

            offer = db.session.query(OffersHistory).filter_by(
                scryfall_card_id=test_scry_id,
                offers_id = my_offer.id,
                card_type=foil_type,
                condition='NM',
                amount=rounded_offer,
                merchant=merchant,
                source='MTGBAN'
            ).filter(Offers.last_updated >= one_day_interval_before).first()

            if offer is None:
                raise AssertionError("NO OFFER FOUND")

            #Latest Offer
            latestoffer = db.session.query(LatestOffersHistory).filter_by(
                offers_id= latest_offer.database_id,
                merchant = merchant,
                amount = offer_amount,
                card_type = foil_type,
                condition = 'NM',
                source = 'MTGBAN'
            ).filter(Offers.last_updated >= one_day_interval_before).first()

            if latest_offer is None:
                raise AssertionError("NO LATEST OFFER FOUND")

        #Assert that the PM OffersHistory and LatestOfferHistory are there
        pm_offer_history = db.session.query(OffersHistory).filter_by(
            scryfall_card_id=test_scry_id,
            offers_id = my_offer.id,
            card_type=foil_type,
            condition='NM',
            amount=highest_offer,
            merchant='PM',
            source='Purplemana'
        ).filter(Offers.last_updated >= one_day_interval_before).first()

        if pm_offer_history is None:
            raise AssertionError("NO PM OFFER FOUND")

        #Latest Offer
        pm_latest_offer = db.session.query(LatestOffersHistory).filter_by(
            offers_id= latest_offer.database_id,
            merchant = 'PM',
            amount = highest_offer,
            card_type = foil_type,
            condition = 'NM',
            source = 'Purplemana'
        ).filter(Offers.last_updated >= one_day_interval_before).first()

        if pm_latest_offer is None:
            raise AssertionError("NO LATEST PM OFFER FOUND")

@pytest.mark.parametrize("testing", [True, False])
def test_update_mtgban(client, testing):
    # Testing with testing=False is loading the stored buy_list dictionary
    # Testing with testing=True is loading the live buy_list from the api 
    #Setup test
    mtg_set = 'ced'
    limit = 2
    # Update 
    ret_val = update_mtgban(mtg_set, testing=testing, limit=limit)
    assert ret_val is True

    ## Check if the Expected Rows are there. Query using SCRY_ID and Foiltype
    buy_list = BuyList(mtg_set=mtg_set, testing=testing, limit=limit) #Use this function to get the mtg_set

    for scry_id in buy_list.get_scryfall_ids():
        offer = buy_list.get_offers(scry_id)
        one_day_interval_before = datetime.today() - timedelta(days=1)

        for foil_type in offer.keys():
            highest_offer = 0
            is_foil = buy_list.is_foil(foil_type)
            # Generic Item
            generic_item = db.session.query(GenericItems).filter_by(
                scryfall_card_id=scry_id, foil=is_foil, nonfoil=not(is_foil)).all()
            
            if len(generic_item) >= 1:
                #Choose the first item that doesn't have the 'UPDATE ME' as name
                for item in generic_item:
                    if item.name != 'UPDATE ME':
                        generic_item = item
                        break
                else:
                    raise AssertionError("NO GENERIC ITEM FOUND")
            else:
                generic_item=generic_item[0]

            if generic_item is None:
                raise AssertionError("NO GENERIC ITEM FOUND")
                
            # Offer
            my_offer = db.session.query(Offers).filter_by(
                scryfall_card_id=scry_id,
                item_index=generic_item.item_index,
                item=generic_item,
                condition='NM').\
                filter(Offers.last_updated >= one_day_interval_before).order_by(Offers.id.desc()).first()
            
            if my_offer is None:
                raise AssertionError("NO OFFER FOUND")

            #Latest Offer
            latest_offer = db.session.query(LatestOffers).filter_by(
                item_id = generic_item.id,
                condition = 'NM',
                scryfall_card_id = scry_id,
                item_index = generic_item.item_index,
                item=generic_item).\
                filter(Offers.last_updated >= one_day_interval_before).first()

            if latest_offer is None:
                raise AssertionError("NO LATEST OFFER FOUND")

            for merchant in buy_list.get_merchants(scry_id, foil_type):
                offer_amount = buy_list.get_offer_amount(scry_id, foil_type, merchant)
                rounded_offer = round(offer_amount, 2)

                omit_merchants = ['HA', 'TCGMkt', 'CS']
                # for AB we will reduce their offer due to price inflation
                if merchant == 'ABU':
                    matching_offer = 0.8*rounded_offer
                else:
                    matching_offer = rounded_offer

                if matching_offer > highest_offer and merchant not in omit_merchants:
                    highest_offer = matching_offer

                offer = db.session.query(OffersHistory).filter_by(
                    scryfall_card_id=scry_id,
                    offers=my_offer,
                    card_type=foil_type,
                    condition='NM',
                    amount=rounded_offer,
                    merchant=merchant,
                    source='MTGBAN'
                ).filter(Offers.last_updated >= one_day_interval_before).first()

                if offer is None:
                    raise AssertionError("NO OFFERSHISTORY FOUND")

                #Latest Offer
                latestoffer = db.session.query(LatestOffersHistory).filter_by(
                    offers_id= latest_offer.database_id,
                    merchant = merchant,
                    amount = offer_amount,
                    card_type = foil_type,
                    condition = 'NM',
                    source = 'MTGBAN'
                ).filter(Offers.last_updated >= one_day_interval_before).first()

                if latest_offer is None:
                    raise AssertionError("NO LATEST OFFER FOUND")

            pm_offer_history = db.session.query(OffersHistory).filter_by(
                scryfall_card_id=scry_id,
                offers=my_offer,
                card_type=foil_type,
                condition='NM',
                amount=highest_offer,
                merchant='PM',
                source='Purplemana'
            ).filter(Offers.last_updated >= one_day_interval_before).first()

            if pm_offer_history is None:
                raise AssertionError("NO PM OFFER FOUND")

            #Latest Offer
            pm_latest_offer = db.session.query(LatestOffersHistory).filter_by(
                offers_id= latest_offer.database_id,
                merchant = 'PM',
                amount = highest_offer,
                card_type = foil_type,
                condition = 'NM',
                source = 'Purplemana'
            ).filter(Offers.last_updated >= one_day_interval_before).first()

            if pm_latest_offer is None:
                raise AssertionError("NO LATEST PM OFFER FOUND")

        celery_logger.debug(f"TEST CHECK: Success updating ID:{scry_id} with all merchants and offers")
    
    celery_logger.debug(f"TEST CHECK: Success updating all IDs in {mtg_set}")

@pytest.mark.skip(reason="Takes too long to run on automation")
def test_insert_daily_offers_quick_sets(client):
    ## WARNING: This test takes long
    # Goes through all the setmodels and udpates one entry to check for set viability
    ## Updates one item of each set to test for set compatability using the offers_updates(limit=1) argument
    # Setup test
    limit = 1

    # Start Test
    mtg_sets = db.session.query(SetModel).order_by("code").all()
    mtg_sets = [x.code for x in mtg_sets]
    print(f"Updating offers for {len(mtg_sets)} sets")
    celery_logger.debug(f"Updating offers for {len(mtg_sets)} sets")
    success_flag = True
    passed_sets = set()
    for mtg_set in mtg_sets:
        try:
            ret_val = update_mtgban(mtg_set, limit=limit)
            if ret_val is False:
                success_flag = False
                raise Exception
            else:
                passed_sets.add(mtg_set)
        except Exception as e:
            celery_logger.debug(f"ERROR at updating mtgban with set:{mtg_set}")
            continue
        
        #Create log PASSED: len(passed_sets)/len(mtg_sets)
        celery_logger.debug(f"Passed{mtg_set} | {len(passed_sets)}/{len(mtg_sets)}")
    
    celery_logger.debug(f"Success sets: {passed_sets} | Failed sets: {set(mtg_sets) - passed_sets}")
    assert success_flag

pytest.mark.skip(reason="Not yet implemented")
def test_update_scryfall_id_multiprocessing(client):
    #Setup Test Parameters
    #Compare the two times
    #print(f"TEST INFO: Successfully updated {len(buy_list.get_scryfall_ids())} scryfall ids in {time_multi} seconds")
    #print(f"TEST INFO: Multi-processed update was {time_multi/time_single} times faster than single-processed update")
    pass

from sqlalchemy import func, cast, Date
from datetime import date

import cProfile
import io
import pstats
import contextlib

@contextlib.contextmanager
def profiled():
    pr = cProfile.Profile()
    # Save PR to file
    
    pr.enable()
    yield
    pr.disable()
    s = io.StringIO()
    ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
    ps.print_stats()
    #uncomment this to see who's calling what
    #ps.print_callers()
    print(s.getvalue())


    
    



