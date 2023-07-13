import json

import requests
from .util import get_real_item, set_user_to_customer


def get_image():
    # grab image from internet for upload test
    r = requests.get("https://purplemana-media.s3.amazonaws.com/12/243532/zz__AP-122720-1-front-deskew.jpg", stream=True)
    path = './tests/test_image.jpg'
    if r.status_code == 200:
        with open(path, 'wb') as f:
            for chunk in r:
                f.write(chunk)
    return path


def _upload(client):
    set_user_to_customer(client)
    path = get_image()
    print("downloaded image")
    # pick out real item belonging to test user
    real_item = get_real_item(client)
    print(real_item)
    # craft file upload request
    upload_url = f"https://localhost:5000/upload?labels=testing&real_item_id={real_item['databaseId']}"
    print("uploading to", upload_url)
    data = {'file': open(path, 'rb')}

    # do upload
    res = client.post(upload_url, data=data, content_type='multipart/form-data')
    data = json.loads(res.data.decode('utf-8'))
    print(data)
    # query database for file url
    # download file with get request
    # compare file hashes
