import datetime
from graphene import Mutation, String, Boolean, Field, Int, List, Float, Date
from sqlalchemy import or_, exc
from items_factory import total_value_of_real_item_list, estimated_value_of_real_item, \
    update_item_list_on_real_item_mutation, make_item_hash
from models.data_models import db, ItemCollections, RealItems, Users, GenericItems, SetModel, \
    Conditions, Merchants, Activities, Subscriptions, Media, Defects, Transactions, LatestOffers, LatestOffersHistory, \
    TransactionItems, ItemLists, MerchantsConditionMultiplier, ListingFeedback, EbayListing, TransactionStatus, TransactionLogs
from .ItemManager import ItemManager
from .TransactionManager import TransactionManager
from .graphene_models import ItemCollectionObject, RealItemObject, GenericItemObject, \
    UserObject, SetObject, ConditionsObject, MerchantsObject, SubscriptionsObject, MediaObject, \
    DefectsObject, TransactionsObject, TransactionItemObject, ItemListsObject, ListingFeedbackObject, TransactionLogObject
import os
import requests
from security import user_is_logged_in, user_is_admin
from flask import session
import logging
from media_factory import external_remove_media
import boto3
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from loggers import transaction_logger


class UpdateUser(Mutation):
    """requires id, used for setting user preferences: per_page, view_mode, color_theme"""
    class Arguments:
        database_id = Int(required=True)
        per_page = Int()
        view_mode = String()
        color_theme = String()
        username = String()
        name = String()
        street1 = String()
        street2 = String()
        city = String()
        state = String()
        zip = String()
        country = String()

    ok = Field(Boolean, default_value=False)
    user = Field(lambda: UserObject)
    debug = Field(String, default_value="no debug info")

    @user_is_logged_in
    def mutate(root, info, database_id, per_page=None, view_mode=None, color_theme=None, username=None, name=None,
               street1=None, street2=None, city=None, state=None, zip=None, country=None, **kwargs):
        my_user = Users()
        try:
            my_user: Users = db.session.query(Users).filter_by(database_id=database_id).first()
            if not my_user:
                raise Exception("no user found")
            if my_user.database_id != session["user_id"]:
                raise Exception("user can't modify other users preferences")
            if per_page:
                my_user.per_page = per_page
            if view_mode:
                if view_mode not in ["grid", "list"]:
                    raise Exception("view mode may only be either grid or list")
                my_user.view_mode = view_mode
            if color_theme:
                if color_theme not in ["light", "dark"]:
                    raise Exception("color theme may only be either light or dark")
                my_user.color_theme = color_theme
            if username:
                my_user.username = username
            if name:
                my_user.real_name = name
            if street1:
                my_user.address_line_one = street1
            if street2:
                my_user.address_line_two = street2
            if city:
                my_user.address_city = city
            if state:
                my_user.address_state = state
            if zip:
                my_user.address_zipcode = zip
            if country:
                my_user.address_country = country
            db.session.add(my_user)
            db.session.commit()
            ok = True
        except Exception as ex:
            db.session.rollback()
            return UpdateUser(user=my_user, debug=str(ex))

        return UpdateUser(user=my_user, ok=ok)


class CreateItemList(Mutation):
    """requires name, owner is set to the user that is currently logged in / session user"""
    class Arguments:
        name = String(required=True)
        public = Boolean()

    ok = Field(Boolean, default_value=False)
    item_list = Field(lambda: ItemListsObject)
    debug = Field(String, default_value="no debug info")

    @user_is_logged_in
    def mutate(root, info, name, **kwargs):
        my_list = ItemLists()
        try:
            my_list = ItemLists(name=name, user_id=session["user_id"])
            my_list.date_created = datetime.datetime.now()
            my_list.date_updated = datetime.datetime.now()
            my_list.count = 0
            my_list.value = 0
            db.session.add(my_list)
            db.session.commit()

            # integromat content endpoint
            # https://hook.integromat.com/q1x3846bbmscrcrndzitlg7py1n9bsv2
            url = "https://hook.integromat.com/q1x3846bbmscrcrndzitlg7py1n9bsv2"
            user = db.session.query(Users).filter_by(database_id=session['user_id']).first()
            params = {
                "user": user.username,
                "name": my_list.name,
                "url": f"https://juzam.purplemana.com/lists/{str(my_list.database_id)}"
            }
            if os.getenv('FLASK_ENV') == 'production':
                requests.get(url, params=params)
            ok = True
        except Exception as ex:
            db.session.rollback()
            return CreateItemList(collection=my_list, debug=str(ex))

        return CreateItemList(item_list=my_list, ok=ok)


class UpdateItemList(Mutation):
    class Arguments:
        database_id = Int(required=True)
        name = String()
        public = Boolean()
        user_id = Int()

    ok = Field(Boolean, default_value=False)
    item_list = Field(lambda: ItemListsObject)
    debug = Field(String, default_value="no debug info")

    @user_is_logged_in
    def mutate(root, info, database_id, name=None, public=None, user_id=None):
        try:
            my_list = db.session.query(ItemLists).filter_by(database_id=database_id).first()
            if not my_list:
                raise Exception(f"list with id {database_id} wasn't found for user with roles {session['roles']}")

            if "administrator" in session["roles"]:
                if user_id:
                    my_list.user_id = user_id
            elif my_list.user_id != session['user_id']:
                raise Exception("user can't update item list unless its owned")
            
            if name:
                my_list.name = name
      
            if public:
                pass

            my_list.date_updated = datetime.datetime.now()
            db.session.add(my_list)
            db.session.commit()
            ok = True
        except Exception as ex:
            db.session.rollback()
            return UpdateItemList(debug=str(ex))
        return UpdateItemList(ok=ok, item_list=my_list)

class DeleteItemList(Mutation):
    class Arguments:
        database_id = Int(required=True)

    ok = Field(Boolean, default_value=False)
    debug = Field(String, default_value="no debug info")

    @user_is_logged_in
    def mutate(root, info, database_id):
        try:
            my_list = db.session.query(ItemLists).filter_by(database_id=database_id).first()
            if not my_list:
                raise Exception(f"list with id {database_id} wasn't found for user with roles {session['roles']}")
            if "administrator" in session["roles"]:
                pass
            elif my_list.user_id != session['user_id']:
                raise Exception("user can't delete item list unless owned")
            if database_id == 296:
                raise Exception("dont try to delete the vault")
            items = db.session.query(RealItems).filter_by(item_list_id=my_list.database_id).all()
            delete_stale_transactions([x.database_id for x in items])

            for my_item in items:
                my_item.item_list_id = 333
                my_item.owner = 4
                my_item.item_collections_id = 717
                db.session.add(my_item)
                db.session.commit()

            list_id = my_list.database_id
            ItemLists.query.filter_by(database_id=list_id).delete()
            db.session.commit()
            ok = True
        except Exception as ex:
            db.session.rollback()
            return DeleteItemList(debug=str(ex))
        return DeleteItemList(ok=ok)


class CreateMedia(Mutation):
    class Arguments:
        real_item_id = Int(required=True)
        type = String(required=True)
        media_url = String(required=True)
        label = String(required=True)

    ok = Field(Boolean, default_value=False)
    media = Field(lambda: MediaObject)
    debug = Field(String, default_value="no debug info")

    def mutate(root, info, real_item_id, type, media_url, label):
        my_media = Media()
        try:
            my_media = Media()
            my_media.realitem_id = real_item_id
            realitem = db.session.query(RealItems).filter_by(database_id=real_item_id).first()

            real_item_mutation_auth(realitem)

            my_media.realitem = realitem
            my_media.type = type
            my_media.media_url = media_url
            my_media.label = label
            my_media.date_created = datetime.datetime.now()
            db.session.add(my_media)
            db.session.commit()
            ok = True
        except Exception as ex:
            db.session.rollback()
            return CreateMedia(media=my_media, debug=str(ex))
        else:
            return CreateMedia(media=my_media, ok=ok)


class UpdateMedia(Mutation):
    class Arguments:
        database_id = Int(required=True)
        real_item_id = Int()
        type = String()
        media_url = String()
        label = String()

    ok = Field(Boolean, default_value=False)
    media = Field(lambda: MediaObject)
    debug = Field(String, default_value="no debug info")

    def mutate(root, info, database_id, real_item_id=None, type=None, media_url=None, label=None):
        my_media = Media()
        try:
            my_media = db.session.query(Media).filter_by(database_id=database_id).first()
            real_item = db.session.query(RealItems).filter_by(database_id=my_media.realitem_id).first()

            real_item_mutation_auth(real_item)

            if real_item_id:
                my_media.realitem_id = real_item_id
                realitem = db.session.query(RealItems).filter_by(database_id=real_item_id).first()
                my_media.realitem = realitem
            if type:
                my_media.type = type
            if media_url:
                my_media.media_url = media_url
            if label:
                my_media.label = label
            my_media.date_updated = datetime.datetime.now()
            db.session.add(my_media)
            db.session.commit()
            ok = True
        except Exception as ex:
            db.session.rollback()
            return UpdateMedia(media=my_media, debug=str(ex))
        else:
            return UpdateMedia(media=my_media, ok=ok)


class DeleteMedia(Mutation):
    class Arguments:
        database_id = Int(required=True)

    ok = Field(Boolean, default_value=False)
    debug = Field(String, default_value="no debug info")

    def mutate(root, info, database_id):
        try:
            my_media = db.session.query(Media).filter_by(database_id=database_id).first()
            real_item = db.session.query(RealItems).filter_by(database_id=my_media.realitem_id).first()

            real_item_mutation_auth(real_item)

            # delete item from s3 bucket
            try:
                print('starting remove media')
                external_remove_media(database_id)
            except Exception as ex:
                return DeleteRealItem(debug=str(ex))

            db.session.query(Media).filter_by(database_id=database_id).delete()
            db.session.commit()
            ok = True
        except Exception as ex:
            db.session.rollback()
            return UpdateMedia(debug=str(ex))
        else:
            return UpdateMedia(ok=ok)


class RealItemCreateAndEditArguments:
    condition = String()
    forsale_price = Float()


class CreateRealItem(Mutation):
    """item_id is genericItemId, sets creator to session user, sets owner to session user. creates activity"""
    class Arguments(RealItemCreateAndEditArguments):
        item_id = Int(required=True)
        item_list_id = Int(required=True)

    ok = Field(Boolean, default_value=False)
    real_item = Field(lambda: RealItemObject)
    debug = Field(String, default_value="no debug info")

    @user_is_logged_in
    def mutate(root, info, item_id, item_list_id, **kwargs):
        my_item = RealItemObject()
        try:
            my_item = RealItems()
            my_item.item_id = item_id

            default = db.session.query(ItemCollections).filter_by(user_id=session['user_id'], name='default').first()
            if not default:
                default = ItemCollections(user_id=session['user_id'], name='default')
                db.session.add(default)
                db.session.commit()
            my_item.item_collections_id = default.database_id
            item_list = db.session.query(ItemLists).filter_by(database_id=item_list_id).first()
            if not item_list:
                raise Exception("no item list found")
            if 'administrator' in session['roles']:
                pass
            elif item_list.user_id == session['user_id']:
                pass
            else:
                raise Exception("user can only update their own item lists")
            my_item.item_list_id = item_list_id
            my_item.creator = session['user_id']
            my_item.owner = session['user_id']
            my_item.status = 'NEW'
            my_item.date_created = datetime.datetime.now()
            editable_fields = [x for x in dir(RealItemCreateAndEditArguments) if '__' not in x]
            for field in kwargs:
                if field not in editable_fields:
                    continue
                setattr(my_item, field, kwargs[field])
            if not my_item.condition:
                my_item.condition = 'LP'
            my_item.item_hash = make_item_hash(my_item)
            db.session.add(my_item)
            db.session.commit()

            # update item lists with new summary data
            my_item.fmv = estimated_value_of_real_item(my_item)
            update_item_list_on_real_item_mutation(item_list_id)

            db.session.add(my_item)
            db.session.commit()
            ok = True
        except Exception as ex:
            db.session.rollback()
            return CreateRealItem(real_item=my_item, debug=str(ex))
        return CreateRealItem(real_item=my_item, ok=ok)


def real_item_mutation_auth(item):
    if 'administrator' in session['roles']:
        pass
    elif session['user_id'] != item.owner:
        raise Exception("users can only modify their own items")
    else:
        pass


def transaction_auth(status):
    if status not in ['CLIENT_REVIEW', 'PURPLEMANA_REVIEW'] and 'administrator' not in session['roles']:
        raise Exception("users can only modify real items in unconfirmed transactions")
    elif status not in ['CLIENT_REVIEW', 'PURPLEMANA_REVIEW', 'GRADING'] and 'administrator' in session['roles']:
        raise Exception("admins can only modify real item in unconfirmed transactions and in GRADING transactions")


def total_credit_from_transaction(transaction_id):
    remaining_items = db.session.query(TransactionItems).filter_by(transaction_id=transaction_id)
    new_total = 0
    for item in remaining_items:
        if item.admin_price:
            new_total += item.admin_price
        elif item.trade_in_value:
            new_total += item.trade_in_value
        else:
            pass
    return round(new_total, 2)


def real_item_mutation_transaction_auth(item):
    # get active transaction if it exists
    transaction_items = db.session.query(TransactionItems).filter_by(real_item_id=item.database_id).all()
    transactions = [x.transaction_id for x in transaction_items]
    active_transactions = db.session.query(Transactions)\
        .filter(Transactions.database_id.in_(transactions))\
        .filter(Transactions.status != 'CREDIT_ISSUED').all()
    if not active_transactions:
        return
    if len(active_transactions) > 1:
        print("real item is involved in multiple transactions")
    active_transaction = active_transactions[0]
    status = active_transaction.status
    transaction_auth(status)


def update_transactions_on_real_item_mutation(real_item_id, mutation='CONDITION'):
    print("updating on real item", real_item_id)
    real_item = db.session.query(RealItems).filter_by(database_id=real_item_id).first()
    affected_items = db.session.query(TransactionItems).filter_by(real_item_id=real_item_id).all()
    affected_transaction_ids = list(set([x.transaction_id for x in affected_items]))
    affected_transactions = db.session.query(Transactions).filter(Transactions.database_id.in_(affected_transaction_ids)).all()

    # real items were authed before this point and transaction is in CLIENT_REVIEW, PURPLEMANA_REVIEW, GRADING, GRADED
    for transaction in affected_transactions:
        if transaction.status == 'CREDIT_ISSUED':
            continue
        mutated_item = [x for x in affected_items if x.transaction_id == transaction.database_id][0]
        if mutation == 'DELETE':
            db.session.query(TransactionItems).filter_by(database_id=mutated_item.database_id).delete()
            db.session.commit()
            message = f"{session['username']} deleted real item {real_item.item_hash}"
        elif mutation == 'CONDITION':
            mutated_item.trade_in_value = round(estimated_value_of_real_item(real_item), 2)
            db.session.add(mutated_item)
            db.session.commit()
            message = f"{session['username']} updated {mutation.lower()} of real item {real_item.item_hash} to {real_item.condition}"
        elif mutation == 'ITEM_ID':
            mutated_item.trade_in_value = round(estimated_value_of_real_item(real_item), 2)
            db.session.add(mutated_item)
            db.session.commit()
            generic_item = db.session.query(GenericItems).filter_by(id=real_item.item_id).first()
            message = f"{session['username']} updated {mutation.lower()} of real item {real_item.item_hash} to {generic_item.name}"
        else:
            message = f"{session['username']} updated real item {real_item.item_hash} unhandled log case"

        log = TransactionLogs(transaction_id=transaction.database_id, date_created=datetime.datetime.now(), message=message)
        db.session.add(log)
        if transaction.status in ['CLIENT_REVIEW', 'PURPLEMANA_REVIEW']:
            transaction.status = 'CLIENT_REVIEW'
        transaction.right_credit = total_credit_from_transaction(transaction.database_id)
        db.session.add(transaction)
        db.session.commit()


class UpdateRealItem(Mutation):
    """databaseId is realItemId, user must be owner of realItem or admin to update"""
    class Arguments(RealItemCreateAndEditArguments):
        database_id = Int(required=True)
        item_list_id = Int()
        item_id = Int()

    ok = Field(Boolean, default_value=False)
    real_item = Field(lambda: RealItemObject)
    debug = Field(String, default_value="no debug info")

    @user_is_logged_in
    def mutate(root, info, database_id, item_list_id=None, item_id=None, **kwargs):
        my_item = RealItems()
        print("in real items update mutator searching for", database_id, session['user_id'])
        try:
            my_item: RealItems = db.session.query(RealItems).filter_by(database_id=database_id).first()

            # permission auth throws exceptions
            real_item_mutation_auth(my_item)

            # business logic auth (status allowed actions)
            real_item_mutation_transaction_auth(my_item)

            # field updates and db commit
            if item_list_id:
                my_item.item_list_id = item_list_id
            if item_id:
                my_item.item_id = item_id
            my_item.date_updated = datetime.datetime.now()
            editable_fields = [x for x in dir(RealItemCreateAndEditArguments) if '__' not in x]
            for field in kwargs:
                if field not in editable_fields:
                    continue
                setattr(my_item, field, kwargs[field])
            my_item.item_hash = make_item_hash(my_item)
            my_item.fmv = estimated_value_of_real_item(my_item)
            db.session.add(my_item)
            db.session.commit()

            # item list cascading updates
            update_item_list_on_real_item_mutation(my_item.item_list_id)
            db.session.commit()

            # transaction cascading updates
            update_transactions_on_real_item_mutation(my_item.database_id)
            db.session.commit()
            ok = True
        except Exception as ex:
            db.session.rollback()
            return UpdateRealItem(real_item=my_item, debug=str(ex))
        else:
            return UpdateRealItem(real_item=my_item, ok=ok)


class DeleteRealItem(Mutation):
    """databaseId is realItemId, deletes realItem from database, deletes corresponding activities from database"""
    class Arguments:
        database_id = Int(required=True)

    ok = Field(Boolean, default_value=False)
    debug = Field(String, default_value="no debug info")

    @user_is_logged_in
    def mutate(root, info, database_id):
        try:
            my_item: RealItems = db.session.query(RealItems).filter_by(database_id=database_id).first()
            item_list_id = my_item.item_list_id

            # permission auth throws exceptions
            real_item_mutation_auth(my_item)

            # business logic auth (status allowed actions)
            real_item_mutation_transaction_auth(my_item)

            # pull transactions and update each of them to not include the deleted real item in their total
            # delete transaction item corresponding to that real item, and then recalculate transaction totals
            update_transactions_on_real_item_mutation(my_item.database_id, mutation='DELETE')
            db.session.commit()

            # delete real item by moving to the trashpile
            my_item.item_list_id = 333
            my_item.owner = 4
            my_item.item_collections_id = 717
            db.session.add(my_item)
            db.session.commit()

            # recalculate item list stats
            update_item_list_on_real_item_mutation(item_list_id)
            update_item_list_on_real_item_mutation(333)
            db.session.commit()
            ok = True
        except Exception as ex:
            db.session.rollback()
            return DeleteRealItem(debug=str(ex))
        return DeleteRealItem(ok=ok)


def delete_stale_transactions(real_item_ids):
    # find old/stale transactions that were never approved by PM, delete them and replace with new transaction
    print(real_item_ids)
    matching_transaction_items = db.session.query(TransactionItems) \
        .filter(TransactionItems.real_item_id.in_(real_item_ids)).all()
    print(matching_transaction_items)
    matching_transactions = [x.transaction_id for x in matching_transaction_items]
    print(matching_transactions)
    stale_statuses = ['CLIENT_REVIEW', 'PURPLEMANA_REVIEW']
    stale_transaction_pointer = db.session.query(Transactions) \
        .filter(Transactions.status.in_(stale_statuses)) \
        .filter(Transactions.database_id.in_(matching_transactions))
    stale_transactions = [x.database_id for x in stale_transaction_pointer.all()]

    db.session.query(TransactionItems) \
        .filter(TransactionItems.transaction_id.in_(stale_transactions)) \
        .delete()
    db.session.query(TransactionLogs) \
        .filter(TransactionLogs.transaction_id.in_(stale_transactions)) \
        .delete()
    db.session.query(Transactions) \
        .filter(Transactions.database_id.in_(stale_transactions)) \
        .delete()

    db.session.commit()


class CreateTransaction(Mutation):
    """should be triggered by user submitting a transaction for review.
    creates a transaction with PURPLEMANA_REVIEW status"""
    class Arguments:
        item_list_id = Int(required=True)

    ok = Field(Boolean, default_value=False)
    transaction = Field(lambda: TransactionsObject)
    debug = Field(String, default_value="no debug info")

    @user_is_logged_in
    def mutate(root, info, item_list_id, **kwargs):

        transaction = TransactionsObject()
        try:
            transaction_logger.debug(f"{session['user_id']} starting new transaction from list {item_list_id}")
            real_items_for_transaction = db.session.query(RealItems).filter_by(item_list_id=item_list_id).all()
            for real_item in real_items_for_transaction:
                if real_item.owner != session['user_id'] and 'administrator' not in session['roles']:
                    raise Exception("user must own items (or be admin) to submit transaction")
            transaction_logger.debug(real_items_for_transaction)
            transaction_logger.debug("processing real items in preparation for transaction"+str(len(real_items_for_transaction)))
            if len(real_items_for_transaction) == 0:
                raise Exception("transaction expects real items for creation")
            item_list = db.session.query(ItemLists).filter_by(database_id=real_items_for_transaction[0].item_list_id).first()
            owner = item_list.user_id

            real_item_ids = [x.database_id for x in real_items_for_transaction]

            delete_stale_transactions(real_item_ids)

            transaction = Transactions()
            transaction.left_owner = owner
            transaction.right_owner = 4
            transaction.date_created = datetime.datetime.now()
            transaction.status = 'PURPLEMANA_REVIEW'
            db.session.add(transaction)
            db.session.commit()

            condition_multipliers = db.session.query(MerchantsConditionMultiplier).filter_by(merchant='PM').all()
            condition_multipliers = {x.condition_id: x.multiplier for x in condition_multipliers}
            for item in real_items_for_transaction:
                try:
                    trade_in_value_NM = item.fmv * (condition_multipliers['NM'] / condition_multipliers[item.condition])
                    if item.fmv < 3.00:
                        continue
                    added_item = TransactionItems(real_item_id=item.database_id, transaction_id=transaction.database_id,
                                          side="left", trade_in_value=item.fmv, trade_in_value_NM=trade_in_value_NM)
                    db.session.add(added_item)
                    db.session.add(item)
                except Exception as ex:
                    print(ex)
                    transaction_logger.debug(f"failed to add item to transaction {item} {str(ex)}")
            db.session.commit()

            transaction.right_credit = round(total_value_of_real_item_list(real_items_for_transaction), 2)
            db.session.add(transaction)

            log = TransactionLogs(transaction_id=transaction.database_id, date_created=datetime.datetime.now(), message=""
                  f"Transaction created by {session['username']} for {len(real_items_for_transaction)} items at {transaction.right_credit}")
            db.session.add(log)
            db.session.commit()

            # integromat content endpoint
            # https://hook.integromat.com/q1x3846bbmscrcrndzitlg7py1n9bsv2
            url = "https://hook.integromat.com/q1x3846bbmscrcrndzitlg7py1n9bsv2"
            params = {
                "user": session['username'],
                "name": item_list.name,
                "url": f"https://juzam.purplemana.com/lists/{str(item_list.database_id)}"
            }
            if os.getenv('FLASK_ENV') == 'production':
                requests.get(url, params=params)
            ok = True
        except Exception as ex:
            print(ex)
            db.session.rollback()
            return CreateTransaction(transaction=transaction, debug=str(ex))
        else:
            return CreateTransaction(transaction=transaction, ok=ok)


class DeleteTransaction(Mutation):
    """required transactionId. only the left_owner can delete the transaction. deletes transaction items as well"""
    class Arguments:
        transaction_id = Int(required=True)

    ok = Field(Boolean, default_value=False)
    debug = Field(String, default_value="no debug info")

    @user_is_logged_in
    def mutate(root, info, transaction_id):
        try:
            transaction_logger.debug(f"deleting {transaction_id} for user {session['user_id']}")
            transaction = db.session.query(Transactions).filter_by(database_id=transaction_id).first()
            if not transaction:
                raise Exception("no transaction found")
            transaction_id = transaction.database_id
            if transaction.left_owner != session['user_id'] and 'administrator' not in session['roles']:
                raise Exception("users cant delete unowned transactions")
            if transaction.status not in ['CLIENT_REVIEW', 'PURPLEMANA_REVIEW'] and 'administrator' not in session['roles']:
                raise Exception("users can't delete transactions approved by PM")
            db.session.query(TransactionItems).filter_by(transaction_id=transaction_id).delete()
            db.session.query(TransactionLogs).filter_by(transaction_id=transaction_id).delete()
            db.session.query(Transactions).filter_by(database_id=transaction_id).delete()
            db.session.commit()
            ok = True
        except Exception as ex:
            db.session.rollback()
            return DeleteTransaction(debug=str(ex))
        else:
            return DeleteTransaction(ok=ok)


class UpdateTransactionStatus(Mutation):
    """requires transactionId.
    transaction status is modeled as a finite state machine, status is capitalized string
    newly created transactions are in PURPLEMANA_REVIEW state
    admin denies -> CLIENT_REVIEW
    admin approves -> TRADEIN_ARRIVING
    admin approves in person -> CREDIT_ISSUED
    if transaction_items / real_items / transaction is modified -> CLIENT_REVIEW
    users can submit transactions CLIENT_REVIEW -> PURPLEMANA_REVIEW
    """
    class Arguments:
        transaction_id = Int(required=True)
        status = String(required=True)
        admin_comment = String()
        testing = Boolean()

    ok = Field(Boolean, default_value=False)
    debug = Field(String, default_value="no debug info")
    transaction = Field(lambda: TransactionsObject)

    @user_is_logged_in
    def mutate(root, info, transaction_id, status, admin_comment=None, testing=False):
        logging.debug(f"in mutation to update {transaction_id} to {status}")
        print("in transaction status mutation")
        transaction = Transactions()
        try:
            transaction: Transactions = db.session.query(Transactions).filter_by(database_id=transaction_id).first()
            if 'administrator' in session['roles']:
                pass
            elif session['user_id'] not in [transaction.left_owner, transaction.right_owner]:
                raise Exception("users can only modify their own transactions")
            transaction_manager = TransactionManager(transaction.database_id)
            if os.getenv('FLASK_ENV') == 'development':
                transaction_manager.update_status(status, testing=testing)
            else:
                transaction_manager.update_status(status)
            if admin_comment:
                transaction.admin_comment = admin_comment
                db.session.add(transaction)
                db.session.commit()
            log = TransactionLogs(transaction_id=transaction.database_id, date_created=datetime.datetime.now(),
                  message=f"Transaction status updated for {session['username']} to {status}'")
            db.session.add(log)
            db.session.commit()
            ok = True
        except Exception as ex:
            db.session.rollback()
            return UpdateTransactionStatus(transaction=transaction, debug=str(ex))
        else:
            return UpdateTransactionStatus(transaction=transaction, ok=ok)


class UpdateTransactionItem(Mutation):
    class Arguments:
        transaction_item_id = Int(required=True)
        admin_price = Float()

    ok = Field(Boolean, default_value=False)
    debug = Field(String, default_value="no debug info")

    @user_is_logged_in
    def mutate(root, info, transaction_item_id, admin_price=None):
        try:
            transaction_item = db.session.query(TransactionItems).filter_by(database_id=transaction_item_id).first()
            transaction = db.session.query(Transactions).filter_by(database_id=transaction_item.transaction_id).first()
            real_item = db.session.query(RealItems).filter_by(database_id=transaction_item.real_item_id).first()

            # permission auth throws exceptions
            real_item_mutation_auth(real_item)

            # business logic auth (status allowed actions)
            real_item_mutation_transaction_auth(real_item)

            if admin_price:
                transaction_item.admin_price = admin_price
                db.session.add(transaction_item)
                db.session.commit()

            if transaction.status in ['CLIENT_REVIEW', 'PURPLEMANA_REVIEW']:
                transaction.status = 'CLIENT_REVIEW'
            transaction.right_credit = total_credit_from_transaction(transaction.database_id)
            db.session.add(transaction)
            log = TransactionLogs(transaction_id=transaction.database_id, date_created=datetime.datetime.now(),
                  message=f"Transaction item {transaction_item.database_id} - {real_item.item_hash} updated by {session['username']} "
                          f"to {admin_price}, new total {transaction.right_credit}")
            db.session.add(log)
            db.session.commit()
            ok = True
        except Exception as ex:
            db.session.rollback()
            return UpdateTransactionItem(debug=str(ex))
        else:
            return UpdateTransactionItem(ok=ok)


class DeleteTransactionItem(Mutation):
    class Arguments:
        transaction_item_id = Int(required=True)

    ok = Field(Boolean, default_value=False)
    debug = Field(String, default_value="no debug info")

    @user_is_logged_in
    def mutate(root, info, transaction_item_id):
        try:
            transaction_item = db.session.query(TransactionItems).filter_by(database_id=transaction_item_id).first()
            transaction = db.session.query(Transactions).filter_by(database_id=transaction_item.transaction_id).first()
            real_item = db.session.query(RealItems).filter_by(database_id=transaction_item.real_item_id).first()

            # permission auth throws exceptions
            real_item_mutation_auth(real_item)

            # business logic auth (status allowed actions)
            real_item_mutation_transaction_auth(real_item)

            db.session.query(TransactionItems).filter_by(database_id=transaction_item_id).delete()
            db.session.commit()

            if transaction.status in ['CLIENT_REVIEW', 'PURPLEMANA_REVIEW']:
                transaction.status = 'CLIENT_REVIEW'
            transaction.right_credit = total_credit_from_transaction(transaction.database_id)
            db.session.add(transaction)
            log = TransactionLogs(transaction_id=transaction.database_id, date_created=datetime.datetime.now(),
                  message=f"Transaction item {transaction_item.database_id} - {real_item.item_hash} deleted by {session['username']}, "
                          f"new total {transaction.right_credit}")
            db.session.add(log)
            db.session.commit()
            ok = True
        except Exception as ex:
            db.session.rollback()
            return DeleteTransactionItem(debug=str(ex))
        else:
            return DeleteTransactionItem(ok=ok)


def record_buy_with_credit_in_transactions(real_item, buyer, seller):
    transaction = Transactions(left_owner=buyer.database_id, right_owner=seller.database_id, date_created=datetime.datetime.now(), left_credit=real_item.forsale_price)
    db.session.add(transaction)
    items = TransactionItems(transaction_id=transaction.database_id, real_item_id=real_item.database_id, side='right')
    db.session.add(items)


class BuyRealItemWithCredit(Mutation):
    class Arguments:
        real_item_id = Int(required=True)

    ok = Field(Boolean, default_value=False)
    debug = Field(String, default_value="no debug info")
    real_item = Field(lambda: RealItemObject)
    user = Field(lambda: UserObject)

    @user_is_logged_in
    def mutate(root, info, real_item_id):
        try:
            buyer: Users = db.session.query(Users).filter_by(database_id=session['user_id']).first()
            item: RealItems = db.session.query(RealItems).filter_by(database_id=real_item_id).first()
            seller: Users = db.session.query(Users).filter_by(database_id=item.owner).first()
            if not item:
                raise Exception(f"no real item found with id {real_item_id}")
            if not item.status == 'PUBLISH':
                raise Exception("that item isn't for sale")
            if buyer.credit < item.forsale_price:
                raise Exception("user does not have enough credit")
            try:
                item_list = db.session.query(ItemLists).filter_by(name="Bought Items").first()
                item_list_id = item_list.database_id
            except:
                item_list = ItemLists(name=f"Bought Items", user_id=session['user_id'], value=0, count=0)
                db.session.add(item_list)
                db.session.commit()
                item_list_id = item_list.database_id

            buyer_collection: ItemCollections = db.session.query(ItemCollections).filter_by(user_id=buyer.database_id).first()
            buyer.credit -= item.forsale_price
            seller.credit += item.forsale_price
            item.status = "SOLD"
            item.item_list_id = item_list_id
            item.owner = buyer.database_id
            item.item_collections_id = buyer_collection.database_id
            item.item_hash = make_item_hash(item)

            record_buy_with_credit_in_transactions(item, buyer, seller)
            update_item_list_on_real_item_mutation(item_list_id)
            if item.item_list_id:
                update_item_list_on_real_item_mutation(item.item_list_id)
            db.session.add(item)
            db.session.add(buyer)
            db.session.add(seller)
            db.session.commit()
            ok = True
        except Exception as ex:
            db.session.rollback()
            return BuyRealItemWithCredit(debug=str(ex))
        else:
            return BuyRealItemWithCredit(ok=ok, user=buyer, real_item=item)

class UpdateRealItemStatus(Mutation):
    """requires transactionId.
    transaction status is modeled as a finite state machine, status is capitalized string
    newly created transactions are in PURPLEMANA_REVIEW state
    admin denies -> CLIENT_REVIEW
    admin approves -> TRADEIN_ARRIVING
    admin approves in person -> CREDIT_ISSUED
    if transaction_items / real_items / transaction is modified -> CLIENT_REVIEW
    users can submit transactions CLIENT_REVIEW -> PURPLEMANA_REVIEW
    """
    class Arguments:
        real_item_id = Int(required=True)
        status = String(required=True)
        admin_comment = String()

    ok = Field(Boolean, default_value=False)
    debug = Field(String, default_value="no debug info")
    real_item = Field(lambda: RealItemObject)

    @user_is_logged_in
    def mutate(root, info, real_item_id, status, admin_comment=None):
        logging.debug(f"in mutation to update {real_item_id} to {status}")
        my_real_item = RealItems()
        try:
            my_real_item: RealItems = db.session.query(RealItems).filter_by(database_id=real_item_id).first()
            if 'administrator' in session['roles']:
                pass
            elif session['user_id'] != my_real_item.owner:
                raise Exception("users can only modify their own items")

            item_manager = ItemManager(my_real_item.database_id)
            item_manager.update_status(status)
            ok = True
        except Exception as ex:
            db.session.rollback()
            return UpdateRealItemStatus(real_item=my_real_item, debug=str(ex))
        else:
            return UpdateRealItemStatus(real_item=my_real_item, ok=ok)

class CreateUpdateListingFeedback(Mutation):
    class Arguments:
        ebaylisting_id = Int(required=True)
        is_correct = Boolean(required=True)
        user_comment = String()
        user_selected_generic_id = Int() #This is not required in case user has not selected any card/has choseon WRONG to all predictions
        
    ok = Field(Boolean, default_value=False)
    debug = Field(String, default_value="no debug info")
    listing_feedback = Field(lambda: ListingFeedbackObject)

    @staticmethod
    @user_is_logged_in
    def mutate(root, info, ebaylisting_id, is_correct, user_selected_generic_id=None, user_comment=None):
        def get_one_or_create(model: ListingFeedback,
                        create_method='',
                        create_method_kwargs=None,
                        **kwargs):
            try:
                return db.session.query(model).filter_by(**kwargs).one(), True
            except NoResultFound:
                kwargs.update(create_method_kwargs or {})
                created = getattr(model, create_method, model)(**kwargs)
                try:
                    db.session.add(created)
                    db.session.commit()
                    return created, False
                except exc.IntegrityError:
                    db.session.rollback()
                    return db.session.query(model).filter_by(**kwargs).one(), True
            
            except MultipleResultsFound:
                return db.session.query(model).filter_by(**kwargs).first(), False


        try: #Create new listing feedback
            listing_feedback, retval = get_one_or_create(ListingFeedback, 
                user_id=session['user_id'], listing_id = ebaylisting_id,
                create_method_kwargs= {
                    'user_comment': user_comment,
                    'is_correct': is_correct,
                    'user_selected_generic_id': user_selected_generic_id
                })

            if listing_feedback: # Was able to retreive existing entry
                #Update the parameters
                listing_feedback.user_comment = user_comment
                listing_feedback.is_correct = is_correct
                listing_feedback.user_selected_generic_id = user_selected_generic_id
                db.session.commit()

        except Exception as e:
            db.session.rollback()
            return CreateUpdateListingFeedback(debug=str(e), ok=False)

        return CreateUpdateListingFeedback(ok=True, debug=f'Created/Updated Listing Feedback with id {listing_feedback.database_id}')


class CreateTransactionLog(Mutation):
    """for user/admin to directly submit log to transactionLog - takes transactionId and message as required inputs"""
    class Arguments:
        transaction_id = Int(required=True)
        message = String(required=True)

    ok = Field(Boolean, default_value=False)
    transaction_logs = Field(lambda: TransactionLogObject)
    debug = Field(String, default_value="no debug info")

    @user_is_logged_in
    def mutate(root, info, transaction_id, message):
        log = TransactionLogs()
        try:
            transaction = db.session.query(Transactions).filter_by(database_id=transaction_id).first()
            if 'administrator' in session['roles']:
                pass
            elif session['user_id'] not in [transaction.left_owner, transaction.right_owner]:
                raise Exception("users can only modify their own transactions")
            log = TransactionLogs(transaction_id=transaction_id, message=message, date_created=datetime.datetime.now())
            db.session.add(log)
            db.session.commit()
            ok = True
        except Exception as ex:
            print(ex)
            db.session.rollback()
            return CreateTransactionLog(transaction_logs=log, debug=str(ex))
        else:
            return CreateTransactionLog(transaction_logs=log, ok=ok)
