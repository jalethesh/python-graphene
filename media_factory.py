import hashlib
import logging
import os
import time
import magic
from flask import Blueprint, request, flash, jsonify, session
from werkzeug.utils import redirect
from security import user_is_logged_in
from models.data_models import RealItems, db, Media
from models.data_models import Users
import boto3
import botocore


media_factory = Blueprint("media", __name__, static_folder="static", template_folder="templates")


def allowed_file(filename):
    bool_allowed = '.' in filename and filename.rsplit('.', 1)[1].lower() in ['png', 'jpg', 'jpeg']
    print(filename, bool_allowed, filename.rsplit('.', 1)[1].lower())
    return bool_allowed


# post request from front end
# can do a get request to see a simple file upload form
@media_factory.route('/upload', methods=['GET', 'POST'])
@user_is_logged_in
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            print("no file found!")
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            print("no filename found!")
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            logging.debug("passed file name check")
            logging.debug(f"found real id {request.args.get('real_item_id')} and labels {request.args.get('labels')}")
            f = magic.Magic()
            file.save('./uploaded_image')
            file = open('./uploaded_image', 'rb')
            filetype = f.from_file('./uploaded_image')
            logging.debug(f"file is determined to be {filetype}")
            try:
                if 'PNG' not in filetype and 'JPEG' not in filetype and 'JPG' not in filetype:
                    raise Exception("file not a PNG, JPEG, or JPG")
            except Exception as ex:
                logging.debug(str(ex))
                return jsonify({"message": f"file was found to be {filetype}, only JPG, JPEG, and PNG are allowed"})
            try:
                real_item_id = request.args.get('real_item_id')
                if not real_item_id or real_item_id is None or real_item_id == 'None':
                    raise Exception("no real item id provided")
                labels = request.args.get('labels')
                if not labels or labels is None or labels == 'None':
                    raise Exception("no labels provided")
                image_url = external_add_media(real_item_id, file, labels)
            except Exception as ex:
                logging.debug(str(ex))
                return jsonify({"debug": "upload to s3 failed, "})
            return jsonify({"url": image_url})
        return jsonify({"message": "file wasn't uploaded"})

    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File (png or jpg)</h1>
    <form method=post enctype=multipart/form-data>
      <input type=file name=file>
      <input type=submit value=Upload>
    </form>
    '''


def time_hash():
    hash = hashlib.sha1()
    hash.update(str(time.time()).encode('utf-8'))
    return hash.hexdigest()


@user_is_logged_in
def external_add_media(real_item_id, media_file, label):
    user = db.session.query(Users).filter_by(database_id=session['user_id']).first()
    real_item = db.session.query(RealItems).filter_by(database_id=real_item_id).first()
    if real_item.owner != user.database_id and 'administrator' not in session['roles']:
        raise Exception("user must own the item they are uploading images for")

    s3 = boto3.Session().resource('s3')

    label_hash = label+"_"+os.path.basename(time_hash())
    bucket_name = 'purplemana-media'
    key = str(user.database_id) + "/" + str(real_item.item_id) + "/" + label_hash

    # upload the file and set the content type
    bucket = s3.Bucket(bucket_name)
    bucket.upload_fileobj(media_file, key, ExtraArgs={'ContentType': "image/jpeg", 'ACL': "public-read"})

    # get the public url
    config = botocore.client.Config(signature_version=botocore.UNSIGNED)
    object_url = boto3.client('s3', config=config).generate_presigned_url('get_object', ExpiresIn=0,
                                                                          Params={'Bucket': bucket_name, 'Key': key})
    print(object_url)

    new_media = Media(type="image", label=label, media_url=object_url, realitem_id=real_item.database_id)
    db.session.add(new_media)
    db.session.commit()

    return object_url


@user_is_logged_in
def external_remove_media(media_id):
    user = db.session.query(Users).filter_by(database_id=session['user_id']).first()
    media_item = db.session.query(Media).filter_by(database_id=media_id).first()
    if not media_item:
        raise Exception(f"Media item with media_id={media_id} was not found to delete")

    real_item = db.session.query(RealItems).filter_by(database_id=media_item.realitem_id).first()
    print(user, media_item, real_item)
    if real_item.owner != user.database_id and 'administrator' not in session['roles']:
        raise Exception("user must be admin or own the item to update/delete connected media")

    url = media_item.media_url

    bucket_name = 'purplemana-media'
    key = url.split('.com/')[1]
    print(key)

    s3 = boto3.resource('s3')
    s3.Object(bucket_name, key).delete()
