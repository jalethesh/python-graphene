import pickle
from timeit import timeit
from typing import List
from sqlalchemy import exc, or_
import requests

# from graphql_service import ItemManager
from models.data_models import RealItems, db, ItemCollections, OffersTimeSeries, ItemLists, TransactionItems
from models.data_models import Users, SetModel, GenericItems, Offers, OffersHistory, Conditions, Merchants, Media, \
    Defects, MerchantsConditionMultiplier, LatestOffers, LatestOffersHistory
from flask import Blueprint, render_template, jsonify, session
import click
import pandas as pd
import csv
import os
from sqlalchemy import desc, asc, func
import boto3
import botocore
from urlextract import URLExtract
import locale
import time
from datetime import datetime
import json
import h5py

from loggers import items_logger
from security import user_is_admin

items_factory = Blueprint("items", __name__, static_folder="static", template_folder="templates")


@items_factory.cli.command('attach_media')
@click.argument('username')
@click.argument('real_item')
@click.argument('media_url')
@click.argument('media_type')
@click.argument('label')
def attach_media(username, real_item, media_url, media_type, label):
    internal_attach_media(username, real_item, media_url, media_type, label)


def internal_attach_media(username, real_item, media_url, media_type, label):
    # print("attach media called")

    userid = db.session.query(Users).filter_by(username=username).first()
    # print(f"userid found: {userid.database_id}")

    fetch_real_item = db.session.query(RealItems).filter_by(database_id=real_item).first()
    # print(f"fetch_real_item found: {fetch_real_item}")

    fetch_generic_item = db.session.query(GenericItems).filter_by(id=fetch_real_item.item_id).first()
    # print(f"fetch_generic_item found: {fetch_generic_item}")

    s3_client = boto3.client('s3')

    r = requests.get(media_url, stream=True)

    boto3_session = boto3.Session()
    s3 = boto3_session.resource('s3')

    file_key = os.path.basename(media_url)

    bucket_name = 'purplemana-media'
    key = str(userid.database_id) + "/" + str(fetch_real_item.item_id) + "/" + file_key

    # upload the file and set the content type
    bucket = s3.Bucket(bucket_name)
    bucket.upload_fileobj(r.raw, key, ExtraArgs={'ContentType': "image/jpeg", 'ACL': "public-read"})

    # get the public url
    config = botocore.client.Config(signature_version=botocore.UNSIGNED)
    object_url = boto3.client('s3', config=config).generate_presigned_url('get_object', ExpiresIn=0,
                                                                          Params={'Bucket': bucket_name, 'Key': key})
    print(object_url)

    new_media = Media(type="image", label=label, media_url=object_url, realitem_id=fetch_real_item.database_id)
    db.session.add(new_media)
    db.session.commit()


@items_factory.cli.command('import_airtable_items')
@click.argument('csv_file')
def import_airtable_items(csv_file):
    # open file in read mode
    df = pd.read_csv(csv_file)

    for index, row in df.iterrows():

        print(f"---------------------------------------------")
        print(f"row.CARDS: {row.CARDS}")
        print(f"row.sku: {row.SKU}")
        print(f"row.COST_BASIS: {row.COST_BASIS}")
        print(f"row.TRADE_IN_VALUE: {row.TRADE_IN_VALUE}")
        print(f"row.STORE_PRICE: {row.STORE_PRICE}")
        print(f"row.CARD_INDEX: {row.CARD_INDEX}")
        print(f"row.MARKETING_IMAGE_QR_URL: {row.MARKETING_IMAGE_QR_URL}")
        print(f"row.MARKETING_IMAGE_NOQR_URL: {row.MARKETING_IMAGE_NOQR_URL}")
        print(f"row.WOO_IMAGE_FRONT: {row.WOO_IMAGE_FRONT}")
        print(f"row.WOO_IMAGE_BACK: {row.WOO_IMAGE_BACK}")
        print(f"row.IMAGE_QR_LABEL: {row.IMAGE_QR_LABEL}")
        print(f"row.WOO_FUSED_IMAGE: {row.WOO_FUSED_IMAGE}")
        print(f"row.QR_URL: {row.QR_URL}")
        print(f"row.Condition: {row.Condition}")
        print(f"row.STATUS: {row.STATUS}")

        extractor = URLExtract()

        try:
            urls = extractor.find_urls(row.IMAGE_QR_LABEL)
            QR_IMAGE_URL = urls[0]
            print(f"QR_IMAGE_URL: {QR_IMAGE_URL}")
            # find the item_id
            look_for_item = db.session.query(GenericItems).filter_by(item_index=row.CARDS).first()
            print(f"look_for_item: {look_for_item}")

            locale.setlocale(locale.LC_ALL, 'en_US.UTF8')
            parsed_cost_basis = None
            parsed_store_price = None
            parsed_tradeinvalue = None
            parsed_condition = "NONE"

            if row.STORE_PRICE != row.STORE_PRICE:
                print("STORE_PRICE NAN DETECTED")
            else:
                parsed_store_price = locale.atof(row.STORE_PRICE.strip("$"))
                print(f"parsed_store_price: {parsed_store_price}")

            if row.COST_BASIS != row.COST_BASIS:
                print("NAN DETECTED.  Keep as None")
            else:
                parsed_cost_basis = locale.atof(row.COST_BASIS.strip("$"))
                print(f"parsed_cost_basis: {parsed_cost_basis}")

            if row.Condition != row.Condition:
                print("NAN DETECTED.  Keep as None")
            else:
                parsed_condition = row.Condition

            if row.TRADE_IN_VALUE != row.TRADE_IN_VALUE:
                print("row.TRADE_IN_VALUE NAN DETECTED")
            else:
                parsed_tradeinvalue = locale.atof(row.TRADE_IN_VALUE.strip("$"))
                print(f"parsed_tradeinvalue: {parsed_tradeinvalue}")

            new_real_item = RealItems(status=row.STATUS, item_collections_id=666, item_id=look_for_item.id, sku=row.SKU,
                                      creator=12, owner=12, condition=parsed_condition, cost_basis=parsed_cost_basis,
                                      trade_in_value=parsed_tradeinvalue, forsale_price=parsed_store_price,
                                      woocommerce_url=row.WOO_URL, woocommerce_product_id=row.WOO_PRODUCT_ID)

            db.session.add(new_real_item)
            db.session.commit()
            print(f"Inserted: {new_real_item}")

            # now let's handle the media

            front_image = row.WOO_IMAGE_FRONT
            # print(f"front_image: {front_image}")
            back_image = row.WOO_IMAGE_BACK
            ebay_front = row.IMAGE_EBAY_FRONT
            ebay_back = row.IMAGE_EBAY_BACK
            marketing_image_qr = row.MARKETING_IMAGE_QR_URL
            marketing_image_noqr = row.MARKETING_IMAGE_NOQR_URL
            fused_image = row.WOO_FUSED_IMAGE
            dbid = new_real_item.database_id
            print(f"dbid: {dbid}")

            if front_image and front_image == front_image:
                internal_attach_media("anxman", dbid, front_image, "image", "front_image")
                print("attach_media finished for front_image")

            if back_image and back_image == back_image:
                internal_attach_media("anxman", dbid, back_image, "image", "back_image")
                print("attach_media finished for back_image")

            if ebay_front and ebay_front == ebay_front:
                internal_attach_media("anxman", dbid, ebay_front, "image", "ebay_front")
                print("attach_media finished for ebay_front")

            if ebay_back and ebay_back == ebay_back:
                internal_attach_media("anxman", dbid, ebay_back, "image", "ebay_back")
                print("attach_media finished for ebay_back")

            if marketing_image_qr and marketing_image_qr == marketing_image_qr:
                print("attaching marketing qr image")
                internal_attach_media("anxman", dbid, marketing_image_qr, "image", "marketing_image_qr")
                print("attach_media finished for marketing_image_qr")

            if marketing_image_noqr and marketing_image_noqr == marketing_image_noqr:
                internal_attach_media("anxman", dbid, marketing_image_noqr, "image", "marketing_image_noqr")
                print("attach_media finished for marketing_image_noqr")

            if fused_image and fused_image == fused_image:
                internal_attach_media("anxman", dbid, fused_image, "image", "fused_image")
                print("attach_media finished for fused_image")

            if QR_IMAGE_URL and QR_IMAGE_URL == QR_IMAGE_URL:
                internal_attach_media("anxman", dbid, QR_IMAGE_URL, "image", "QR_IMAGE_URL")
                print("attach_media finished for QR_IMAGE_URL")

            # okay now let's insert the defects
            if row.Inked and row.Inked == row.Inked:
                new_defect = Defects(realitem=new_real_item, defect_name="INKED")
                print("Adding defect: Inked")
                db.session.add(new_defect)
                db.session.commit()

            if row.Signed and row.Signed == row.Signed:
                new_defect = Defects(realitem=new_real_item, defect_name="SIGNED")
                print("Adding defect: SIGNED")
                db.session.add(new_defect)
                db.session.commit()

            if row.DENTED and row.DENTED == row.DENTED:
                new_defect = Defects(realitem=new_real_item, defect_name="DENTED")
                print("Adding defect: DENTED")
                db.session.add(new_defect)
                db.session.commit()

            if row.SCRATCHED and row.SCRATCHED == row.SCRATCHED:
                new_defect = Defects(realitem=new_real_item, defect_name="SCRATCHED")
                print("Adding defect: SCRATCHED")
                db.session.add(new_defect)
                db.session.commit()

            if row.BEND and row.BEND == row.BEND:
                new_defect = Defects(realitem=new_real_item, defect_name="BEND")
                print("Adding defect: BEND")
                db.session.add(new_defect)
                db.session.commit()

            if row.ROLLER_LINES and row.ROLLER_LINES == row.ROLLER_LINES:
                new_defect = Defects(realitem=new_real_item, defect_name="ROLLER_LINES")
                print("Adding defect: ROLLER_LINES")
                db.session.add(new_defect)
                db.session.commit()

            if row.CLOUDING and row.CLOUDING == row.CLOUDING:
                new_defect = Defects(realitem=new_real_item, defect_name="CLOUDING")
                print("Adding defect: CLOUDING")
                db.session.add(new_defect)
                db.session.commit()

            if row.CREASED and row.CREASED == row.CREASED:
                new_defect = Defects(realitem=new_real_item, defect_name="CREASED")
                print("Adding defect: CREASED")
                db.session.add(new_defect)
                db.session.commit()

            if row.SMUDGES and row.SMUDGES == row.SMUDGES:
                new_defect = Defects(realitem=new_real_item, defect_name="SMUDGES")
                print("Adding defect: SMUDGES")
                db.session.add(new_defect)
                db.session.commit()

            if row.CURLING and row.CURLING == row.CURLING:
                new_defect = Defects(realitem=new_real_item, defect_name="CURLING")
                print("Adding defect: CURLING")
                db.session.add(new_defect)
                db.session.commit()

            print("Finished ... sleeping")
            print("-----------------------------------")
            time.sleep(5)



        except Exception as ex:
            print("Failed to complete // exception " + str(ex))
            time.sleep(5)
            continue
            # return str(ex)


@items_factory.cli.command('add_merchants')
@click.argument('csv_file')
def add_merchants(csv_file):
    # open file in read mode
    df = pd.read_csv(csv_file)

    for index, merchant in df.iterrows():
        print(f"---------------------------------------------")
        print(f"merchant.shortcode: {merchant.shortcode}")
        print(f"merchant.name: {merchant.merchant_name}")
        print(f"merchant.city: {merchant.city}")
        print(f"merchant.state: {merchant.state}")
        print(f"merchant.country: {merchant.country}")

        insert_merchant = Merchants(shortcode=merchant.shortcode, name=merchant.merchant_name, city=merchant.city,
                                    state=merchant.state, country=merchant.country)

        db.session.add(insert_merchant)
        print(f"inserting {merchant.merchant_name} into db")
        db.session.commit()
        print(f"{merchant.merchant_name} committed to db")


@items_factory.cli.command('add_conditions')
@click.argument('csv_file')
def add_conditions(csv_file):
    # open file in read mode
    df = pd.read_csv(csv_file)

    for index, condition in df.iterrows():
        print(f"---------------------------------------------")
        # print(f"index: {index}, condition: {condition}")
        print(f"condition.us_code: {condition.us_code}")
        print(f"condition.eu_code: {condition.eu_code}")
        print(f"condition.type: {condition.type}")

        insert_condition = Conditions(us_code=condition.us_code, eu_code=condition.eu_code, type=condition.type)

        db.session.add(insert_condition)
        print(f"inserting {condition.us_code} into db")
        db.session.commit()
        print(f"{condition.us_code} committed to db")


@items_factory.cli.command('update_sets')
def scryfall_update_sets():
    print("scryfall_update_sets called")

    scryfall_bulk_data_api = "https://api.scryfall.com/sets"

    r = requests.get(scryfall_bulk_data_api)
    set_data = r.json()['data']

    for set in set_data:
        print(str(set))

        if set.get('mtgo_code'):
            print("mtgo_code set do nothing")
        else:
            set['mtgo_code'] = None

        if set.get('arena_code'):
            print("arena_code set do nothing")
        else:
            set['arena_code'] = None

        if set.get('tcgplayer_id'):
            print(" ")
        else:
            set['tcgplayer_id'] = None

        insert_set = SetModel(scryfall_set_id=set['id'], code=set['code'], mtgo_code=set['mtgo_code'],
                              arena_code=set['arena_code'], tcgplayer_id=set['tcgplayer_id'], name=set['name'],
                              uri=set['uri'], scryfall_uri=set['scryfall_uri'], search_uri=set['search_uri'],
                              released_at=set['released_at'], set_type=set['set_type'], digital=set['digital'],
                              nonfoil_only=set['nonfoil_only'], foil_only=set['foil_only'],
                              icon_svg_uri=set['icon_svg_uri'])

        db.session.add(insert_set)
        print("inserting into db")
        db.session.commit()
        print("committed")

    return True


@items_factory.cli.command('download_bulk_json')
@click.argument('bulk_set')
def download_bulk_data(bulk_set):
    print(f"download_bulk_data called writing to {bulk_set}.json")

    scryfall_bulk_data_api = "https://api.scryfall.com/bulk-data"

    r = requests.get(scryfall_bulk_data_api)
    bulk_data = r.json()['data']
    # print(bulk_data)
    for data in bulk_data:
        print(data['type'])
        if data['type'] == bulk_set:
            default_cards_url = data['download_uri']
            r.encoding = 'utf8'
            r = requests.get(default_cards_url)

            try:
                with open(bulk_set + ".json", 'wb') as f:
                    # print(r.content)
                    f.write(r.content)
                    print(bulk_set + ".json" + " written successfully")
                    return True
            except:
                print("Failed to write file")

    return False


@items_factory.cli.command('convert_json_to_csv')
@click.argument('input')
@click.argument('output')
def convert_json_to_csv(input, output):
    print(f"called convert_json_to_csv() on {input} to {output}")

    pdObj = pd.read_json(input, orient='records')
    print(f"read file successfully")

    try:
        print(f"trying to write to {output}")
        pdObj.to_csv(output, index=False, header=True, encoding="utf8", quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
        return True
    except:
        print(f"Failed to convert {input} to {output}")

    return False


@items_factory.cli.command('divide_csv')
@click.argument('input')
@click.argument('output')
@click.argument('num_rows')
def divide_csv(input, output, num_rows):
    print(f"divide_csv called with input: {input}, output: {output}, and num_rows: {num_rows}")
    file_in = input
    file_out = output
    file_temp = '_temp.csv'
    num_rows = int(num_rows)

    df = pd.read_csv(input, low_memory=False, quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
    print(f"read file successfully")

    try:
        print(f"trying to write to {output} and slice {num_rows} rows")
        df[:num_rows].to_csv(output, header=True, index=False, encoding="utf8", quotechar='"',
                             quoting=csv.QUOTE_NONNUMERIC)
    except:
        print(f"Failed to convert {input} to {output}")

    print(f"writing temp file: {file_temp}")
    df[num_rows:].to_csv(file_temp, header=True, index=False, encoding="utf8", quotechar='"',
                         quoting=csv.QUOTE_NONNUMERIC)

    # Rename f_temp to file_in, first remove existing file_in then rename temp file
    os.remove(file_in)
    os.rename(file_temp, file_in)
    return True


@items_factory.cli.command('csv_to_db')
@click.argument('input')
@click.argument('output')
def divide_csv(input, output):
    print(f"csv_to_db called with input: {input}, output: {output}")

    # open file in read mode
    df = pd.read_csv(input, quotechar='"')

    for index, card in df.iterrows():

        scryfall_id = card['id']

        print(f"---------------------------------------------")
        # print(f"index: {index}, row: {card}")
        print(f"card_name: {card['name']}")
        print(f"scryfall_card_id: {scryfall_id}")
        print(f"scryfall_set_id: {card['set_id']}")
        print(f"set: {card['set']}")
        myitem_index = card['set'].upper() + "__" + card['name']
        print(f"item_index: {myitem_index}")
        # print(f"---------------------------------------------")

        if card['set'] == "cei" or card['set'] == "ced":
            print("Collector's edition found")
            time.sleep(10)

        oracle_text = str(card['oracle_text'])
        scryfall_id = card['id']
        original_card_name = card['name']

        try:
            image_uri_small = eval(card['image_uris'])['small']
            image_uri_normal = eval(card['image_uris'])['normal']
            image_uri_large = eval(card['image_uris'])['large']
            image_uri_png = eval(card['image_uris'])['png']
            # print(f"image_uri_small: {image_uri_small}")
        except:
            print(f"---------------------------------------------")
            print("can't find all images, falling back to another attempt")
            print(f"image_uris: {card['image_uris']}")

            file1 = open("errors.txt", "a")  # append mode
            file1.write(f"Error with image extraction for item_index: {myitem_index}\n\n")
            file1.close()

        import winsound

        if "showcase" in str(card['frame_effects']):
            print("showcase FOUND")
            card['name'] = card['name'] + " [Showcase]"
            myitem_index = myitem_index + "_SHOWCASE"
            # time.sleep(5)


        elif "extendedart" in str(card['frame_effects']):
            print("extendedart FOUND")
            card['name'] = card['name'] + " [Extended Art]"
            myitem_index = myitem_index + "_EXTENDEDART"
            # time.sleep(5)

        if card['promo'] == True:
            print("promo FOUND ... retrieving type")
            print(card['promo_types'])
            import winsound
            card['name'] = card['name'] + " [Promo]"
            myitem_index = myitem_index + "_PROMO"
            # time.sleep(5)

        if card['full_art'] == True:
            print("Card is full art")
            import winsound
            card['name'] = card['name'] + " [Full Art]"
            myitem_index = myitem_index + "_FULLART"
            # time.sleep(5)

        is_paper = False
        if 'paper' in card['games']:
            is_paper = True

        if card['nonfoil'] and is_paper:
            print("card is nonfoil ...")
            nonfoil_flag = True
            foil_flag = False

        if card['foil'] and is_paper:
            print("card is foil ... modifying name")
            card['name'] = card['name'] + " [Foil]"
            myitem_index = myitem_index + "_FOIL"
            nonfoil_flag = False
            foil_flag = True

        try:
            insert_card = GenericItems(scryfall_card_id=scryfall_id, lang=card['lang'], name=card['name'],
                                       uri=card['uri'], scryfall_uri=card['scryfall_uri'], cmc=card['cmc'],
                                       cardmarket_id=card['cardmarket_id'], tcgplayer_id=card['tcgplayer_id'],
                                       color_identity=card['color_identity'], colors=card['colors'],
                                       keywords=str(card['keywords']), image_uris=card['image_uris'], foil=foil_flag,
                                       nonfoil=nonfoil_flag, etchedfoil=False, mana_cost=card['mana_cost'],
                                       oracle_text=oracle_text, power=card['power'], reserved=card['reserved'],
                                       toughness=card['toughness'], type_line=card['type_line'], artist=card['artist'],
                                       booster=card['booster'], border_color=card['border_color'],
                                       collector_number=card['collector_number'], flavor_name=card['flavor_name'],
                                       flavor_text=card['flavor_text'], frame=card['frame'],
                                       illustration_id=card['illustration_id'], printed_name=card['printed_name'],
                                       printed_text=card['printed_text'], printed_type_line=card['printed_type_line'],
                                       promo=card['promo'], released_at=card['released_at'],
                                       scryfall_set_uri=card['scryfall_set_uri'], set_search_uri=card['set_search_uri'],
                                       set_type=card['set_type'], set_uri=card['set_uri'], set=card['set'],
                                       scryfall_set_id=card['set_id'], image_uri_small=image_uri_small,
                                       image_uri_normal=image_uri_normal, image_uri_large=image_uri_large,
                                       image_uri_png=image_uri_png, item_index=myitem_index,
                                       oracle_id=card['oracle_id'], multiverse_ids=card['multiverse_ids'],
                                       mtgo_id=card['mtgo_id'], produced_mana=card['produced_mana'],
                                       mtgo_foil_id=card['mtgo_foil_id'], legalities=card['legalities'],
                                       full_art=card['full_art'], textless=card['textless'], loyalty=card['loyalty'],
                                       oversized=card['oversized'], card_back_id=card['card_back_id'],
                                       games=card['games'], rarity=card['rarity'], variation=card['variation'],
                                       variation_of=card['variation_of'], layout=card['layout'],
                                       original_name=original_card_name)
            db.session.add(insert_card)
            db.session.commit()
            print("inserted: " + insert_card)

        except:
            print(f"Error inserting into db: {myitem_index}")

            file1 = open("errors.txt", "a")  # append mode
            file1.write(
                f"Error with inserting into db for item_index: {myitem_index} and scryfall_card_id: {card['id']}\n")
            file1.close()
            db.session.rollback()

            try:
                print(
                    "Let's see if an GenericItem with same item_index already exists in case we are having a name collision")

                look_for_card = db.session.query(GenericItems).filter_by(item_index=myitem_index).first()
                print(f"look_for_card: {look_for_card}")
                # time.sleep(1)

                if (look_for_card):
                    print(f"look_for_card.scryfall_card_id: {look_for_card.scryfall_card_id}")
                    print(f"scryfall_id: {scryfall_id}")

                    if look_for_card.scryfall_card_id == scryfall_id:
                        print("Card already exists with same scryfall_id ... do nothing")
                    else:
                        myitem_index = myitem_index + "_" + card['collector_number']
                        print(f"New myitem_index: {myitem_index}")
                        new_name = card['name'] + " [" + card['collector_number'] + "]"
                        print(f"new_name: {new_name}")
                        # time.sleep(5)

                        insert_card = GenericItems(scryfall_card_id=scryfall_id, lang=card['lang'], name=new_name,
                                                   uri=card['uri'], scryfall_uri=card['scryfall_uri'], cmc=card['cmc'],
                                                   cardmarket_id=card['cardmarket_id'],
                                                   tcgplayer_id=card['tcgplayer_id'],
                                                   color_identity=card['color_identity'], colors=card['colors'],
                                                   keywords=str(card['keywords']), image_uris=card['image_uris'],
                                                   foil=foil_flag, nonfoil=nonfoil_flag, etchedfoil=False,
                                                   mana_cost=card['mana_cost'], oracle_text=oracle_text,
                                                   power=card['power'], reserved=card['reserved'],
                                                   toughness=card['toughness'], type_line=card['type_line'],
                                                   artist=card['artist'], booster=card['booster'],
                                                   border_color=card['border_color'],
                                                   collector_number=card['collector_number'],
                                                   flavor_name=card['flavor_name'], flavor_text=card['flavor_text'],
                                                   frame=card['frame'], illustration_id=card['illustration_id'],
                                                   printed_name=card['printed_name'], printed_text=card['printed_text'],
                                                   printed_type_line=card['printed_type_line'], promo=card['promo'],
                                                   released_at=card['released_at'],
                                                   scryfall_set_uri=card['scryfall_set_uri'], set_name=card['set_name'],
                                                   set_search_uri=card['set_search_uri'], set_type=card['set_type'],
                                                   set_uri=card['set_uri'], set=card['set'],
                                                   scryfall_set_id=card['set_id'], image_uri_small=image_uri_small,
                                                   image_uri_normal=image_uri_normal, image_uri_large=image_uri_large,
                                                   image_uri_png=image_uri_png, item_index=myitem_index,
                                                   oracle_id=card['oracle_id'], multiverse_ids=card['multiverse_ids'],
                                                   mtgo_id=card['mtgo_id'], produced_mana=card['produced_mana'],
                                                   mtgo_foil_id=card['mtgo_foil_id'], legalities=card['legalities'],
                                                   full_art=card['full_art'], textless=card['textless'],
                                                   loyalty=card['loyalty'], oversized=card['oversized'],
                                                   card_back_id=card['card_back_id'], games=card['games'],
                                                   rarity=card['rarity'], variation=card['variation'],
                                                   variation_of=card['variation_of'], layout=card['layout'],
                                                   original_name=original_card_name)
                        db.session.add(insert_card)
                        db.session.commit()
                        # time.sleep(5)


            except:
                print("Didn't find matching")

                file1 = open("errors.txt", "a", encoding="utf-8")  # append mode
                returnstring = "Check by hand: Error with inserting into db for item_index: " + myitem_index + " and scryfall_card_id: " + \
                               card['id'] + "\n"
                file1.write(returnstring)
                file1.close()
                db.session.rollback()

    # shutil.move(input,output)
    df.to_csv(output, mode='a')
    os.remove(input)

    return True


@items_factory.route("/sets/<set_name>")
def cards_in_set(set_name):
    print("cards_in_set called")

    card_data = None

    original_set_name = set_name

    try:
        card_data = db.session.query(GenericItems).filter_by(set_name=set_name.replace('_', ' ')).order_by('name').all()
    except:
        print("error in querying data in render_cards")

    return render_template("cards.html", card_data=card_data, set_name=original_set_name)


@items_factory.route("/sets/<set_name>/<card_name>")
def render_card(set_name, card_name):
    print("render_card called")

    original_set_name = set_name.replace('_', ' ')
    original_card_name = card_name.replace('_', ' ')
    # print(original_set_name)
    # print(original_card_name)

    mycard = db.session.query(GenericItems).filter_by(set_name=original_set_name, name=original_card_name).first()
    print(f"{mycard.name} ({mycard.set}): {mycard.item_index}")

    # this returns a list of offer items, in each offer item are the linked OffersHistory items
    # the card.html document expects a list of OffersHistory items, so a list comprehension is used to map the offers
    # list to an OffersHistory list
    offers_history_query = db.session.query(GenericItems, Offers, OffersHistory). \
        select_from(GenericItems). \
        join(Offers). \
        join(OffersHistory). \
        filter(GenericItems.item_index == mycard.item_index). \
        order_by(desc(OffersHistory.amount), desc(Offers.last_updated), desc(Offers.id)). \
        all()

    print("found these offers")
    for item in offers_history_query:
        print(item, item.OffersHistory, item.OffersHistory)
    offers_history_list = [x.OffersHistory for x in offers_history_query]

    return render_template("card.html", card=mycard, offers_history_query=offers_history_list)


@items_factory.route("/sets")
def render_sets():
    set_data = db.session.query(SetModel).order_by("code").all()
    return render_template("sets.html", set_data=set_data)


@items_factory.cli.command("load_condition_multipliers")
def load_condition_multipliers():
    data = pd.read_csv('condition_multipliers.csv').to_dict('records')
    merchants = [x.shortcode for x in db.session.query(Merchants).all()]
    print(data)
    for condition in data:
        condition_id = condition['Condition']
        print(f"processing condition {condition_id}")
        for merchant in merchants:
            try:
                multiplier = condition[merchant]
                print(f'attempting to set merchant {merchant} on element {condition[merchant]}')
                condition_multiplier_matches = db.session.query(MerchantsConditionMultiplier) \
                    .filter(MerchantsConditionMultiplier.merchant == merchant) \
                    .filter(MerchantsConditionMultiplier.condition_id == condition_id).all()
                if len(condition_multiplier_matches) == 0:
                    # insert new
                    condition_multiplier = MerchantsConditionMultiplier(merchant=merchant, condition_id=condition_id,
                                                                        multiplier=multiplier)
                    db.session.add(condition_multiplier)
                    db.session.commit()
                else:
                    # update required
                    pass
            except Exception as ex:
                print(ex)
                db.session.rollback()


@items_factory.cli.command("load_condition_multipliers")
def load_condition_multipliers():
    real_items = [x for x in db.session.query(RealItems).all() if not x.condition]
    for item in real_items:
        try:
            print(item, item.condition, str(item.condition))
            item.condition = 'NONE'
            db.session.add(item)
            db.session.commit()
        except Exception as ex:
            print(ex)
            db.session.rollback()


def calculate_cost_single_card(real_item, offer_history, condition_multipliers):
    if real_item.condition == 'NONE' or not real_item.condition:
        real_item.condition = 'LP'
    # here 0.8 is the market average conversion factor from NM to LP
    # a 1$ card at NM in the market is worth 0.8$ LP in our site (LP multiplier is 1)
    print(offer_history.amount, condition_multipliers[real_item.condition])
    estimated_value = offer_history.amount * condition_multipliers[real_item.condition] * 0.8
    return round(estimated_value, 2)


@items_factory.cli.command("highest_card")
@click.argument('collection_id')
def highest_card(collection_id):
    condition_multipliers = db.session.query(MerchantsConditionMultiplier).filter_by(merchant='PM').all()
    condition_multipliers = {x.condition_id: x.multiplier for x in condition_multipliers}
    real_items = db.session.query(RealItems).filter_by(item_collections_id=collection_id).all()
    print('length of real_items', len(real_items))
    real_items_ids = [real_item.item_id for real_item in real_items]
    generic_items = db.session.query(GenericItems).filter(GenericItems.id.in_(real_items_ids)).all()
    generic_item_ids = [generic_item.id for generic_item in generic_items]
    offers = db.session.query(LatestOffers).filter(LatestOffers.item_id.in_(generic_item_ids)).all()
    offer_database_id = [offer.database_id for offer in offers]
    offers_history = db.session.query(LatestOffersHistory).filter(LatestOffersHistory.offers_id.in_(offer_database_id)).all()
    max_value = 0
    max_real_item = real_items[0]
    print(f"found {len(real_items)} items in collection {collection_id}")
    failures = 0
    for i, real_item in enumerate(real_items):
        # print("estimating value of", real_item)
        try:
            estimated_value = calculate_cost_single_card(real_item, generic_items, offers)
            if estimated_value > max_value:
                max_value = estimated_value
                max_real_item = real_item
                print(f'{i} max_value', max_value)
                print(f'{i} max_real_item', max_real_item)
        except Exception as ex:
            db.session.rollback()
            failures += 1
            print(f'{i} Not Found', real_item, ex)
    print(f"found {failures} / {len(real_items)} failures")
    print('max_real_item_database_id', max_real_item.database_id)
    return max_real_item.database_id


def estimated_value_of_real_item(real_item):
    condition_multipliers = db.session.query(MerchantsConditionMultiplier).filter_by(merchant='PM').all()
    condition_multipliers = {x.condition_id: x.multiplier for x in condition_multipliers}

    offer = db.session.query(LatestOffers).filter(LatestOffers.item_id==real_item.item_id).first()
    if not offer:
        return 0
    offers_history = db.session.query(LatestOffersHistory)\
        .filter(LatestOffersHistory.offers_id == offer.database_id)\
        .filter_by(merchant='PM').all()

    try:
        history = [x for x in offers_history if x.merchant == 'PM'][0]
        print('calculating cost of card')
        return calculate_cost_single_card(real_item, history, condition_multipliers)
    except Exception as ex:
        print("no PM offer found for", real_item, ex)
        return 0


def total_value_of_real_item_list(real_items):
    # the blocks of data are pulled from the database
    # then each table is wrote into a dict so that the contents are indexed / mapped with a hash key
    condition_multipliers = db.session.query(MerchantsConditionMultiplier).filter_by(merchant='PM').all()
    condition_multipliers = {x.condition_id: x.multiplier for x in condition_multipliers}
    print('length of real_items', len(real_items))
    generic_items_ids = [real_item.item_id for real_item in real_items]
    # print("using these generic item ids", generic_items_ids[:5], "...")
    offers = db.session.query(LatestOffers).filter(LatestOffers.item_id.in_(generic_items_ids)).all()
    offers_map = {}
    for offer in offers:
        offers_map[str(offer.item_id)] = offer
    offer_database_id = [offer.database_id for offer in offers]
    offers_history = db.session.query(LatestOffersHistory)\
        .filter(LatestOffersHistory.offers_id.in_(offer_database_id))\
        .filter_by(merchant='PM').all()
    offers_history_map = {}
    for offer_history in offers_history:
        offers_history_map[str(offer_history.offers_id)] = offer_history
    total = 0
    failures = 0
    start = time.time()

    for i, real_item in enumerate(real_items):
        if i % 20 == 0:
            print(f"{i} / {len(real_items)}")
        try:
            offer = offers_map[str(real_item.item_id)]
            history = offers_history_map[str(offer.database_id)]
            estimated_value = calculate_cost_single_card(real_item, history, condition_multipliers)
            real_item.fmv = estimated_value
            # real_item.trade_in_value = estimated_value
            db.session.add(real_item)
            total += estimated_value
            db.session.commit()
        except Exception as ex:
            db.session.rollback()
            failures += 1
            print(f'{i} Not Found', real_item, ex)
    end = time.time()
    # print(f"loop total {end-start} s/item {(end-start) / len(real_items)}")
    print(f"found {failures} / {len(real_items)} failures")
    return total


def update_item_list_on_real_item_mutation(item_list_id):
    real_items = db.session.query(RealItems).filter_by(item_list_id=item_list_id).all()
    print(f"{[x.fmv for x in real_items if x.fmv][:5]} ...")
    total_value = sum([x.fmv for x in real_items if x.fmv])
    item_list: ItemLists = db.session.query(ItemLists).filter_by(database_id=item_list_id).first()
    if not item_list:
        raise Exception(f'item list not valid: {item_list_id}')
    item_list.value = round(total_value, 2)
    item_list.count = len(real_items)
    item_list.date_updated = datetime.now()
    db.session.add(item_list)


@items_factory.cli.command("update_fmv")
def update_fmv_item():
    real_items = db.session.query(RealItems).all()
    failures = 0
    print("Length:", len(real_items))
    for i, real_item in enumerate(real_items):
        try:
            new_value = round(estimated_value_of_real_item(real_item),2)
            if i % 30 == 0:
                print(f"#{i} old fmv value: {real_item.fmv} | new fmv value: {new_value}")

            if new_value == 0: 
                new_value = 0.0
                items_logger.error("Failed to update real item fmv value, assign 0.0")
                failures += 1

            real_item.fmv = new_value
            db.session.add(real_item)
            db.session.commit()
        except Exception as ex:
            db.session.rollback()
            failures += 1
            items_logger.debug(ex)
    print(f"The update of {failures} / {len(real_items)} real_items.fmv failed")


def make_item_hash(real_item):
    generic_item: GenericItems = db.session.query(GenericItems).filter_by(id=real_item.item_id).first()
    try:
        set_name = str(generic_item.set_name)
    except Exception as ex:
        items_logger.debug(f"{real_item} has no set name {str(ex)}")
        set_name = "_"
    try:
        condition = str(real_item.condition)
    except Exception as ex:
        items_logger.debug(f"{real_item} has no condition {str(ex)}")
        condition = "_"
    item_hash = '_'.join([set_name,
                          str(generic_item.item_index),
                          condition,])
    return item_hash


@items_factory.cli.command("update_real_items_hash")
def update_real_items_hash():
    real_items: List[RealItems] = db.session.query(RealItems).all()
    failures = 0
    print("Length:", len(real_items))
    for i, real_item in enumerate(real_items):

        try:
            item_hash = make_item_hash(real_item)
            items_logger.debug(f"{i} {real_item} {item_hash}")
            if i % 30 == 0:
                print(f"#{i} new item hash value: {item_hash}")
            real_item.item_hash = item_hash
            db.session.add(real_item)
            db.session.commit()
        except Exception as ex:
            db.session.rollback()
            failures += 1
            items_logger.debug(f"{real_item} {str(ex)}")
    print(f"The update of {failures} / {len(real_items)} real_items.item_hash failed")


@items_factory.cli.command("update_item_lists")
def update_item_lists():
    item_lists: List[ItemLists] = db.session.query(ItemLists).all()
    failures = 0
    print("item_lists length:", len(item_lists))
    for i, item_list in enumerate(item_lists):
        try:
            update_item_list_on_real_item_mutation(item_list.database_id)
            db.session.commit()
        except Exception as ex:
            failures += 1
            db.session.rollback()
            items_logger.debug(ex)
    print(f"The update of {failures} / {len(item_lists)} item_lists.value failed")


@items_factory.cli.command("value_collection")
def value_collection():
    user = db.session.query(Users).filter_by(username="taylorprime").first()
    user_id = user.database_id
    real_items = db.session.query(RealItems).filter_by(owner=user_id).all()
    total_value_of_real_item_list(real_items)


def time_string():
    now = datetime.now()
    return now.strftime("%d/%m/%Y %H:%M:%S")

import shutil
@items_factory.cli.command("make_history")
def make_history():
    # download offers table in batches, and then builds a hash map using the primary key as the hash key
    n_offers = db.session.query(Offers).count()
    print(f"found {n_offers} offers")
    n_history = db.session.query(OffersHistory).count()
    print(f"found {n_history} history rows")

    offers_by_id = {}

    # batch_size = 100_000
    # for i in range(0, n_offers, batch_size):
    #     start = time.time()
    #     print(f"processing chunk {i/batch_size} / {n_offers/batch_size}")
    #     offers_chunk: List[Offers] = db.session.query(Offers).order_by(asc(Offers.id)).offset(i).limit(batch_size)
    #     for offer in offers_chunk:
    #         offers_by_id[offer.id] = {'id': offer.id, 'item_id': offer.item_id}
    #
    #     end = time.time()
    #     print(f"{time_string()} took {end-start} s")
    # pickle.dump(offers_by_id, open('offers', 'wb'))

    offers_by_id = pickle.Unpickler(open('offers', 'rb')).load()

    # download offersHistory using a local file as a buffer via h5py
    # for each item downloaded, lookup the offers record in the offers hash map, then store the data using the item_id

    # each entry is a json serialized array of dicts where each dict is a data point
    # json.dumps([ {}, {}, {}, {}, ... ])
    # it must be de-serialized into the python objects, then appended to with matching history data, then re-stored

    def make_new_dataset():
        f_history = h5py.File(data_fpath, "w")
        utf8_type = h5py.string_dtype('utf-8')
        history_dset = f_history.create_dataset("mydataset", (10_000_000, 1), dtype=utf8_type)
        start_offset = 0
        return history_dset, start_offset

    batch_size = 100_000
    data_fpath = "history-hdf.hdf5"
    try:
        shutil.copy( f'./datasets/history_backup_{30000000}.hdf5', data_fpath)
        f_history = h5py.File(data_fpath, "r+")
        history_dset = f_history['mydataset']
        start_offset =300*batch_size
    except Exception as ex:
        print(ex)
        history_dset, start_offset = make_new_dataset()
    if start_offset == 0:
        try:
            shutil.copy( f'./datasets/history_backup_{20000000}.hdf5', data_fpath)
            f_history = h5py.File(data_fpath, "r+")
            history_dset = f_history['mydataset']
            start_offset =200*batch_size
        except Exception as ex:
            print(ex)
            history_dset, start_offset = make_new_dataset()
    if start_offset == 0:
        try:
            shutil.copy( f'./datasets/history_backup_{10000000}.hdf5', data_fpath)
            f_history = h5py.File(data_fpath, "r+")
            history_dset = f_history['mydataset']
            start_offset =100*batch_size
        except Exception as ex:
            print(ex)
            history_dset, start_offset = make_new_dataset()

    print(f"using offset {start_offset}")
    for i in range(start_offset, n_history, batch_size):
        if i%10_000_000 == 0:
            shutil.copy(data_fpath, f'./datasets/history_backup_{i}.hdf5')
        start = time.time()
        history_chunk: List[OffersHistory] = db.session.query(OffersHistory).order_by(asc(OffersHistory.id)).offset(i).limit(batch_size)
        print(f"processing history chunk {i/batch_size} / {n_history/batch_size}")
        sample_keys = []
        chunk_count = 0
        for history in history_chunk:
            try:
                item_id = offers_by_id[history.offers_id]['item_id']
                if not item_id:
                    continue
            except:
                print("no matching offer")
                continue
            try:
                arr = json.loads(history_dset[item_id][0].decode('utf-8'))
                if len(arr) > 2 and len(sample_keys) < 20:
                    sample_keys.append(item_id)
            except:
                arr = []
            if history.id in [x['id'] for x in arr]:
                continue
            arr.append({
                'id': history.id,
                'last_updated': history.last_updated.isoformat(),
                'amount': history.amount,
                'merchant': history.merchant,
            })
            str_arr = json.dumps(arr)
            history_dset[item_id] = str_arr
            chunk_count += 1

        end = time.time()
        print(f"{time_string()} took {end-start} s for {chunk_count} size chunk")
        print(sample_keys)

    # now that all the data is processed, it can be transferred to the db
    time_series = db.session.query(OffersTimeSeries).all()
    time_series = {x.item_id: x for x in time_series}

    valid = 0
    for i in range(3_000_000):
        if i % 100_000 == 0:
            print(f"{i} / 3 000 000")
            try:
                db.session.commit()
            except Exception as ex:
                print("commit ex", ex)
                db.session.rollback()
        try:
            data = json.loads(history_dset[i][0].decode('utf-8'))
            if len(data) < 5:
                continue
            try:
                series = time_series[i]
            except:
                series = OffersTimeSeries(item_id=i, history='', date_created=datetime.now())
            series.history = json.dumps(data)
            db.session.add(series)
            valid += 1
        except:
            pass
    print(f"found {valid} id with history")

def update_generic_placeholder(gen_item: GenericItems, card: dict):
    # Update the `gen_item` with the `card` data

    print(f"---------------------------------------------")
    # print(f"index: {index}, row: {card}")
    print(f"card_name: {card['name']}")
    print(f"scryfall_card_id: {gen_item.scryfall_card_id}")
    print(f"scryfall_set_id: {card['set_id']}")
    print(f"set: {card['set']}")
    myitem_index = card['set'].upper() + "__" + card['name']
    print(f"item_index: {myitem_index}")
    # print(f"---------------------------------------------")

    if card['set'] == "cei" or card['set'] == "ced":
        print("Collector's edition found")

    card['nonfoil'] = gen_item.nonfoil
    card['foil'] = gen_item.foil
    print("foil", card['foil'])
    oracle_text = str(card['oracle_text']) if 'oracle_text' in card else 'NaN'
    scryfall_id = card['id']
    promo_type = None
    full_art = None
    original_card_name = card['name']
    if 'frame_effects' not in card:
        card['frame_effects'] = ''
      
    # TODO: Refactor try satement statement here
    try:
        image_uri_small = card['image_uris'].get('small')
        image_uri_normal = card['image_uris'].get('normal')
        image_uri_large = card['image_uris'].get('large')
        image_uri_png = card['image_uris'].get('png')
    except:
        print(f"---------------------------------------------")
        print("can't find all images, falling back to another attempt")
        try:
            print(f"image_uris: {card['image_uris']}")
        except:
            print("ERROR card image uris not found, probably double sided", scryfall_id)
            file1 = open("errors.txt", "a")  # append mode
            file1.write(f"Error with image extraction for item_index: {myitem_index}\n\n")
            file1.close()
            items_logger.debug(f"SKIPPING: Error with image extraction for item_index: {myitem_index}")
            return False
    if "showcase" in str(card['frame_effects']):
        print("showcase FOUND")
        card['name'] = card['name'] + " [Showcase]"
        myitem_index = myitem_index + "_SHOWCASE"

    elif "extendedart" in str(card['frame_effects']):
        print("extendedart FOUND")
        card['name'] = card['name'] + " [Extended Art]"
        myitem_index = myitem_index + "_EXTENDEDART"

    if card['promo']:
        print("promo FOUND ... retrieving type")
        # print(card['promo_types'])
        card['name'] = card['name'] + " [Promo]"
        myitem_index = myitem_index + "_PROMO"

    if card['full_art']:
        print("Card is full art")
        card['name'] = card['name'] + " [Full Art]"
        myitem_index = myitem_index + "_FULLART"

    is_paper = False
    if 'paper' in card['games']:
        is_paper = True

    if card['nonfoil'] and is_paper:
        print("card is nonfoil ...")

    if card['foil'] and is_paper:
        print("card is foil ... modifying name")
        card['name'] = card['name'] + " [Foil]"
        myitem_index = myitem_index + "_FOIL"

    # these fields are nullable in the database, but not always present on the request response
    # if they are missing on the response, write NaN
    nullable_fields = ['cardmarket_id', 'power', 'toughness', 'flavor_name', 'flavor_text', 'printed_name',
                        'printed_text', 'printed_type_line', 'mtgo_foil_id', 'loyalty', 'variation_of', 'mana_cost',
                        'mtgo_id', 'oracle_text', 'illustration_id', 'tcgplayer_id']
    for field in nullable_fields:
        if field not in card:
            card[field] = float("NaN")

    # cast dictionaries to strings
    card['image_uris'] = json.dumps(card['image_uris'])
    card['legalities'] = json.dumps(card['legalities'])

    # this is a special field that we will use to create the item index / name fields
    if 'collector_number' in card:
        print("found collector number", card["collector_number"])
        if card['lang'] != 'en':
            card['name'] = card['name'] + f' [{card["collector_number"]}]' + f' [{card["lang"]}]'
        myitem_index = myitem_index + f'_{card["collector_number"]}' + f'_{card["lang"]}'
    print("card name", card['name'])
    print("item index", myitem_index)

    # these fields parse out as non-strings: lists or dicts
    # stringify them for the database
    for field in ['multiverse_ids', 'produced_mana', 'games', 'color_identity', 'colors']:
        if field not in card:
            card[field] = 'NaN'
            continue
        card[field] = str(card[field])

    #Add item hash
    promo = "promo" if card['promo'] else ""
    foil = 'foil' if card['foil'] else ""
    card['item_hash'] = f"{card['name']}-{card['set_name']}-{card['set']}-{promo}-{foil}-{str(card['collector_number'])}-{card['artist']}-{card['lang']}"

    # Bypass if the item already has a name. 
    # Case where item was already previously updated but incompletely or incorrectly
    # Need to keep the previous name and original item_index
    if gen_item.name != 'UPDATE ME':
        card['name'] = gen_item.name 
        myitem_index = gen_item.item_index        

    updates = GenericItems(scryfall_card_id=scryfall_id, lang=card['lang'], name=card['name'],
                            uri=card['uri'], scryfall_uri=card['scryfall_uri'], cmc=card['cmc'],
                            cardmarket_id=card['cardmarket_id'], tcgplayer_id=card['tcgplayer_id'],
                            color_identity=card['color_identity'], colors=card['colors'],
                            keywords=str(card['keywords']), image_uris=card['image_uris'], foil=card['foil'],
                            nonfoil=card['nonfoil'], etchedfoil=False, mana_cost=card['mana_cost'],
                            oracle_text=card['oracle_text'], power=card['power'], reserved=card['reserved'],
                            toughness=card['toughness'], type_line=card['type_line'], artist=card['artist'],
                            booster=card['booster'], border_color=card['border_color'],
                            collector_number=card['collector_number'], flavor_name=card['flavor_name'],
                            flavor_text=card['flavor_text'], frame=card['frame'],
                            illustration_id=card['illustration_id'], printed_name=card['printed_name'],
                            printed_text=card['printed_text'], printed_type_line=card['printed_type_line'],
                            promo=card['promo'], released_at=card['released_at'],
                            scryfall_set_uri=card['scryfall_set_uri'], set_search_uri=card['set_search_uri'],
                            set_type=card['set_type'], set_uri=card['set_uri'], set=card['set'],
                            scryfall_set_id=card['set_id'], set_name=card['set_name'],
                            image_uri_small=image_uri_small,
                            image_uri_normal=image_uri_normal, image_uri_large=image_uri_large,
                            image_uri_png=image_uri_png, item_index=myitem_index,
                            oracle_id=card['oracle_id'], multiverse_ids=card['multiverse_ids'],
                            mtgo_id=card['mtgo_id'], produced_mana=card['produced_mana'],
                            mtgo_foil_id=card['mtgo_foil_id'], legalities=card['legalities'],
                            full_art=card['full_art'], textless=card['textless'], loyalty=card['loyalty'],
                            oversized=card['oversized'], card_back_id=card['card_back_id'],
                            games=card['games'], rarity=card['rarity'], variation=card['variation'],
                            variation_of=card['variation_of'], layout=card['layout'],
                            original_name=original_card_name, item_hash=card['item_hash'])

    # write data into the retrieved row from the original "UPDATE ME" generic items query
    
    for field in dir(updates):
        if '_' == field[0] or field in ['as_dict', 'id', 'scryfall_id', 'dict']:
            continue
        value = getattr(updates, field)

        try:
            setattr(gen_item, field, value)
        except exc.IntegrityError as e:
            db.session.rollback()
            if 'duplicate key value violates unique constraint' in str(e):
                items_logger.debug(f"ERROR in updating item {gen_item.item_index} to {updates.item_index} due to duplicate unique key. Skipping")
                return False #Expected behavior as of now #TODO Find a way to deal with stagnating data (items w/ name=UPDATE ME) due to leaving it like this
            else:
                items_logger.debug(f"ERROR in updating item {gen_item.item_index}: {e}. Skipping")
            return False

        except Exception as e:
            db.session.rollback()
            print("some collision with", updates.item_index)
            f = open("collisions-generic-items.txt", "a")
            f.write(f"{updates.item_index} {updates.scryfall_card_id}\n")
            f.close()
            items_logger.debug(f"ERROR in updating item {updates.item_index}: {e}")
            print('updating item', gen_item.id)
            return False
            

    db.session.commit()
    items_logger.debug(f"Finished updating item: {updates.item_index}")
    return True


@items_factory.cli.command("update_placeholder_items")
@click.option('-l','--limit', type=int, default=None)
@click.option('--csv_path', type=click.Path(), default=None, help="Folder where to save the csv files")
@click.option('--mtg_set', '-s', default=None, type=str, multiple=True, help='Select a specific set to update. Pass each set with a -s')
def update_placeholder_items(limit, csv_path, mtg_set):
    items_logger.debug("Starting update_generic_items")
    f = open("collisions-generic-items.txt", "a")
    now = time_string()
    f.write(f"{now} beginning updates for generic items\n")
    f.close()
   
    # Add name filter
    query = db.session.query(GenericItems).filter(or_(GenericItems.name == 'UPDATE ME', GenericItems.foil == None, GenericItems.nonfoil == None))
    #Futher filtering by SET
    if isinstance(mtg_set, tuple) and len(mtg_set) >= 1:
        mtg_set_list  = [mtg_set_name.strip().lower() for mtg_set_name in mtg_set]
        generic_item_placeholders = []
        for m_set in mtg_set_list:
            query = db.session.query(GenericItems).filter(or_(GenericItems.name == 'UPDATE ME', GenericItems.foil == None, GenericItems.nonfoil == None))
            generic_item_placeholders.extend(query.filter(GenericItems.set==m_set).limit(limit).all())
    else:
        query = db.session.query(GenericItems).filter(GenericItems.name == 'UPDATE ME')
        generic_item_placeholders = query.limit(limit).all()

    print(f"found {len(generic_item_placeholders)} items to update")

    idx = 0
    for gen_item in generic_item_placeholders:
        scryfall_id = gen_item.scryfall_card_id
        url = f'https://api.scryfall.com/cards/{scryfall_id}?format=json&pretty=true'
        card = requests.get(url).json()
        assert card['id'] == scryfall_id
        gen_item_old_params = gen_item.as_dict().copy()

        # Handle foil/nonfoil NULL values for 'ced','cei'
        if gen_item.set.lower() in ['ced','cei'] and (gen_item.foil is None or gen_item.nonfoil is None):
            gen_item.foil = False
            gen_item.nonfoil = True

            with open('logs/updated_to_nonfoil_true_genitems.txt', 'a+') as f:
                f.write(f"{gen_item.id} {gen_item.name} {gen_item.set}\n")

        ret_val = update_generic_placeholder(gen_item, card)
        
        # Check if update was successful
        if not ret_val:
            items_logger.debug(f"Not able to update: {gen_item.item_index}. Skipping")

        if csv_path:
            affixes = [(gen_item.as_dict(), '_new'), (gen_item_old_params,'_old')]
            for item, affix in affixes:
                if os.path.exists(csv_path.replace('.csv',f'{affix}.csv')):
                # Write row with generic_items's paremeters
                    with open(csv_path.replace('.csv',f'{affix}.csv'), 'a') as csv_file:
                        writer = csv.writer(csv_file)
                        writer.writerow(item.values())
                        # Close and save
                        csv_file.close()
                else: # Create csv_files if it doesn't exist
                    with open(csv_path.replace('.csv',f'{affix}.csv'), 'x') as csv_file:
                        writer = csv.writer(csv_file)
                        writer.writerow(item.keys()) #Write the headers first
                        writer.writerow(item.values())
                        csv_file.close()

        if isinstance(limit, int) and idx >= limit-1:
            break
        idx += 1

    print(f'Finished updating {idx+1} items')
    items_logger.debug(f'Finished updating {idx+1} items')
    return True


@items_factory.cli.command("check_duplicates")
def check_duplicates():
    # there are duplicates of genericItems and its not clear why
    # they are created when the query for genericItem(scryfallcardId, foil, nonfoil) fails in insert_daily_offers

    def connected_data(generic_item_id):
        print(f"--- {generic_item_id} ---")
        offers = db.session.query(Offers).filter_by(item_id=generic_item_id).all()
        latest_offers = db.session.query(LatestOffers).filter_by(item_id=generic_item_id).all()

        print(f"found {len(offers)} offers")
        for offer in offers:
            print(offer.last_updated)
        if len(latest_offers) > 1:
            raise "multiple latest offers"
        return offers, latest_offers


    # paper filter
    games = ["['arena', 'paper', 'mtgo']", "['arena', 'paper']", "['paper', 'mtgo']", "['paper']"]
    # lets find all the collisions
    # .filter(GenericItems.games.in_(games))
    generic_items = db.session.query(GenericItems)\
        .with_entities(GenericItems.id, GenericItems.name, GenericItems.scryfall_card_id, GenericItems.foil, GenericItems.nonfoil,
                      GenericItems.games, GenericItems.item_index)\
        .all()
    print("retrieved all generic items")
    items_with_hash = [{'item':x, 'hash': x.scryfall_card_id+str(x.foil)+str(x.nonfoil)} for x in generic_items]
    hash_buckets = {}
    for item in items_with_hash:
        if item['hash'] in hash_buckets:
            hash_buckets[item['hash']].append(item)
        else:
            hash_buckets[item['hash']] = [item]

    # my card
    my_card_item_id = '1210183'
    my_card_scryfall = 'dbbcd63d-6c25-47a6-a76c-ac53bf12949c'
    my_card_hash = my_card_scryfall+str(False)+str(True)
    my_hashes = hash_buckets[my_card_hash]
    print("found these items", my_hashes)

    print("created hashes of items for comparisons")
    print(f"created {len(hash_buckets)} hash buckets")
    duplicate_deletes = []
    for i,bucket in enumerate(hash_buckets):
        # if i%1000 == 0:
        print(f"{i} / {len(hash_buckets)}")
        collisions = hash_buckets[bucket]
        if len(collisions) > 1:
            print(f"found collision for {collisions[0]['item'].name} {collisions[0]['item'].scryfall_card_id}")
            all_offers = []
            for collision in collisions:
                offers, latest = connected_data(collision['item'].id)
                all_offers.extend(offers)
                all_offers.extend(latest)
            collision_ids = [x['item'].id for x in collisions]
            earliest_id = min(collision_ids)
            earliest_item = [x for x in collisions if x['item'].id == earliest_id][0]
            delete_items = [x for x in collisions if x['item'].id != earliest_id]
            print(f"earliest generic item is {earliest_item['item'].id} {earliest_item['hash']}")
            try:

                # updating offers
                for offer in all_offers:
                    pass
                    offer.item_id = earliest_item['item'].id
                    offer.item_index = earliest_item['item'].item_index
                    db.session.add(offer)
                # deleting later added generic item
                for deleteable in delete_items:
                    duplicate_deletes.append(deleteable)
                    db.session.query(GenericItems).filter_by(id=deleteable['item'].id).delete()
                    print("deleting item", deleteable['item'].id)
                db.session.commit()
            except Exception as ex:
                print(ex)
                db.session.rollback()
    pd.DataFrame(duplicate_deletes).to_csv('data_processing/generic_deletes.csv', index=False)


# took about 6 hours first time it was run
@items_factory.cli.command("hash_generic_items")
def hash_generic_items():
    items: List[GenericItems] = db.session.query(GenericItems).filter(func.lower(GenericItems.games).contains('paper')).all()
    for i, item in enumerate(items):
        if i%1000 == 0:
            print(f"{i}/{len(items)}")
        promo = "promo" if item.promo else ""
        foil = "foil" if item.foil else ""
        hash_str = f"{item.name}-{item.set_name}-{item.set}-{promo}-{foil}-{str(item.collector_number)}-{item.artist}"
        item.item_hash = hash_str
        db.session.add(item)
        if i%1000 == 0:
            print(f"committing {i}/{len(items)}")
            db.session.commit()


@items_factory.route("/items/to_scan", methods=['GET'])
def items_to_scan():
    results: List[RealItems] = db.session.query(RealItems, GenericItems)\
        .filter(RealItems.status == 'TO_SCAN')\
        .filter(GenericItems.id == RealItems.item_id)\
        .all()
    print(results)
    items = [{'id': x[0].database_id,
              'condition': x[0].condition,
              'sku': x[0].sku,
              'url': f"https://juzam.purplemana.com/assets/{str(x[0].database_id)}",
              'set': x[1].set,
              'name': x[1].name} for x in results]
    return jsonify(items)


@items_factory.route("/items/print_qr/<real_item_id>")
@user_is_admin
def reprint_qr(real_item_id):
    real_item = db.session.query(RealItems).filter_by(database_id=int(real_item_id)).first()

    url = "https://hook.integromat.com/21diinamf4lhd7arygaqu9d9kc7tzo41"

    params = {
        'qr_url': real_item.qr_label_url,
        'filename': f'qr-label-{real_item.sku}'
    }

    requests.get(url, params=params)

    db.session.add(real_item)
    db.session.commit()

    return jsonify({"message": "success"})


@items_factory.cli.command("update_trade")
def update_trade():
    real_items = db.session.query(RealItems).filter_by(item_list_id=278).all()
    print(len(real_items))
    for item in real_items:
        item.status = 'TO_SCAN'
        db.session.add(item)
    db.session.commit()


@items_factory.cli.command("set_trade_in_nm_values")
def set_trade_in_nm_values():
    items: List[TransactionItems] = db.session.query(TransactionItems).filter_by().all()
    condition_multipliers = db.session.query(MerchantsConditionMultiplier).filter_by(merchant='PM').all()
    condition_multipliers = {x.condition_id: x.multiplier for x in condition_multipliers}

    for item in items:
        real_item = db.session.query(RealItems).filter_by(database_id=item.real_item_id).first()
        item.trade_in_value_NM = item.trade_in_value * (1.25 / condition_multipliers[real_item.condition])
        db.session.add(item)
    db.session.commit()


@items_factory.cli.command("rehash_real_items")
def rehash_real_items():
    real_items = db.session.query(RealItems).all()
    print(len(real_items))
    for item in real_items:
        item.item_hash = make_item_hash(item)
        print(item.item_hash)
        db.session.add(item)
    db.session.commit()
