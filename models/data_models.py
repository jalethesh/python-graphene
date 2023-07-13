from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_restful import Api
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import String, Boolean, Integer, DateTime, Date, func

api = Api()
ma = Marshmallow()
db = SQLAlchemy()
Base = declarative_base()


class SetModel(db.Model):
    __tablename__ = 'sets'

    id = db.Column(db.Integer, primary_key=True, unique=True)
    scryfall_set_id = db.Column(db.String(), unique=True)
    code = db.Column(db.String(), unique=True)
    mtgo_code = db.Column(db.String())
    arena_code = db.Column(db.String())
    tcgplayer_id = db.Column(db.Integer())
    name = db.Column(db.String())
    uri = db.Column(db.String())
    scryfall_uri = db.Column(db.String())
    search_uri = db.Column(db.String())
    released_at = db.Column(db.Date())
    set_type = db.Column(db.String())
    digital = db.Column(db.Boolean())
    nonfoil_only = db.Column(db.Boolean())
    foil_only = db.Column(db.Boolean())
    icon_svg_uri = db.Column(db.String())

    def __repr__(self):
        return '<Set %r>' % self.name


class GenericItems(db.Model):
    __tablename__ = 'generic_items'

    id = db.Column(db.Integer, primary_key=True, unique=True)
    oracle_id = db.Column(db.String())
    multiverse_ids = db.Column(db.String())
    mtgo_id = db.Column(db.String())
    produced_mana = db.Column(db.String())
    mtgo_foil_id = db.Column(db.String())
    scryfall_card_id = db.Column(db.String())
    legalities = db.Column(db.String())
    full_art = db.Column(db.Boolean())
    textless = db.Column(db.Boolean())
    loyalty = db.Column(db.String())
    oversized = db.Column(db.Boolean())
    frame = db.Column(db.String())
    card_back_id = db.Column(db.String())
    games = db.Column(db.String())
    lang = db.Column(db.String())
    name = db.Column(db.String())
    uri = db.Column(db.String())
    rarity = db.Column(db.String())
    variation = db.Column(db.String())
    variation_of = db.Column(db.String())
    layout = db.Column(db.String())
    scryfall_uri = db.Column(db.String())
    cmc = db.Column(db.Float())
    cardmarket_id = db.Column(db.String())
    tcgplayer_id = db.Column(db.String())
    color_identity = db.Column(db.String())
    colors = db.Column(db.String())
    keywords = db.Column(db.String())
    image_uris = db.Column(db.String())
    foil = db.Column(db.Boolean())
    nonfoil = db.Column(db.Boolean())
    etchedfoil = db.Column(db.Boolean())    
    mana_cost = db.Column(db.String())
    oracle_text = db.Column(db.String())
    power = db.Column(db.String())
    reserved = db.Column(db.Boolean())
    toughness = db.Column(db.String())
    type_line = db.Column(db.String())
    artist = db.Column(db.String())
    booster = db.Column(db.String())
    border_color = db.Column(db.String())
    collector_number = db.Column(db.String())
    flavor_name = db.Column(db.String())
    flavor_text = db.Column(db.String())
    illustration_id = db.Column(db.String())
    printed_name = db.Column(db.String())
    printed_text = db.Column(db.String())
    printed_type_line = db.Column(db.String())
    promo = db.Column(db.Boolean(), default=False)
    purchase_uris = db.Column(db.String())
    released_at = db.Column(db.Date())
    scryfall_set_uri = db.Column(db.String())
    set_name = db.Column(db.String())
    set_search_uri = db.Column(db.String())
    set_type = db.Column(db.String())
    set_uri = db.Column(db.String())
    set = db.Column(db.String())
    image_uri_small = db.Column(db.String())
    image_uri_normal = db.Column(db.String())
    image_uri_large = db.Column(db.String())
    image_uri_png = db.Column(db.String())
    item_index = db.Column(db.String(), unique=True)
    scryfall_set_id = db.Column(db.String, db.ForeignKey('sets.scryfall_set_id'), nullable=False)
    offers = db.relationship('Offers', back_populates='item')
    latest_offers = db.relationship('LatestOffers', back_populates='item')
    original_name = db.Column(db.String())
    item_hash = db.Column(db.String())

    def __repr__(self):
        return '<Item Index %r>' % self.item_index

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class Offers(db.Model):
    __tablename__ = 'offers'

    id = db.Column(db.Integer, primary_key=True, unique=True, nullable=False)
    scryfall_card_id = db.Column(db.String())
    item_index = db.Column(db.String())
    last_updated = db.Column(db.Date(), default=func.now())
    item_id = db.Column(db.Integer(), db.ForeignKey('generic_items.id'))
    item = db.relationship('GenericItems', back_populates='offers')
    offers_history = db.relationship('OffersHistory', back_populates='offers')
    condition = db.Column(db.String(), db.ForeignKey('conditions.us_code'), default='NM')

    def __repr__(self):
        return f"<Offers {self.id}"


class LatestOffers(db.Model):
    __tablename__ = 'latest_offers'

    database_id = db.Column(db.Integer, primary_key=True, unique=True, nullable=False)
    scryfall_card_id = db.Column(db.String())
    item_index = db.Column(db.String())
    last_updated = db.Column(db.Date(), default=func.now())
    item_id = db.Column(db.Integer(), db.ForeignKey('generic_items.id'))
    item = db.relationship('GenericItems', back_populates='latest_offers')
    condition = db.Column(db.String(), db.ForeignKey('conditions.us_code'), default='NM')

    def __repr__(self):
        return f"<LatestOffers {self.database_id}"


class Conditions(db.Model):
    __tablename__ = 'conditions'

    us_code = db.Column(db.String(), primary_key=True, unique=True)
    eu_code = db.Column(db.String())
    date_updated = db.Column(db.DateTime(), default=db.func.current_timestamp())
    type = db.Column(db.String())
    sort_order = db.Column(db.Integer(), default=0)

    def __repr__(self):
        return f"<Conditions {self.us_code}"


class OffersHistory(db.Model):
    __tablename__ = 'offers_history'

    id = db.Column(db.Integer, primary_key=True, unique=True)
    scryfall_card_id = db.Column(db.String())
    last_updated = db.Column(db.DateTime(), default=db.func.current_timestamp())
    source = db.Column(db.String())
    merchant = db.Column(db.String(), db.ForeignKey('merchants.shortcode'))
    amount = db.Column(db.Float())
    card_type = db.Column(db.String())
    condition = db.Column(db.String(), db.ForeignKey('conditions.us_code'))
    offers_id = db.Column(db.Integer(), db.ForeignKey('offers.id'))
    offers = db.relationship('Offers', back_populates='offers_history', cascade='delete,all')

    def __repr__(self):
        return f"<OffersHistory {self.id}>"


class LatestOffersHistory(db.Model):
    __tablename__ = 'latest_offers_history'

    database_id = db.Column(db.Integer, primary_key=True, unique=True)
    scryfall_card_id = db.Column(db.String())
    last_updated = db.Column(db.DateTime(), default=db.func.current_timestamp())
    source = db.Column(db.String())
    merchant = db.Column(db.String(), db.ForeignKey('merchants.shortcode'))
    amount = db.Column(db.Float())
    card_type = db.Column(db.String())
    condition = db.Column(db.String(), db.ForeignKey('conditions.us_code'))
    offers_id = db.Column(db.Integer(), db.ForeignKey('latest_offers.database_id'))

    def __repr__(self):
        return f"<LatestOffersHistory {self.database_id}>"


class Merchants(db.Model):
    __tablename__ = 'merchants'

    shortcode = db.Column(db.String(), primary_key=True, unique=True, nullable=False)
    name = db.Column(db.String())
    city = db.Column(db.String())
    state = db.Column(db.String())
    country = db.Column(db.String())
    date_created = db.Column(db.DateTime(), default=db.func.current_timestamp())
    website = db.Column(db.String())


class MerchantsConditionMultiplier(db.Model):
    __tablename__ = 'merchants_condition_multiplier'

    database_id = db.Column(db.Integer, primary_key=True, unique=True)
    merchant = db.Column(db.String(), db.ForeignKey("merchants.shortcode"))
    condition_id = db.Column(db.String(), db.ForeignKey("conditions.us_code"))
    multiplier = db.Column(db.Float())


class Users(db.Model):
    __tablename__ = 'users'
    database_id = db.Column(db.Integer(), primary_key=True, unique=True)
    username = db.Column(db.String(), unique=True)
    security_role = db.Column(db.String())
    token = db.Column(db.String())
    expiration = db.Column(db.Integer())
    wordpress_id = db.Column(db.Integer(), unique=True)
    credit = db.Column(db.Float())
    password = db.Column(db.String())
    email = db.Column(db.String(), unique=True)
    address_line_one = db.Column(db.String())
    address_line_two = db.Column(db.String())
    address_state = db.Column(db.String())
    address_city = db.Column(db.String())
    address_country = db.Column(db.String())
    address_zipcode = db.Column(db.String())
    phone_number = db.Column(db.String())
    real_name = db.Column(db.String())
    view_mode = db.Column(db.String())
    color_theme = db.Column(db.String())
    per_page = db.Column(db.Integer())
    date_created = db.Column(db.DateTime())
    date_updated = db.Column(db.DateTime())
    last_login = db.Column(db.DateTime())
    cognito_id = db.Column(db.String())


class ItemCollections(db.Model):
    __tablename__ = 'item_collections'
    database_id = db.Column(db.Integer(), primary_key=True, unique=True)
    user_id = db.Column(db.Integer(), db.ForeignKey("users.database_id"))
    name = db.Column(db.String())
    public = db.Column(db.Boolean())
    date_created = db.Column(db.DateTime(), default=func.now())
    date_updated = db.Column(db.DateTime())
    trashed = db.Column(db.Boolean())
    order_status = db.Column(db.String())
    admin_approved = db.Column(db.Boolean())
    admin_comment = db.Column(db.String())
    real_items = db.relationship('RealItems', cascade="all, delete-orphan")
    cover_photo_item = db.relationship('RealItems', viewonly=True)

    def as_dict(self):
        return {"database_id": self.database_id, "user_id": self.user_id, "name": self.name, "public": self.public}


class RealItems(db.Model):
    __tablename__ = 'real_items'
    database_id = db.Column(db.Integer(), primary_key=True, unique=True)
    item_collections_id = db.Column(db.Integer(), db.ForeignKey("item_collections.database_id", ondelete="CASCADE"))
    item_id = db.Column(db.Integer(), db.ForeignKey("generic_items.id"))
    sku = db.Column(db.String())
    creator = db.Column(db.Integer(), db.ForeignKey("users.database_id"))
    owner = db.Column(db.Integer(), db.ForeignKey("users.database_id"))
    date_created = db.Column(db.Date(), default=func.now())
    date_updated = db.Column(db.Date())
    condition = db.Column(db.String, db.ForeignKey('conditions.us_code'), nullable=True)
    cost_basis = db.Column(db.Float())
    fmv = db.Column(db.Float())
    trade_in_value = db.Column(db.Float())
    woocommerce_url = db.Column(db.String())
    woocommerce_product_id = db.Column(db.Integer())
    forsale_price = db.Column(db.Float())
    media = db.relationship('Media', cascade="all, delete-orphan", back_populates='realitem')
    defects = db.relationship('Defects', back_populates='realitem')
    status = db.Column(db.String())
    transaction_status = db.Column(db.String())
    user_list = db.Column(db.String(), default="default")
    item_list_id = db.Column(db.Integer(), db.ForeignKey('item_lists.database_id'))
    item_hash = db.Column(db.String())
    qr_url = db.Column(db.String())
    qr_label_url = db.Column(db.String())
    recent_transaction = db.Column(db.Integer())

    def as_dict(self):
        return {"database_id": self.database_id, "item_collections_id": self.item_collections_id,
                "item_id": self.item_id, "owner": self.owner, "condition": self.condition,
                "forsale_price": self.forsale_price}


class Defects(db.Model):
    __tablename__ = 'real_items_defects'
    database_id = db.Column(db.Integer(), primary_key=True, unique=True)
    defect_name = db.Column(db.String())
    realitem_id = db.Column(db.Integer, db.ForeignKey('real_items.database_id'), nullable=False)
    realitem = db.relationship("RealItems", back_populates="defects")

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class Media(db.Model):
    __tablename__ = 'media'
    database_id = db.Column(db.Integer(), primary_key=True, unique=True)
    type = db.Column(db.String())
    media_url = db.Column(db.String())
    label = db.Column(db.String())
    date_created = db.Column(db.Date(), default=func.now())
    date_updated = db.Column(db.Date(), default=func.now())
    realitem_id = db.Column(db.Integer, db.ForeignKey('real_items.database_id'), nullable=False)
    realitem = db.relationship("RealItems", back_populates="media")

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class Topics(db.Model):
    __tablename__ = 'topics'
    database_id = db.Column(db.Integer(), primary_key=True, unique=True)
    display_name = db.Column(db.String())
    date_created = db.Column(db.Date())    

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class EbayListing(db.Model):
    __tablename__ = 'ebay_listing'
    database_id = db.Column(db.Integer(), primary_key=True, unique=True)
    url = db.Column(db.String())
    title = db.Column(db.String())
    winning_bid = db.Column(db.Float())
    auction_type = db.Column(db.String())
    number_of_bids = db.Column(db.Integer())
    best_offer = db.Boolean()
    seller_name = db.Column(db.String())
    seller_feedback = db.Column(db.Integer())
    listing_date = db.Column(db.Date()) 
    photo_url_1 = db.Column(db.String())
    photo_url_2 = db.Column(db.String())
    photo_url_3 = db.Column(db.String())
    photo_url_4 = db.Column(db.String())
    photo_url_5 = db.Column(db.String())
    photo_file_name = db.Column(db.String())

    predicted_generic_id = db.Column(db.Integer(), db.ForeignKey('generic_items.id'))
    predicted_generic_id_list = db.Column(db.String())
    user_selected_generic_id = db.Column(db.Integer(), db.ForeignKey('generic_items.id'))
    user_approved = db.Column(db.Boolean(), default=False)
    user_comment = db.Column(db.String())
    user_id = db.Column(db.Integer(), db.ForeignKey('users.database_id'))
    date_approved = db.Column(db.Date())

    def __repr__(self):
        return f"<EbayListing {self.database_id}>"

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

'''
https://activitystrea.ms/specs/json/1.0/
An activity consists of an actor, a verb, an object, and a target.

Example activities:

1) [Ankur] [created a new collection] [Favorite Foils]
Actor: Ankur (Users)
Verb: Created a new collection
Object: Favorite Foils (ItemCollections)


2) [Arthur] is [accepting offers] on [Unlimited Black Lotus]
Actor: Arthur (Users)
Verb: Accepting Offers
Object:  Unlimited black Lotus (RealItem)


3) [Jelani] added [Unlimited Black Lotus] to his collection [Power Nine]
Actor: Jelani (UserS)
Verb: Added item to collection
Object: Unlimited Black Lotus (RealItem)
Target:  Collection called "Power Nine" (ItemCollections)


4) Purplemana has increased the buylist 33% for [Unlimited Black Lotus]
Actor:  Purplemana
Verb:  Increased
Object:  Unlimited Black Lotus (GenericItem)
[Offer] was [updated] for [Unlimited Black Lotus] by 30%
[object] was [verb] for [target] by 30%

5) [Ankur] added [defect] to [purpleLotus]
6) [Ankur] added [photos] for [purpleLotus] in [lotusCollection]
'''


class Activities(db.Model):
    __tablename__ = 'activities'
    database_id = db.Column(db.Integer(), primary_key=True, unique=True)
    actor = db.Column(db.String())
    
    # required fields
    # object is the entity of interest that is being followed
    object = db.Column(db.String(), nullable=False)
    objectEntity = db.Column(db.String())

    # target typically follows "to" in the sentence, not required
    target = db.Column(db.String())
    targetEntity = db.Column(db.String())

    # additional fields for context when presenting activities
    verb = db.Column(db.String(), nullable=False)
    content = db.Column(db.String())  # sentence literal
    icon = db.Column(db.String())  # probably the object icon (user avatar, card png, collection icon)
    timestamp = db.Column(db.Date())

    # relevant channels for the activity, can be null
    userId = db.Column(db.Integer(), db.ForeignKey('users.database_id'))
    offersId = db.Column(db.Integer(), db.ForeignKey('offers.id'))
    realItemId = db.Column(db.Integer(), db.ForeignKey('real_items.database_id'))
    collectionId = db.Column(db.Integer(), db.ForeignKey('item_collections.database_id'))
    genericItemId = db.Column(db.Integer(), db.ForeignKey('generic_items.id'))


# one user will have one entry for each of the entities they follow, so each row will look like
# id, usrdid, null, null, null, null, lotusGenericId : corresponding to following lotus updates
class Subscriptions(db.Model):
    __tablename__ = 'subscriptions'
    database_id = db.Column(db.Integer(), primary_key=True)
    subscriberId = db.Column(db.Integer(), db.ForeignKey('users.database_id'))
    userId = db.Column(db.Integer(), db.ForeignKey('users.database_id'))
    offersId = db.Column(db.Integer(), db.ForeignKey('offers.id'))
    realItemId = db.Column(db.Integer(), db.ForeignKey('real_items.database_id'))
    collectionId = db.Column(db.Integer(), db.ForeignKey('item_collections.database_id'))
    genericItemId = db.Column(db.Integer(), db.ForeignKey('generic_items.id'))


class CollectionHistory(db.Model):
    __tablename__ = 'collection_history'
    database_id = db.Column(db.Integer(), primary_key=True)
    collectionId = db.Column(db.Integer(), db.ForeignKey('item_collections.database_id'))
    timestamp = db.Column(db.Date())
    retail_value = db.Column(db.Float())
    pm_value = db.Column(db.Float())
    number_of_items = db.Column(db.Integer())


class Trades(db.Model):
    __tablename__ = 'trades'
    database_id = db.Column(db.Integer(), primary_key=True)
    date_created = db.Column(db.Date())
    date_updated = db.Column(db.Date())
    status = db.Column(db.String(), db.ForeignKey('trade_status.state'))
    left_credit = db.Column(db.Float())
    left_owner = db.Column(db.Integer(), db.ForeignKey('users.database_id'))
    left_confirm = db.Column(db.Boolean())
    right_credit = db.Column(db.Float())
    right_owner = db.Column(db.Integer(), db.ForeignKey('users.database_id'))
    right_confirm = db.Column(db.Boolean())
    left_close = db.Column(db.Boolean())
    right_close = db.Column(db.Boolean())
    half_closed_side = db.Column(db.String())
    paypal_costs = db.Column(db.Float())
    shipping_and_handling_costs = db.Column(db.Float())

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class TradeItems(db.Model):
    __tablename__ = 'trade_items'
    database_id = db.Column(db.Integer(), primary_key=True)
    trade_id = db.Column(db.Integer(), db.ForeignKey('trades.database_id'))
    real_item_id = db.Column(db.Integer(), db.ForeignKey('real_items.database_id'))
    side = db.Column(db.String())  # RIGHT OR LEFT

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class TradeStatus(db.Model):
    __tablename__ = 'trade_status'
    state = db.Column(db.String(), primary_key=True)
    

class Transactions(db.Model):
    __tablename__ = 'transactions'
    database_id = db.Column(db.Integer(), primary_key=True)
    date_created = db.Column(db.Date())
    date_updated = db.Column(db.Date())
    status = db.Column(db.String(), db.ForeignKey('transaction_status.state'))
    left_credit = db.Column(db.Float())
    left_owner = db.Column(db.Integer(), db.ForeignKey('users.database_id'))
    left_confirm = db.Column(db.Boolean())
    right_credit = db.Column(db.Float())
    right_owner = db.Column(db.Integer(), db.ForeignKey('users.database_id'))
    right_confirm = db.Column(db.Boolean())
    left_close = db.Column(db.Boolean())
    right_close = db.Column(db.Boolean())
    half_closed_side = db.Column(db.String())
    paypal_costs = db.Column(db.Float())
    shipping_and_handling_costs = db.Column(db.Float())
    admin_comment = db.Column(db.String())
    web_admin_approved = db.Column(db.Boolean())

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class TransactionLogs(db.Model):
    __tablename__ = 'transaction_logs'
    database_id = db.Column(db.Integer(), primary_key=True)
    transaction_id = db.Column(db.Integer(), db.ForeignKey('transactions.database_id'))
    date_created = db.Column(db.Date())
    message = db.Column(db.String())


class TransactionItems(db.Model):
    __tablename__ = 'transaction_items'
    database_id = db.Column(db.Integer(), primary_key=True)
    transaction_id = db.Column(db.Integer(), db.ForeignKey('transactions.database_id'))
    real_item_id = db.Column(db.Integer(), db.ForeignKey('real_items.database_id'))
    side = db.Column(db.String())  # RIGHT OR LEFT
    trade_in_value = db.Column(db.Float())
    trade_in_value_NM = db.Column(db.Float())
    web_approval = db.Column(db.Boolean())
    final_approval = db.Column(db.Boolean())
    admin_price = db.Column(db.Float())

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class TransactionStatus(db.Model):
    __tablename__ = 'transaction_status'
    state = db.Column(db.String(), primary_key=True)


class Notifications(db.Model):
    __tablename__ = 'notifications'
    database_id = db.Column(db.Integer(), primary_key=True)
    date_created = db.Column(db.Date())
    date_updated = db.Column(db.Date())
    read = db.Column(db.Boolean())  # past tense of reading
    message = db.Column(db.String())
    user_id = db.Column(db.Integer(), db.ForeignKey('users.database_id'))


class OffersTimeSeries(db.Model):
    __tablename__ = 'offers_time_series'
    item_id = db.Column(db.Integer(), primary_key=True)
    date_created = db.Column(db.DateTime())
    date_updated = db.Column(db.DateTime())
    history = db.Column(db.String())


class ItemLists(db.Model):
    __tablename__ = 'item_lists'
    database_id = db.Column(db.Integer(), primary_key=True, unique=True)
    user_id = db.Column(db.Integer(), db.ForeignKey("users.database_id"))
    name = db.Column(db.String())
    value = db.Column(db.Float())
    count = db.Column(db.Integer())
    date_created = db.Column(db.DateTime(), default=func.now())
    date_updated = db.Column(db.DateTime())
    real_items = db.relationship('RealItems', cascade="all, delete-orphan")

    def as_dict(self):
        return {"database_id": self.database_id, "user_id": self.user_id, "name": self.name}

class ListingFeedback(db.Model):
    __tablename__ = 'listing_feedback'
    database_id = db.Column(db.Integer(), primary_key=True, unique=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('users.database_id'))
    listing_id = db.Column(db.Integer(), db.ForeignKey('ebay_listing.database_id'))
    user_comment = db.Column(db.String())
    user_selected_generic_id = db.Column(db.Integer(), db.ForeignKey('generic_items.id'))
    is_correct = db.Column(db.Boolean())
    date_created = db.Column(db.DateTime(), default=func.now())

    def __repr__(self):
        return f"<ListingFeedback {self.database_id}>"

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}