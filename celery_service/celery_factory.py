import datetime
from celery import Celery
from sqlalchemy import desc
from .tasks import update_mtgban, snapshot_collections, check_offers
import click
from flask import jsonify
from models.data_models import db, SetModel, RealItems, Offers, OffersHistory, LatestOffers, GenericItems, \
    LatestOffersHistory, MerchantsConditionMultiplier
from loggers import get_logger

celery_logger = get_logger("celery")
celery_logger.debug(f"calling celery factory level logger with name celery")

# celery factory contains (in addition to celery tasks) the daily jobs
# insert daily offers
# snapshot collections
# these daily jobs will probably eventually be parallelized over multiple celery workers

def make_celery(app):
    celery = Celery(
        app.import_name,
        backend=app.config['CELERY_RESULT_BACKEND'],
        broker=app.config['CELERY_BROKER_URL']
    )

    #celery.conf.update(app.config)

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask

    @celery.task
    def background_update_mtgban(mtg_set):
        # some long running task here
        print("starting celery task")
        update_mtgban(mtg_set)

    # bypassing celery until this process is a bottleneck
    def offers_updates(limit_each_set=None, set=None):
        if not(set is None or len(set)==0):
            mtg_sets = set
        else:
            mtg_sets = db.session.query(SetModel).order_by("code").all()
            mtg_sets = [x.code for x in mtg_sets]

        print(f"Updating offers for {len(mtg_sets)} sets")
        celery_logger.debug(f"Updating offers for {len(mtg_sets)} sets")

        for mtg_set in mtg_sets:
            print("processing", mtg_set)
            try:
                ret_val = update_mtgban(mtg_set, limit=limit_each_set)
                if ret_val is False:
                    raise Exception
            except Exception as e:
                celery_logger.debug(f"ERROR at offers_updates with set:{mtg_set}: {e}")
                continue
        return True

    @app.cli.command("insert_daily_offers")
    @click.option('--limit_each_set', '-l', default=None, type=int, help='limit the number of cards processed per set')
    @click.option('--mtg_set', '-s', default=None, type=str, multiple=True, help='Select a specific set to update. Pass each set with a -s')
    def insert_daily_offers(limit_each_set, mtg_set):
        offers_updates(limit_each_set=limit_each_set, set=mtg_set)

    @app.cli.command("insert_offers_test")
    def insert_offers_test():
        celery_logger.debug(f"doing insert offers test with celery worker")
        update_mtgban('lea', testing=True)

    @app.cli.command("snapshot_collections")
    def snapshot():
        snapshot_collections()

    @app.cli.command("check_offers")
    def validate_offers():
        check_offers()

    @celery.task
    def process_real_item(real_item_id, generic_item_id):
        # some long running task here
        print("starting celery task")
        celery_logger.debug(f"starting process real item task for {real_item_id} {generic_item_id}")
        try:
            generic_item = db.session.query(GenericItems).filter_by(id=generic_item_id).first()
            item = db.session.query(RealItems).filter_by(database_id=real_item_id).first()
            if not item.status:
                item.status = 'PUBLISH'
            if not item.condition:
                item.condition = 'LP'
            item.date_updated = datetime.datetime.now()
            db.session.add(item)
            # search through offers table to pull the most up to date offer
            offers = get_offers(generic_item_id)
            if not offers:
                return
            # search latestOffers table for current cached data. if it doesn't exist then create the row
            latest_offers = get_latest_offers(generic_item)
            if not latest_offers:
                return
            celery_logger.debug(f"found latest offer {latest_offers}, updating with most recent data")
            latest_offers.last_updated = offers.last_updated
            db.session.add(latest_offers)
            offers_history = db.session.query(OffersHistory).filter_by(offers_id=offers.id).all()
            latest_offers_history = db.session.query(LatestOffersHistory).filter_by(offers_id=latest_offers.database_id).all()
            celery_logger.debug(f"found {len(offers_history)} history items in offersHistory")
            for history in offers_history:
                if history.merchant == 'PM':
                    item.trade_in_value = calculate_trade_in_value(history, item.condition)

                latest_history_item = [x for x in latest_offers_history if x.merchant == history.merchant]
                if len(latest_history_item) == 0:
                    latest_history_item = LatestOffersHistory(merchant=history.merchant,
                                                              amount=history.amount,
                                                              last_updated=history.last_updated,
                                                              scryfall_card_id=history.scryfall_card_id,
                                                              card_type=history.card_type,
                                                              condition="NM", source=history.source,
                                                              offers_id=latest_offers.database_id)
                else:
                    latest_history_item = latest_history_item[0]
                latest_history_item.amount = history.amount
                latest_history_item.last_updated = datetime.datetime.now()
                db.session.add(latest_history_item)
                db.session.commit()
                celery_logger.debug(f"created or updated {latest_history_item}")
            db.session.commit()
        except Exception as ex:
            db.session.rollback()
            celery_logger.warning(ex)
        celery_logger.debug(f"update real item {real_item_id} celery task complete")

    celery.process_real_item = process_real_item

    @app.route("/celery-update-real-items")
    def celery_update_real_items():
        real_items = db.session.query(RealItems).all()
        for item in real_items:
            process_real_item.delay(item.database_id, item.item_id)
        return jsonify({"message": "completed update"})


    app.celery = celery
    return celery


# check offers for entry
def get_offers(generic_item_id):
    offers = db.session.query(Offers).filter_by(item_id=generic_item_id).order_by(desc(Offers.last_updated)).all()
    if len(offers) == 0:
        celery_logger.debug("no offers were found")
        return None
    offers = offers[0]
    celery_logger.debug(f"most recent offer found is {offers}")
    return offers


# get latestOffers entry (assumes offers for item exists)
def get_latest_offers(generic_item):
    latest_offers = db.session.query(LatestOffers).filter_by(item_id=generic_item.id).all()
    if len(latest_offers) == 0:
        try:
            latest_offers = LatestOffers(scryfall_card_id=generic_item.scryfall_card_id,
                                         item_index=generic_item.item_index,
                                         last_updated=datetime.datetime.now(), item=generic_item,
                                         condition='NM')
            db.session.add(latest_offers)
            db.session.commit()
        except Exception as ex:
            db.session.rollback()
            celery_logger.warning(str(ex))
            return None
    else:
        latest_offers = latest_offers[0]
    return latest_offers


# use condition multipliers and latest offer to calculate trade_in_value
def calculate_trade_in_value(pm_lp_offer, condition):
    condition_multiplier = db.session.query(MerchantsConditionMultiplier).filter_by(merchant='PM', condition_id=condition).first()
    return pm_lp_offer.amount*condition_multiplier.multiplier

