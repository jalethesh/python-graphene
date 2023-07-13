import json
import os
import time
from datetime import datetime

import boto3
import botocore
import requests
from flask import session

from graphql_service.ItemManager import ItemManager
from items_factory import update_item_list_on_real_item_mutation
from media_factory import time_hash
from models.data_models import db, Transactions, TransactionItems, RealItems, Notifications, ItemCollections, Users, \
    GenericItems, ItemLists
from typing import List, Dict
from security import user_is_admin, user_is_logged_in
from loggers import get_logger
transaction_logger = get_logger("transactions")


class TransactionManager:
    def __init__(self, transaction_id):
        self.transaction_id = transaction_id
        self.transaction: Transactions = db.session.query(Transactions).filter_by(database_id=transaction_id).first()
        self.transaction_items: List[TransactionItems] = db.session.query(TransactionItems).filter_by(transaction_id=self.transaction_id).all()
        self.user: Users = db.session.query(Users).filter_by(database_id=self.transaction.left_owner).first()
        self.real_items: List[RealItems] = db.session.query(RealItems).filter(RealItems.database_id.in_([x.real_item_id for x in self.transaction_items])).all()
        self.item_managers: Dict[str] = {str(x.database_id): ItemManager(x.database_id) for x in self.real_items}
        # handlers are organized into a 2 layer hashmap, first layer is current state and second layer is next state
        # the value associated any layer 2 key is the function/events that happen as a result of that state change
        self.handlers = {
            'PURPLEMANA_REVIEW': {
                'TRADEIN_ARRIVING': self.purplemana_review_to_tradein_arriving,
                'CLIENT_REVIEW': self.purplemana_review_to_client_review
            },
            'CLIENT_REVIEW': {
                'PURPLEMANA_REVIEW': self.client_review_to_purplemana_review,
            },
            'TRADEIN_ARRIVING': {
                'ARRIVED': self.tradein_arriving_to_arrived
            },
            'ARRIVED': {
                'GRADING': self.arrived_to_grading
            },
            'GRADING': {
                'GRADED': self.grading_to_graded,
            },
            'GRADED': {
                'FINAL_CLIENT_REVIEW': self.graded_to_final_client_review
            },
            'FINAL_CLIENT_REVIEW': {
                'FINAL_PM_REVIEW': self.final_client_review_to_final_pm_review
            },
            'FINAL_PM_REVIEW': {
                'CREDIT_ISSUED': self.final_pm_review_to_credit_issued
            },
        }

    def update_status(self, status, testing=False):
        # permissions: only user/admin have access to update state for owned/any transactions
        print(f"updating {self.transaction.status} to {status}")
        transaction_update_actions = self.handlers[self.transaction.status][status]
        transaction_logger.debug(f"updating {self.transaction_id} to {status}")
        for item in self.real_items:
            item.transaction_status = status
            db.session.add(item)
        db.session.add(self.transaction)
        db.session.commit()
        transaction_update_actions(testing=testing)

    @user_is_logged_in
    def client_review_to_purplemana_review(self, testing=False):
        # transactions will be created in this state
        # entrypoint: user submits the buylist to PM
        # actions: send email to Anx to review transaction
        self.transaction.status = 'PURPLEMANA_REVIEW'
        db.session.add(self.transaction)
        db.session.commit()

    @user_is_admin
    def purplemana_review_to_client_review(self, testing=False):
        self.transaction.status = 'CLIENT_REVIEW'
        db.session.add(self.transaction)
        db.session.commit()

    @user_is_admin
    def purplemana_review_to_tradein_arriving(self, testing=False):
        # entrypoint: Admin clicks approve while transaction in purplemana_review state
        # actions: user is provided shipping details including invoice

        # purplemana_add_inventory_dev_discord
        # posts to discord for each item being received by purplemana
        trade_purplemana_add_inventory_endpoint = "https://hook.integromat.com/31bpxoowweks6qwe58q4jxn8yfpf4nj7"
        content = []
        invoice_items = []
        date = datetime.now()
        transaction_logger.debug(self.transaction.as_dict())
        for i, transaction_item in enumerate(self.transaction_items):
            transaction_logger.debug(transaction_item.as_dict())
            real_item: RealItems = db.session.query(RealItems).filter_by(database_id=transaction_item.real_item_id).first()
            generic_item: GenericItems = db.session.query(GenericItems).filter_by(id=real_item.item_id).first()
            real_item.status = 'TRADE_ARRIVING'
            real_item.sku = f"AP-{str(date.month).zfill(2)}{str(date.day).zfill(2)}{date.year}-{real_item.database_id}"
            real_item.total_costs = real_item.fmv
            db.session.add(real_item)
            datum = f""" -TESTING-
            Trade-in accepted! I am adding this card to inventory:
            transaction_id: {str(transaction_item.transaction_id)}
            trade_in_value: {str(transaction_item.trade_in_value)}
            index: {generic_item.item_index}
            condition: {real_item.condition}
            FMV (fair market value): {str(real_item.fmv)}
            """
            content.append(datum)
            if not transaction_item.trade_in_value:
                transaction_logger.warning(f"item is buylisted with no transaction in value {real_item} #{self.transaction.database_id}")
                transaction_item.trade_in_value = 0.01
            invoice_items.append(json.dumps({'item_index': generic_item.item_index, 'condition': real_item.condition,
                                             'trade_in_value': round(transaction_item.trade_in_value, 2), 'id': real_item.database_id}))

        def sort_by_key(s):
            invoice_dict = json.loads(s)
            return invoice_dict['trade_in_value']

        invoice_items.sort(key=lambda x: -sort_by_key(x))

        db.session.commit()
        params = {'discord_posts': content}
        if not testing:
            requests.get(trade_purplemana_add_inventory_endpoint, params=params)
        transaction_logger.debug(f"using these items to generate invoice {invoice_items}")
        self.transaction.status = 'GENERATE_INVOICE'
        db.session.add(self.transaction)
        db.session.commit()

        #   transaction generate invoice - https://www.integromat.com/scenario/2754290/edit
        #       send email to customer with shipping details
        # prepare items and s3 url for invoice, then pass key to integromat to do upload
        bucket_name = 'pm-invoices'
        filename = 'invoice_'+os.path.basename(time_hash())
        key = str(self.user.database_id) + "/" + str(self.transaction_id) + "/" + filename
        config = botocore.client.Config(signature_version=botocore.UNSIGNED)
        object_url = boto3.client('s3', config=config)\
                          .generate_presigned_url('get_object', ExpiresIn=0, Params={'Bucket': bucket_name, 'Key': key})
        # TRADE_GENERATE_INVOICE dev hook
        generate_invoice_hook = "https://hook.integromat.com/ekfpagpkjc5rlp3stdhlm2r4xktaev6s"
        print("email", self.user.email)
        email_or_trashcan = self.user.email if self.user.email else "dylan.adams@purplemana.com"
        variables = {'trade_qr': '', 'client_name': self.user.username, 'Template': 24324,
                     'client_email': email_or_trashcan, 'invoice_number': self.transaction.database_id,
                     'trade_in_total': self.transaction.right_credit, 'client_address1': self.user.email,
                     'client_address2': '', 's3_invoice_folder': object_url, 's3_invoice_filename': filename,
                     }
        data = {"invoice_item": invoice_items}
        print('=&'.join(variables.keys()))
        # if not testing:
        requests.post(generate_invoice_hook, params=variables, data=data)
        transaction_logger.debug(f"invoice generator endpoint GET completed with these params {variables}")
        self.transaction.status = 'MAKE_SHIPPING_LABEL'
        db.session.add(self.transaction)
        db.session.commit()
        
        # local GET to shippo API and receive shippo parcel ID - store in transaction
        test_token = os.getenv('SHIPPO_TOKEN')
        # from_name, from_address_1, from_address_2, from_address_3, from_address_city, from_address_state, from_address_country
        # to_name, to_address_1, to_address_2, to_address_3, to_address_city, to_address_state, to_address_country, to_email
        # purplemana skus
        # buyer_requested_shipping: usps_first, usps_priority, ups_second_day_air, ups_next_day_air, usps_first
        # extra: signature confirmed result
        # signature decision if usps_first
        # signature decision for if order is > 500
        # signature decision if buy requests signature confirmation with shipping

        url = "https://api.goshippo.com/shipments/"
        test_token = os.getenv('SHIPPO_TOKEN')
        headers = {"Authorization": f"ShippoToken {test_token}", "Content-Type": "application/json"}

        content = {
            "address_from": {
                "name": f"{self.user.real_name}",
                "street1": f"{self.user.address_line_one}",
                "street2": f"{self.user.address_line_two}",
                "city": f"{self.user.address_city}",
                "state": f"{self.user.address_state}",
                "zip": f"{self.user.address_zipcode}",
                "country": f"{self.user.address_country}"
            },
            "address_to": {
                "name": "Ankur Pansari",
                "street1": "PMB #143 1459 18TH ST",
                "street2": "Purplemana",
                "city": "San Francisco",
                "state": "CA",
                "zip": "94107",
                "country": "USA"
            },
            "parcels": [{
                "length": "6",
                "width": "4",
                "height": "2",
                "distance_unit": "in",
                "weight": "2",
                "mass_unit": "oz"
            }],
            "extra": {
                "signature_confirmation": "ADULT"
            },
            "async": "false"
        }

        res = requests.get(url, data=content, headers=headers)
        print(res)

        # extract rate id
        # extract amount

        # make request to /transactions to get parcel code

        # https://api.goshippo.com/transactions

        self.transaction.status = 'TRADEIN_ARRIVING'
        db.session.add(self.transaction)
        db.session.commit()

    @user_is_admin
    def tradein_arriving_to_arrived(self, testing=False):
        for i, transaction_item in enumerate(self.transaction_items):
            transaction_logger.debug(transaction_item.as_dict())
            real_item: RealItems = db.session.query(RealItems).filter_by(database_id=transaction_item.real_item_id).first()
            handler = ItemManager(real_item.database_id)
            print("updating item", transaction_item)
            try:
                handler.update_status('ARRIVED')
            except Exception as ex:
                print(ex)


        for i, transaction_item in enumerate(self.transaction_items):
            real_item: RealItems = db.session.query(RealItems).filter_by(
                database_id=transaction_item.real_item_id).first()
            real_item.status = 'PRE_SCAN'
            db.session.add(real_item)

        # commit all changes first, then try updating them 1 by 1 to TO_SCAN
        db.session.commit()

        for i, transaction_item in enumerate(self.transaction_items):
            real_item: RealItems = db.session.query(RealItems).filter_by(
                database_id=transaction_item.real_item_id).first()
            item_manager = ItemManager(real_item_id=real_item.database_id)
            item_manager.update_status('TO_SCAN')
            db.session.add(real_item)
        self.transaction.status = 'ARRIVED'
        db.session.add(self.transaction)
        db.session.commit()

    @user_is_admin
    def arrived_to_grading(self, testing=False):

        for i, transaction_item in enumerate(self.transaction_items):
            real_item: RealItems = db.session.query(RealItems).filter_by(
                database_id=transaction_item.real_item_id).first()
            item_manager = ItemManager(real_item_id=real_item.database_id)
            qr_ready = requests.get(real_item.qr_label_url).status_code == 200
            if not qr_ready and not testing:
                raise Exception("qr url not valid, try again in a minute or update qr_label_url", real_item.qr_label_url)
            item_manager.update_status('PRINT_QR', testing=testing)
            db.session.add(real_item)
        self.transaction.status = 'GRADING'
        db.session.add(self.transaction)
        db.session.commit()

    @user_is_admin
    def grading_to_graded(self, testing=False):
        self.transaction.status = 'GRADED'
        db.session.add(self.transaction)
        db.session.commit()

    @user_is_admin
    def graded_to_final_client_review(self, testing=False):
        self.transaction.status = 'FINAL_CLIENT_REVIEW'
        db.session.add(self.transaction)
        db.session.commit()

    @user_is_logged_in
    def final_client_review_to_final_pm_review(self, testing=False):
        if session['user_id'] != self.transaction.left_owner:
            raise Exception("client must approve here, not admin")
        self.transaction.status = 'FINAL_PM_REVIEW'
        db.session.add(self.transaction)
        db.session.commit()

    @user_is_admin
    def final_pm_review_to_credit_issued(self, testing=False):

        transaction_logger.debug(f"updating ownership of transaction items {self.transaction_items}")
        for i, transaction_item in enumerate(self.transaction_items):
            transaction_logger.debug(transaction_item.as_dict())
            real_item: RealItems = db.session.query(RealItems).filter_by(
                database_id=transaction_item.real_item_id).first()
            real_item.owner = self.transaction.right_owner
            new_owner_collection = db.session.query(ItemCollections).filter_by(
                user_id=self.transaction.right_owner).first()
            new_owner_item_list = ItemLists(database_id=296)
            previous_item_list_id = real_item.item_list_id
            real_item.item_list_id = new_owner_item_list.database_id
            real_item.item_collections_id = new_owner_collection.database_id
            update_item_list_on_real_item_mutation(previous_item_list_id)
            update_item_list_on_real_item_mutation(new_owner_item_list.database_id)
            db.session.add(real_item)
            db.session.commit()

        if self.user.credit:
            self.user.credit += self.transaction.right_credit
        else:
            self.user.credit = self.transaction.right_credit
        db.session.add(self.user)
        self.transaction.status = 'CREDIT_ISSUED'
        db.session.add(self.transaction)
        notification_text = f'Trade# {self.transaction.database_id} has completed, ${self.transaction.right_credit} was added to your account'
        user_notification = Notifications(user_id=self.user.database_id, message=notification_text,
                                          date_created=datetime.now())
        db.session.add(user_notification)
        db.session.commit()
        transaction_logger.debug(f"credit issued and trade sequence completed #{self.transaction.database_id}")








