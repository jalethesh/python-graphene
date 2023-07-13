from graphene import Mutation, String, Boolean, Field, Int, List, Float, Date
from models.data_models import db, GenericItems
from .graphene_models import GenericItemObject
from security import user_is_admin


class GenericItemArguments:
    oracle_id = String()
    multiverse_ids = String()
    mtgo_id = String()
    produced_mana = String()
    mtgo_foil_id = String()
    scryfall_card_id = String()
    legalities = String()
    full_art = Boolean()
    textless = Boolean()
    loyalty = String()
    oversized = Boolean()
    frame = String()
    card_back_id = String()
    games = String()
    lang = String()
    name = String()
    uri = String()
    rarity = String()
    variation = String()
    variation_of = String()
    layout = String()
    scryfall_uri = String()
    cmc = Float()
    cardmarket_id = String()
    tcgplayer_id = String()
    color_identity = String()
    colors = String()
    keywords = String()
    image_uris = String()
    foil = Boolean()
    nonfoil = Boolean()
    etchedfoil = Boolean()    
    mana_cost = String()
    oracle_text = String()
    power = String()
    reserved = Boolean()
    toughness = String()
    type_line = String()
    artist = String()
    booster = String()
    border_color = String()
    collector_number = String()
    flavor_name = String()
    flavor_text = String()
    illustration_id = String()
    printed_name = String()
    printed_text = String()
    printed_type_line = String()
    promo = Boolean()
    purchase_uris = String()
    released_at = Date()
    scryfall_set_uri = String()
    set_name = String()
    set_search_uri = String()
    set_type = String()
    set_uri = String()
    set = String()
    image_uri_small = String()
    image_uri_normal = String()
    image_uri_large = String()
    image_uri_png = String()
    original_name = String()

    # item_index = db.Column(db.String(), unique=True)
    # id = db.Column(db.Integer, primary_key=True, unique=True)
    # scryfall_set_id = db.Column(db.String, db.ForeignKey('sets.scryfall_set_id'), nullable=False)
    # offers = db.relationship('Offers', back_populates='item')


class CreateGenericItem(Mutation):
    class Arguments:
        item_index = String(required=True)
        scryfall_set_id = String(required=True)

    ok = Field(Boolean, default_value=False)
    genericItem = Field(lambda: GenericItemObject)
    debug = Field(String, default_value="no debug info")

    @user_is_admin
    def mutate(root, info, item_index, scryfall_set_id, **kwargs):
        generic_item = GenericItemObject()
        try:
            generic_item = GenericItems()
            generic_item.item_index = item_index
            generic_item.scryfall_set_id = scryfall_set_id
            editable_fields = [x for x in dir(GenericItemArguments) if '__' not in x]
            for field in kwargs:
                if field not in editable_fields:
                    continue
                setattr(generic_item, field, kwargs[field])
            db.session.add(generic_item)
            db.session.commit()
            ok = True
        except Exception as ex:
            db.session.rollback()
            return UpdateGenericItem(genericItem=generic_item, debug=str(ex))
        else:
            return UpdateGenericItem(genericItem=generic_item, ok=ok)


class UpdateGenericItem(Mutation):
    class Arguments(GenericItemArguments):
        database_id = Int(required=True)
        item_index = String()

    ok = Field(Boolean, default_value=False)
    genericItem = Field(lambda: GenericItemObject)
    debug = Field(String, default_value="no debug info")

    @user_is_admin
    def mutate(root, info, database_id, **kwargs):
        generic_item = GenericItemObject()
        try:
            generic_item = GenericItems.query.filter_by(id=database_id).first()
            if 'item_index' in kwargs:
                generic_item.item_index = kwargs['item_index']
            editable_fields = [x for x in dir(GenericItemArguments) if '__' not in x]
            for field in kwargs:
                if field not in editable_fields:
                    continue
                setattr(generic_item, field, kwargs[field])
            db.session.add(generic_item)
            db.session.commit()
            ok = True
        except Exception as ex:
            db.session.rollback()
            return UpdateGenericItem(genericItem=generic_item, debug=str(ex))
        else:
            return UpdateGenericItem(genericItem=generic_item, ok=ok)


class DeleteGenericItem(Mutation):
    class Arguments:
        database_id = Int(required=True)

    ok = Field(Boolean, default_value=False)
    debug = Field(String, default_value="no debug info")

    @user_is_admin
    def mutate(root, info, database_id):
        try:
            GenericItems.query.filter_by(id=database_id).delete()
            db.session.commit()
            ok = True
        except Exception as ex:
            db.session.rollback()
            return DeleteGenericItem(debug=str(ex))
        else:
            return DeleteGenericItem(ok=ok)