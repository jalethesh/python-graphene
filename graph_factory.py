import graphene
from graphene import String, Int, Boolean, Mutation, Field, ObjectType, List, NonNull
from graphene_sqlalchemy import SQLAlchemyConnectionField
from models.data_models import ListingFeedback, SetModel, GenericItems, LatestOffers, LatestOffersHistory, Users, ItemCollections, \
    RealItems, db, ItemLists, EbayListing
from flask import Blueprint
from graphql_service import *

graph_factory = Blueprint("graph_factory", __name__, static_folder="static", template_folder="templates")

# all queries accessible by client are listed here
class Query(graphene.ObjectType):
    """perPage pagination argument has a built in hard limit of 1000"""
    sets = List(SetObject, set_code=String(), partial_name=String(), page=Int(), per_page=Int(),
                description="filterable by set_code, paginated with page/perPage arguments")

    def resolve_sets(self, info, set_code=None, partial_name=None, page=0, per_page=100):
        query = SetObject.get_query(info)  # SQLAlchemy query
        return get_sets(query, set_code, partial_name, page, per_page)

    offers = List(OfferObject, scryfall_card_id=String(), generic_item_id=Int(), start_date=String(), max_entries=Int(),
                  description="pulls data from full offers table, custom resolver is implemented to return "
                              "PM time series through offersHistory subquery")

    def resolve_offers(self, info, scryfall_card_id=None, generic_item_id=None):
        # this resolver is pointing to latestOffers and latestOffersHistory
        # Offers and OffersHistory are the full data set, where latest are just the single latest offer for an item
        query = OfferObject.get_query(info)  # SQLAlchemy query
        return get_offers(query, scryfall_card_id, generic_item_id)

    latest_offers = List(LatestOfferObject, scryfall_card_id=String(), generic_item_id=Int(),
                         description="filters by scryfallCardId and genericItemId if provided. "
                                     "Always returns a single offer")

    def resolve_latest_offers(self, info, scryfall_card_id=None, generic_item_id=None):
        # this resolver is pointing to latestOffers and latestOffersHistory
        # Offers and OffersHistory are the full data set, where latest are just the single latest offer for an item
        print("hitting offer resolver")
        query = LatestOfferObject.get_query(info)  # SQLAlchemy query
        return get_latest_offers(query, scryfall_card_id, generic_item_id)

    item_collections = List(ItemCollectionObject, user_id=Int(), name=String(), collection_id=Int(), trashed=Boolean(),
                            order_status=String(), page=Int(), per_page=Int(), description="filters by user_id, name, "
                            "collection_id, trashed, order_status. paginated with page/perPage arguments. if a userId "
                            "isn't provided, defaults to user determined by session, only admin has access to view "
                            "other users collection.")

    def resolve_item_collections(self, info, user_id=0, name=None, trashed=None, collection_id=None, order_status=None, page=0, per_page=100):
        query = ItemCollectionObject.get_query(info)
        return get_item_collections(query, user_id, name, trashed, collection_id, order_status, page, per_page)

    item_lists = List(ItemListsObject, user_id=Int(), name=String(), item_list_id=Int(),
                            page=Int(), per_page=Int(), description="filters by user_id, name, "
                            "collection_id, trashed, order_status. paginated with page/perPage arguments. if a userId "
                            "isn't provided, defaults to user determined by session, only admin has access to view "
                            "other users collection.")

    def resolve_item_lists(self, info, user_id=0, name=None, item_list_id=None, page=0, per_page=100):
        query = ItemListsObject.get_query(info)
        return get_item_lists(query, user_id, name, item_list_id, page, per_page)

    top_item_lists = List(ItemListsObject, page=Int(), per_page=Int(), description="ordered by total value")

    def resolve_top_item_lists(self, info):
        query = ItemListsObject.get_query(info)
        return get_ranked_item_lists(query)

    real_items = List(RealItemObject, real_item_id=Int(), collection_id=Int(), status=String(), user_id=Int(),
                      item_list_id=Int(), partial_name=String(), sort_key=String(), sort_reverse=Boolean(),
                      page=Int(), per_page=Int(), description="filtered by "
                      "collection_id, userId (owner), paginated with page/perPage. sortKey values are: fmv and "
                      "item_hash")

    def resolve_real_items(self, info, real_item_id=None, collection_id=None, status=None, user_id=None,
                           item_list_id=None, partial_name=None, sort_key=None, sort_reverse=None, page=0, per_page=100):
        query = RealItemObject.get_query(info)  # SQLAlchemy query
        return get_real_items(query, real_item_id, collection_id, status, user_id, item_list_id, partial_name, sort_key,
                              sort_reverse, page, per_page)

    user = Field(UserObject, user_id=Int(), description="filterable by user_id, can only pull information about other "
                 "users as admin")

    def resolve_user(self, info, user_id=0):
        query = db.session.query(Users)
        return get_user(query, user_id)

    generic_items = List(GenericItemObject, database_id=List(Int), set_code=String(), scryfall_card_id=String(), item_index=String(),
                         partial_name=String(), page=Int(), per_page=Int(), description="filterable by set_code, "
                         "scryfallCardId, itemIndex, and partialName. partialName finds genericItems with names like "
                         "%partialName% and is case insensitive")

    def resolve_generic_items(self, info, database_id=None, set_code=None, set_name=None, scryfall_card_id=None, item_index=None, partial_name=None,
                              page=0, per_page=100):
        query = GenericItemObject.get_query(info)
        return get_generic_items(query, database_id, set_code, set_name, scryfall_card_id, item_index, partial_name, page, per_page)
 
    generic_item_names = List(String, description="pulls list of all names from genericItems, then removes duplicates")

    def resolve_generic_item_names(self, info):
        generic_item_name_list = db.session.query(GenericItems.name).all()
        print(generic_item_name_list[0], type(generic_item_name_list[0]))
        generic_item_name_list = [x[0] for x in list(set(generic_item_name_list)) if 'UPDATE ME' not in x[0]]
        generic_item_name_list.sort()
        return generic_item_name_list

    activities = List(ActivitiesObject, page=Int(), per_page=Int())

    def resolve_activities(self, info, page=0, per_page=100):
        query = ActivitiesObject.get_query(info)
        return get_activities(query, page, per_page)

    subscriptions = List(SubscriptionsObject)

    def resolve_subscriptions(self, info):
        query = SubscriptionsObject.get_query(info)
        return get_subscriptions(query)

    defects = List(DefectsObject, real_item_id=Int(), page=Int(), per_page=Int())
    
    def resolve_defects(self, info, real_item_id=0, page=0, per_page=100):
        query = DefectsObject.get_query(info)
        return get_defects(query, real_item_id, page, per_page)

    media = List(MediaObject, real_item_id=Int(), page=Int(), per_page=Int(), description="filter by realItemId")

    def resolve_media(self, info, real_item_id=0, page=0, per_page=100):
        query = MediaObject.get_query(info)
        return get_media(query, real_item_id, page, per_page)

    conditions = List(ConditionsObject, description="list of conditions is small and query simply returns all")

    def resolve_conditions(self, info):
        query = ConditionsObject.get_query(info)
        return get_conditions(query)

    transactions = List(TransactionsObject, transaction_id=Int(), user_id=Int(), collection_id=Int(), status=String(),
                        status_array=List(String), sort_option=String(), sort_mode=String(),
                        page=Int(), per_page=Int(),
                        description="filter by transactionId, userId, collectionId transaction status, "
                                    "sort_option can take on these values: dateCreated, dateUpdated, rightCredit,"
                                    "sort_mode can take on 'asc' or 'desc' ")

    def resolve_transactions(self, info, transaction_id=None, user_id=None, status=None, status_array=None,
                             sort_option=None, sort_mode=None,
                             page=0, per_page=100):
        query = TransactionsObject.get_query(info)
        return get_transactions(query, transaction_id, user_id, status, status_array, sort_option, sort_mode, page, per_page)

    transaction_logs = List(TransactionLogObject, transaction_id=Int(), page=Int(), per_page=Int(),
                            description="filter by transactionId, page, perPage")

    def resolve_transaction_logs(self, info, transaction_id=None, page=0, per_page=100):
        query = TransactionLogObject.get_query(info)
        return get_transaction_logs(query, transaction_id, page, per_page)

    transaction_items = List(TransactionItemObject, transaction_id=Int(), page=Int(), per_page=Int(),
                             description="filter by transactionId")

    def resolve_transaction_items(self, info, transaction_id=None, page=0, per_page=100):
        query = TransactionItemObject.get_query(info)
        return get_transaction_items(query, transaction_id, page, per_page)
    
    merchants_condition_multiplier = List(MerchantsConditionMultiplierObject, description="")

    def resolve_merchants_condition_multiplier(self, info):
        query = MerchantsConditionMultiplierObject.get_query(info)
        return get_merchant_condition_multipliers(query)

    count_published = Int()

    def resolve_count_published(self, info):
        query = RealItemObject.get_query(info)
        query = query.filter_by(status="PUBLISH")
        return query.count()

    ebay_listing = List(EbayListingObject, database_id=Int(), has_prediction=Boolean(), winning_bid_sort=Boolean(), page=Int(), per_page=Int(),
        description="Get Ebay listings. Filterable by database_id")

    def resolve_ebay_listing(self, info, database_id=None, has_prediction=None, winning_bid_sort=False, page=0, per_page=100):
        query = EbayListingObject.get_query(info)
        return get_ebay_listing(query, database_id, has_prediction, winning_bid_sort, page, per_page)
         
    listing_feedback = List(ListingFeedbackObject, user_id=Int(), page=Int(), per_page=Int(),
        description = "filterable by user_id, paginated with page/perPage arguments")

    def resolve_listing_feedback(self, info, user_id=None, page=0, per_page=100):
        query = ListingFeedbackObject.get_query(info)
        return get_listing_feedback(query, user_id, page, per_page)

    # wrapping an external api
    shippo_quotes = List(ShippoQuoteObject, user_id=Int())

    def resolve_shippo_quotes(self, info, user_id=None):
        user = db.session.query(Users).filter_by(database_id=user_id).first()
        return get_shippo_quotes(user)


class Mutations(ObjectType):
    create_generic_item = CreateGenericItem.Field()
    update_generic_item = UpdateGenericItem.Field()
    delete_generic_item = DeleteGenericItem.Field()
    create_real_item = CreateRealItem.Field()
    update_real_item = UpdateRealItem.Field()
    delete_real_item = DeleteRealItem.Field()
    create_media = CreateMedia.Field()
    update_media = UpdateMedia.Field()
    delete_media = DeleteMedia.Field()
    create_transaction = CreateTransaction.Field()
    delete_transaction = DeleteTransaction.Field()
    update_transaction_status = UpdateTransactionStatus.Field()
    delete_transaction_item = DeleteTransactionItem.Field()
    create_item_list = CreateItemList.Field()
    update_item_list = UpdateItemList.Field()
    delete_item_list = DeleteItemList.Field()
    update_user = UpdateUser.Field()
    buy_real_item_with_credit = BuyRealItemWithCredit.Field()
    update_real_item_status = UpdateRealItemStatus.Field()
    create_update_listing_feedback = CreateUpdateListingFeedback.Field()
    create_transaction_log = CreateTransactionLog.Field()
schema = graphene.Schema(query=Query, mutation=Mutations)

