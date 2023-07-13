import os

import requests
from models.data_models import Users


def test_get():
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
    headers = {"Authorization": test_token, "Content-Type": "application/json"}
    user = Users(real_name='Dylan Adams', address_line_one='2763 S Norfolk', address_city='San Francisco', address_zipcode='94403')
    content = {
        "address_from": {
            "name": f"{user.real_name}",
            "street1": f"{user.address_line_one}",
            "street2": f"{user.address_line_two}",
            "city": f"{user.address_city}",
            "state": f"{user.address_state}",
            "zip": f"{user.address_zipcode}",
            "country": f"{user.address_country}"
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
    return res, res.content, res.text