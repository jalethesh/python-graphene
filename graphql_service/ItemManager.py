import time

import requests
from models.data_models import db, RealItems, GenericItems
from loggers import items_logger


class ItemManager:
    def __init__(self, real_item_id):

        self.real_item: RealItems = db.session.query(RealItems).filter_by(database_id=real_item_id).first()
        self.item: GenericItems = db.session.query(GenericItems).filter_by(id=self.real_item.item_id).first()
        # handlers are organized into a 2 layer hashmap, first layer is current state and second layer is next state
        # the value associated any layer 2 key is the function/events that happen as a result of that state change
        # SHIPPED PENDING_TRADE PENDING_SALE ARRIVED CANCELED DRAFT PRESCAN PUBLISH PUSH_LIVE RESERVED
        # SHIPPED SOLD TO_SCAN TRADE_ARRIVING
        self.handlers = {
            'NEW': {
                'TRADE_ARRIVING': self.new_to_trade_arriving
            },
            'TRADE_ARRIVING': {
                'ARRIVED': self.trade_arriving_to_arrived
            },
            'ARRIVED': {
                'PRE_SCAN': self.arrived_to_pre_scan
            },
            'PRE_SCAN': {
                'TO_SCAN': self.pre_scan_to_to_scan
            },
            'TO_SCAN': {
                'PRINT_QR': self.to_scan_to_print_qr
            },
            'PRINT_QR': {
                'DRAFT': self.print_qr_to_draft
            },
            'DRAFT': {
                'PUSH_LIVE': self.draft_to_push_live
            },
            'PUSH_LIVE': {
                'PUBLISH': self.pre_scan_to_to_scan
            },
        }

    def update_status(self, status, testing=False):
        print(f"updating {self.real_item.status} to {status}")
        transaction_update_actions = self.handlers[self.real_item.status][status]
        items_logger.debug(f"updating {self.real_item} to {status}")
        transaction_update_actions(testing=testing)
        db.session.add(self.real_item)
        db.session.commit()

    def new_to_trade_arriving(self, testing=False):
        self.real_item.status = 'TRADE_ARRIVING'

    def trade_arriving_to_arrived(self, testing=False):
        self.real_item.status = 'ARRIVED'

    def arrived_to_pre_scan(self, testing=False):
        self.real_item.status = 'PRE_SCAN'

    def pre_scan_to_to_scan(self, testing=False):

        # request to integromat endpoint - pre_scan to scan dev
        # https://www.integromat.com/scenario/2879114/edit
        integromat_endpoint = "https://hook.integromat.com/ons3dupw3gjj5dmh68yji3zh5ujtk929"
        if not testing:
            requests.get(integromat_endpoint,
                     params={'sku': self.real_item.sku,
                             'url': f"https://juzam.purplemana.com/assets/{str(self.real_item.database_id)}",
                             'condition': self.real_item.condition,
                             'set': self.item.set,
                             'name': self.item.name
                     })
        self.real_item.qr_url = f"https://purplemana-media.s3.us-west-1.amazonaws.com/dev/images/newscanner/qr/" \
                                f"{self.real_item.sku}.png"
        self.real_item.qr_label_url = f"https://purplemana-media.s3.us-west-1.amazonaws.com/dev/images/newscanner/" \
                                f"{self.real_item.sku}/qr_label_{self.real_item.sku}.jpg"
        self.real_item.status = 'TO_SCAN'

    def to_scan_to_print_qr(self, testing=False):
        # print out QR label
        url = "https://hook.integromat.com/21diinamf4lhd7arygaqu9d9kc7tzo41"

        params = {
            'qr_url': self.real_item.qr_label_url,
            'filename': f'qr-label-{self.real_item.sku}'
        }
        if not testing:
            requests.get(url, params=params)
        self.real_item.status = 'PRINT_QR'

    def print_qr_to_draft(self, testing=False):
        self.real_item.status = 'DRAFT'

    def draft_to_push_live(self, testing=False):
        self.real_item.status = 'PUSH_LIVE'







