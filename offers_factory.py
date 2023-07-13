from sqlalchemy import Float, Integer
from models.data_models import db, GenericItems, Offers, OffersHistory, LatestOffers, LatestOffersHistory
from flask import session, url_for, render_template, request, Response, Blueprint, redirect
import pytest
from security import user_is_admin
#from get_lo import offers_logger

offers_factory = Blueprint("offers", __name__, static_folder="static", template_folder="templates")

def get_all_pm_offers(generic_item_index= None):
    #Get offers realted
    results = db.session.query(GenericItems, LatestOffersHistory, LatestOffers) \
        .filter(GenericItems.item_index == generic_item_index) \
        .filter(LatestOffers.item_id == GenericItems.id) \
        .filter(LatestOffersHistory.offers_id == LatestOffers.database_id) \
        .order_by(LatestOffersHistory.merchant.desc()) \
        .all() 
    #results = db.session.query(Offers, OffersHistory, LatestOffersHistory, LatestOffers).join(OffersHistory).join(LatestOffersHistory).join(LatestOffers).filter(LatestOffersHistory.merchant == 'PM').all()
    print("Query done")
    return results

@offers_factory.route('/offer_pricing/<gen_item_index>')
@user_is_admin
def offer_pricing(gen_item_index):
    results = get_all_pm_offers(gen_item_index)    

    gen_items = results[0].GenericItems.__dict__
    latest_offers = [ result.LatestOffers.__dict__ for result in results ]
    latest_offers_history = [ result.LatestOffersHistory.__dict__ for result in results ]

    return render_template('offer_pricing.html', gen_item=gen_items, 
        latest_offers=latest_offers,
        latest_offers_history=latest_offers_history, content = [])  

from wtforms import StringField, SubmitField, IntegerField, FloatField
from wtforms.validators import DataRequired, Optional 
from flask_wtf import FlaskForm
from datetime import datetime, timedelta

class EditPmPrice(FlaskForm):
    generic_item_index = StringField('generic_item_index', validators = [DataRequired()])
    new_price = FloatField('new_price', validators = [DataRequired()])
    latest_offers_id = IntegerField('latest_offers_id', validators = [DataRequired()])
    latest_offers_history_id = IntegerField('latest_offers_history_id', validators = [DataRequired()])

@offers_factory.route('/edit_pm_price', methods=['POST'])
@user_is_admin
def edit_pm_price():
    print("Here at EDIT PM Price")
    form = EditPmPrice(meta={'csrf': False})
    one_day_before = datetime.today() - timedelta(days=1)
    if form.validate_on_submit():
        generic_item_index = form.data['generic_item_index']
        new_price = form.data['new_price']
        latest_offers_id = form.data['latest_offers_id']
        latest_offers_history_id = form.data['latest_offers_history_id']

        latest_offer_history = db.session.query(LatestOffersHistory). \
            filter(LatestOffersHistory.offers_id == latest_offers_history_id). \
            filter(LatestOffersHistory.merchant=='PM'). \
            order_by(LatestOffersHistory.last_updated.asc()).first()
        
        
        if latest_offer_history is None or latest_offer_history.last_updated < one_day_before:
            try:
                #Entry too old, creating a new one or None found
                print("Creating a New Latest Offers History")

                #Query the LatestOffers table for the data we want
                latest_offer = db.session.query(LatestOffers).filter(LatestOffers.database_id == latest_offers_id).first()

                similar_latest_offers_history = db.session.query(LatestOffersHistory.card_type). \
                    filter(LatestOffersHistory.offers_id == latest_offers_id). \
                    filter(LatestOffersHistory.scryfall_card_id == latest_offer.scryfall_card_id). \
                    order_by(LatestOffersHistory.last_updated.asc()).first()
                
                
                latest_offer_history = LatestOffersHistory(
                    scryfall_card_id = latest_offer.scryfall_card_id,
                    last_updated = datetime.today(),
                    source = "PM Admin Override",
                    merchant = "PM",
                    amount = new_price,
                    card_type = similar_latest_offers_history.card_type,
                    condition = latest_offer.condition,
                    offers_id = latest_offers_id)
                
                db.session.add(latest_offer_history)
                db.session.commit()
                print(f"Price updated for {latest_offer_history.merchant} with amount {new_price}")

            except Exception as e:
                print(f'Error creating new LatestOffersHistory: {e}')
        
        else:
            print(f'Updating price for PM {generic_item_index} to {new_price}')
            latest_offer_history.amount = new_price
            latest_offer_history.last_updated = db.func.now()
            latest_offer_history.source = "PM Admin Override"
            db.session.commit()
            print(f'Success! latest_offer_history_id: {latest_offer_history.database_id}')
    

        
        #offers_logger.debug("Updated price for offer_id: %s", latest_offers_id)
        return redirect(url_for('offers.offer_pricing',gen_item_index=generic_item_index))
