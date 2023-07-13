import json

from graphene_sqlalchemy import SQLAlchemyObjectType
import sqlalchemy

from .queries import get_real_items, unfiltered_get_real_items
from models.data_models import GenericItems, RealItems, Media, ItemCollections, ItemLists, OffersHistory, Offers, \
    LatestOffersHistory, LatestOffers, OffersTimeSeries, db, SetModel, Users, Conditions, Merchants, Activities, \
    Subscriptions, Defects, MerchantsConditionMultiplier, TransactionItems, Transactions, TransactionLogs, EbayListing, \
    ListingFeedback
from graphene import relay, List, Int, ObjectType, Field, String, Boolean, Float
from graphene_sqlalchemy import SQLAlchemyConnectionField
from .util import paginate, ShippoQuote
import graphene
import dateutil.parser as dparser


class GenericItemObject(SQLAlchemyObjectType):
    class Meta:
        model = GenericItems
        interfaces = (relay.Node, )


class SetObject(SQLAlchemyObjectType):
    class Meta:
        model = SetModel
        interfaces = (relay.Node, )
    generic_items = SQLAlchemyConnectionField(GenericItemObject)

    def resolve_generic_items(self, info):
        # print(f"hitting generic resolver {dir(self)} {self.scryfall_card_id} :")
        query = GenericItemObject.get_query(info)
        query = query.filter(GenericItems.set == self.code)
        return query.all()


class RealItemObject(SQLAlchemyObjectType):
    class Meta:
        model = RealItems
        interfaces = (relay.Node, )

    generic_items = SQLAlchemyConnectionField(GenericItemObject)

    def resolve_generic_items(self, info):
        query = GenericItemObject.get_query(info)
        query = query.filter(GenericItems.id == self.item_id)
        return query.all()

    media_count = Int()

    def resolve_media_count(self, info):
        query = MediaObject.get_query(info)
        total = query.filter(Media.realitem_id == self.database_id).count()
        return total


# Graphene wrappers for our sqlalchemy objects
class ItemCollectionObject(SQLAlchemyObjectType):
    class Meta:
        model = ItemCollections
        interfaces = (relay.Node,)

    count = Int()

    def resolve_count(self, info):
        query = RealItemObject.get_query(info)
        query = query.filter(RealItems.item_collections_id == self.database_id)
        return query.count()

    real_items = SQLAlchemyConnectionField(RealItemObject, page=Int(), per_page=Int())

    def resolve_real_items(self, info, page=0, per_page=20):
        # print(f"hitting generic resolver {dir(self)} {self.scryfall_card_id} :")
        query = RealItemObject.get_query(info)
        query = query.filter(RealItems.item_collections_id == self.database_id)
        return paginate(query, RealItems.database_id, page, per_page)

    lists = List(graphene.String, )

    def resolve_lists(self, info):
        query = RealItemObject.get_query(info)
        real_items = query.filter(RealItems.item_collections_id == self.database_id).all()
        return list(set([x.user_list for x in real_items]))


class ItemListsObject(SQLAlchemyObjectType):
    class Meta:
        model = ItemLists
        interfaces = (relay.Node,)

    real_items = SQLAlchemyConnectionField(RealItemObject,  status=String(), user_id=Int(), partial_name=String(), sort_key=String(),
                      sort_reverse=Boolean(), page=Int(), per_page=Int())

    def resolve_real_items(self, info, status=None, user_id=None, partial_name=None, sort_key=None, sort_reverse=True,
                           page=0, per_page=100):
        query = RealItemObject.get_query(info)  # SQLAlchemy query
        return unfiltered_get_real_items(query, None, None, status, user_id, self.database_id, partial_name, sort_key,
                              sort_reverse, page, per_page)


class OfferHistoryObject(SQLAlchemyObjectType):
    class Meta:
        model = OffersHistory
        interfaces = (relay.Node, )


class OfferObject(SQLAlchemyObjectType):
    class Meta:
        model = Offers
        interfaces = (relay.Node, )

    offers_history = SQLAlchemyConnectionField(OfferHistoryObject)

    def resolve_offers_history(self, info):
        query = OfferHistoryObject.get_query(info)
        query = query.filter(OffersHistory.offers_id == self.id)
        return query.all()

    # this by default gives all generic cards, so we have a resolver implemented below
    generic_items = SQLAlchemyConnectionField(GenericItemObject)

    # default resolver doesnt filter by Offers.item_id, probably due to relationship
    def resolve_generic_items(self, info):
        # print(f"hitting generic resolver {dir(self)} {self.scryfall_card_id} :")
        query = GenericItemObject.get_query(info)
        query = query.filter(GenericItems.id == self.item_id)
        return query.all()


class LatestOfferHistoryObject(SQLAlchemyObjectType):
    class Meta:
        model = LatestOffersHistory
        interfaces = (relay.Node, )


class LatestOfferObject(SQLAlchemyObjectType):
    class Meta:
        model = LatestOffers
        interfaces = (relay.Node, )
    latest_offers_history = SQLAlchemyConnectionField(LatestOfferHistoryObject)

    def resolve_latest_offers_history(self, info):
        query = LatestOfferHistoryObject.get_query(info)
        query = query.filter(LatestOffersHistory.offers_id == self.database_id)
        return query.all()

    # this by default gives all generic cards, so we have a resolver implemented below
    generic_items = SQLAlchemyConnectionField(GenericItemObject)

    # default resolver doesnt filter by Offers.item_id, probably due to relationship
    def resolve_generic_items(self, info):
        # print(f"hitting generic resolver {dir(self)} {self.scryfall_card_id} :")
        query = GenericItemObject.get_query(info)
        query = query.filter(GenericItems.id == self.item_id)
        return query.all()

    time_series = List(OfferHistoryObject)

    def resolve_time_series(self, info):
        series_row = db.session.query(OffersTimeSeries).filter_by(item_id=self.item_id).first()
        data = json.loads(series_row.history)
        result = []
        for history in data:
            date = dparser.parse(history['last_updated'], fuzzy=True)
            if history['merchant'] == 'PM':
                result.append(OffersHistory(id=history['id'], merchant=history['merchant'],
                                        amount=history['amount'], last_updated=date))
        return result[::-1]


class UserObject(SQLAlchemyObjectType):
    class Meta:
        model = Users
        interfaces = (relay.Node, )
        exclude_fields = ('token', 'expiration', 'password', 'cognito_id', 'wordpress_id', )

    item_collections = SQLAlchemyConnectionField(ItemCollectionObject)

    def resolve_item_collections(self, info):
        query = ItemCollectionObject.get_query(info)
        query = query.filter(ItemCollections.user_id == self.database_id)
        return query.all()


class ConditionsObject(SQLAlchemyObjectType):
    class Meta:
        model = Conditions
        interfaces = (relay.Node, )


class MerchantsObject(SQLAlchemyObjectType):
    class Meta:
        model = Merchants
        interfaces = (relay.Node, )


class ActivitiesObject(SQLAlchemyObjectType):
    class Meta:
        model = Activities
        interfaces = (relay.Node, )


class SubscriptionsObject(SQLAlchemyObjectType):
    class Meta:
        model = Subscriptions
        interfaces = (relay.Node, )


class MediaObject(SQLAlchemyObjectType):
    class Meta:
        model = Media
        interfaces = (relay.Node, )


class DefectsObject(SQLAlchemyObjectType):
    class Meta:
        model = Defects
        interfaces = (relay.Node, )


class MerchantsConditionMultiplierObject(SQLAlchemyObjectType):
    class Meta:
        model = MerchantsConditionMultiplier
        interfaces = (relay.Node, )


class TransactionItemObject(SQLAlchemyObjectType):
    class Meta:
        model = TransactionItems
        interfaces = (relay.Node, )

    real_items = SQLAlchemyConnectionField(RealItemObject)

    def resolve_real_items(self, info):
        # print(f"hitting generic resolver {dir(self)} {self.scryfall_card_id} :")
        query = RealItemObject.get_query(info)
        query = query.filter(RealItems.database_id == self.real_item_id)
        return query.all()


class TransactionsObject(SQLAlchemyObjectType):
    class Meta:
        model = Transactions
        interfaces = (relay.Node, )

    transaction_items = SQLAlchemyConnectionField(TransactionItemObject)

    def resolve_transaction_items(self, info):
        # print(f"hitting generic resolver {dir(self)} {self.scryfall_card_id} :")
        query = TransactionItemObject.get_query(info)
        query = query.filter(TransactionItems.transaction_id == self.database_id)
        return query.all()

    count = Int()

    def resolve_count(self, info):
        query = TransactionItemObject.get_query(info)
        query = query.filter(TransactionItems.transaction_id == self.database_id)
        return query.count()

    user = Field(UserObject)

    def resolve_user(self, info):
        # print(f"hitting generic resolver {dir(self)} {self.scryfall_card_id} :")
        query = UserObject.get_query(info)
        user = query.filter(Users.database_id == self.left_owner).first()
        return user


class EbayListingObject(SQLAlchemyObjectType):
    class Meta:
        model = EbayListing
        interfaces = (relay.Node, ) 


class ListingFeedbackObject(SQLAlchemyObjectType):
    class Meta:
        model = ListingFeedback


class TransactionLogObject(SQLAlchemyObjectType):
    class Meta:
        model = TransactionLogs
        interfaces = (relay.Node, )



from graphene import ObjectType
class ShippoQuoteObject(ObjectType):
    class Meta:
        model = ShippoQuote
    amount = Float()
    estimated_days = Int()
    provider = String()
    name = String()
    token = String()
