import os 
import sys
import pytest
from flask import session, url_for, template_rendered, request, Response, jsonify
from loggers import get_logger
topdir = os.path.join(os.path.dirname(__file__), "..")
sys.path.append(topdir)
from app import create_app
search_logger = get_logger("payments")
from models.data_models import db, Users, RealItems
from sqlalchemy.sql.expression import func


@pytest.fixture
def client():
    app = create_app()
    app_context = app.test_request_context()
    app_context.push()

    @app.route('/session/userid/<ID>')
    def set_user_id(ID):
        search_logger.debug("setting userid "+str(ID))
        session['user_id'] = int(ID)
        session['username'] = 'dylans-test-user'
        session['roles'] = ['guest']
        return jsonify({"message": "ID was set"})

    @app.route('/session/wordpressid/<ID>')
    def set_wordpress_id(ID):
        search_logger.debug("setting wp id "+str(ID))
        session['ID'] = int(ID)
        return jsonify({"message": "ID was set"})

    @app.route('/session/roles/<role>')
    def set_roles(role):
        search_logger.debug("setting roles "+role)
        session['roles'] = role
        return jsonify({"message": "role was set"})

    @app.route('/testing/users/logout')
    def logout():
        search_logger.debug("logging out")
        session.clear()
        return jsonify({"message": "logged out"})

    with app.test_client() as client:
        # with app.app_context():
        #     init_db()
        yield client


@pytest.mark.skip(reason="Not implemented yet")
def test_paypal_payout(client):
    #Not a priority
    pass

@pytest.mark.skip(reason="Not implemented yet")
def test_retrieve_payout(client):
    #Not a priority
    pass

@pytest.mark.skip(reason="Not implemented yet")
def test_add_to_cart(client):
    pass
    # # SETUP
    # # Get user id 
    # user_id = session['user_id']
    # shopping_session = get_shopping_session(user_id)

    # # Add Item to cart
    # # Use the mutation to add the item to the cart


    
    # #check if the cart THROUGH the shopping sessions has been added the item
    # # Select Serveral Items from Real Items to add into cart
    # items = db.session.query(RealItems).order_by(func.random).limit(5).all()
    # user_id = session['user_id']

    # # Make Add to Cart Request for the selected items
    # for item in items:
    #     response = client.post(url_for('add_to_cart', item_id=item.id, user_id=user_id))
    #     assert response.status_code == 200
        
    # # Get the cart of the user and check the items that were just added
    # cart = db.session.query(Cart).filter_by(user_id=user_id).first()
    # assert sorted(items) == sorted(cart.real_items)

    # # CLEANUP
    # # Remove the items from the cart
    # for item in items:
    #     response = client.post(url_for('remove_from_cart', item_id=item.id, user_id=user_id))
    #     assert response.status_code == 200

@pytest.mark.skip(reason="Not implemented yet")
def test_paypal_checkout(client):
    user_id = session['user_id']
    user = db.session.User.query.filter_by(id=user_id).first()

    #TODO: We are currently assuming that the registration email = paypal emai 
    user_email = user.email
    amount = 5.50

    #Make checkout request
    response = client.post()

    




