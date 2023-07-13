from models.data_models import db, ItemLists, RealItems, Transactions
from tests.graphql_example_requests.ex_realItems import upd_real_item_userlist, upd_real_item_item_list_id
from .test_real_items import update_real_item, delete_real_item
from .util import set_user_to_customer, set_user_to_admin, create_real_item, get_users_item_list
import json
from tests.graphql_example_requests.ex_transactions import *


def update_real_item_item_list(client, real_item, item_list_id=0):
    mutation = upd_real_item_item_list_id
    variables = {"databaseId": real_item['databaseId'], "itemListId": item_list_id}
    url = f'http://localhost:5000/graphql-api?query={mutation}&variables={json.dumps(variables)}'
    res = client.post(url)
    data = json.loads(res.data.decode('utf-8'))
    print('update real item returns', data)
    result_ok = data['data']['updateRealItem']['ok']
    assert result_ok
    assert data['data']['updateRealItem']['realItem']['itemListId'] == item_list_id
    return result_ok


def create_transaction(client, item_list_id=0, return_object=False):
    # create a transaction
    print("creating transaction...")
    mutation = make_transaction
    variables = {'itemListId': item_list_id}
    print(variables)
    url = f'http://localhost:5000/graphql-api?query={mutation}&variables={json.dumps(variables)}'
    res = client.post(url)
    data = json.loads(res.data.decode('utf-8'))
    print(data)
    result = data['data']['createTransaction']
    assert result['ok']
    transaction_id = int(result['transaction']['databaseId'])
    assert transaction_id > 0
    print(result['transaction'])
    if return_object:
        return result['transaction']
    else:
        return transaction_id


def delete_transaction(client, transaction_id):
    # delete a transaction - should this cascade to delete the transaction items as well? probably
    print("deleting transaction")
    mutation = del_transaction
    variables = {'transactionId': transaction_id}
    url = f'http://localhost:5000/graphql-api?query={mutation}&variables={json.dumps(variables)}'
    res = client.post(url)
    data = json.loads(res.data.decode('utf-8'))
    print(data)
    result = data['data']['deleteTransaction']
    assert result['ok']


def update_transaction_status(client, transaction_id, status='PURPLEMANA_APPROVE'):
    print("updating transaction status")
    mutation = upd_transaction_status
    variables = {'transactionId': str(transaction_id), 'status': status, 'testing': True}
    url = f'http://localhost:5000/graphql-api?query={mutation}&variables={json.dumps(variables)}'
    res = client.post(url)
    data = json.loads(res.data.decode('utf-8'))
    print(data)
    result = data['data']['updateTransactionStatus']
    assert result['ok']


def CRUD_transactions(client):
    set_user_to_customer(client, log_string='crud transactions')
    item_list = get_users_item_list(client)
    item_list_id = item_list['databaseId']
    real_item = create_real_item(client, 301506, itemListId=item_list_id, return_object=True)
    transaction_id = create_transaction(client, item_list_id=item_list_id)
    delete_transaction(client, transaction_id)
    set_user_to_admin(client, 'crud transactions teardown')
    delete_real_item(client, real_item['databaseId'])


def user_story_setup(client):

    set_user_to_customer(client, log_string='normal seq transactions')
    item_list = get_users_item_list(client)
    item_list_id = item_list['databaseId']

    real_item = create_real_item(client, 301506, itemListId=item_list_id, return_object=True)

    new_real_item = create_real_item(client, 301506, itemListId=item_list_id, return_object=True)

    transaction = create_transaction(client, item_list_id=item_list_id, return_object=True)

    return {'item_list': item_list, 'real_items': [real_item, new_real_item], 'transaction': transaction}


def tear_down(client, setup_data, transaction_id=0):
    set_user_to_admin(client, log_string='teardown')

    try:
        transaction = db.session.query(Transactions).filter_by(database_id=transaction_id).first()
        transaction.status = 'CLIENT_REVIEW'
        db.session.add(transaction)
        db.session.commit()
    except Exception as ex:
        print(ex)

    for item in setup_data['real_items']:
        delete_real_item(client, item['databaseId'])
        # # get admin user id
        # id = 18
        # # get admin item lists
        # admin_lists = db.session.query(ItemLists).filter_by(user_id=id).all()
        # item_list = random.choice(admin_lists)
        # # pick list randomly and assign item to list
        # item: RealItems = db.session.query(RealItems).filter_by(database_id=item['databaseId']).first()
        # item.item_list_id = item_list.database_id
        # db.session.add(item)
        # db.session.commit()

    delete_transaction(client, setup_data['transaction']['databaseId'])


def normal_sequence(client):
    # this test is for the happy path

    # user submits transaction -> PURPLEMANA_REVIEW
    setup_data = user_story_setup(client)
    transaction_id = setup_data['transaction']['databaseId']

    # admin approves transaction -> TRADEIN ARRIVING
    set_user_to_admin(client)
    update_transaction_status(client, transaction_id, status='TRADEIN_ARRIVING')

    # cards arrive -> ARRIVED
    update_transaction_status(client, transaction_id, status='ARRIVED')

    # cards start grading -> GRADING
    update_transaction_status(client, transaction_id, status='GRADING')

    #
    update_transaction_status(client, transaction_id, status='GRADED')

    # cards finish grading, sent to client for final review -> FINAL_CLIENT_REVIEW
    update_transaction_status(client, transaction_id, status='FINAL_CLIENT_REVIEW')

    # user accepts grading -> FINAL_PM_REVIEW
    set_user_to_customer(client)
    update_transaction_status(client, transaction_id, status='FINAL_PM_REVIEW')

    # pm confirms final details -> CREDIT_ISSUED
    set_user_to_admin(client)
    update_transaction_status(client, transaction_id, status='CREDIT_ISSUED')

    # delete real items
    # delete transaction items
    # delete transaction logs
    # delete transaction
    tear_down(client, setup_data, transaction_id=transaction_id)


def approved_transaction_items_should_not_be_updateable(client):

    setup_data = user_story_setup(client)
    transaction_id = setup_data['transaction']['databaseId']
    real_item = setup_data['real_items'][0]

    set_user_to_admin(client)
    update_transaction_status(client, transaction_id, status='TRADEIN_ARRIVING')

    # try to update item that is in TRADEIN_ARRIVING status, should fail
    set_user_to_customer(client, log_string='check client fails transaction update')
    result_ok = update_real_item(client, real_item['databaseId'], do_assert=False)
    assert not result_ok

    set_user_to_admin(client)
    result_ok = update_real_item(client, real_item['databaseId'], do_assert=False)
    assert not result_ok

    # delete transaction items
    # delete transaction
    # delete real_items
    tear_down(client, setup_data, transaction_id=transaction_id)






