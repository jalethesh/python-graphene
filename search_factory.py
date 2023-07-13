from py import process
from graphql_service.generic_item_mutations import GenericItemArguments
from loggers import get_logger
from flask import Blueprint, render_template, request
import sys, time
sys.path.append('search/')
from search.fuzz_search_cli import run_search
import numpy as np
import requests
from flask import jsonify, redirect, url_for, session
from flask_wtf import FlaskForm
from security import user_is_logged_in
from wtforms import StringField, SubmitField, IntegerField, BooleanField
from wtforms.validators import DataRequired, Optional
from graph_factory import Query
from models.data_models import GenericItems, ListingFeedback, db, EbayListing
from datetime import datetime
import click
import pandas as pd
import multiprocessing
from sqlalchemy.sql.expression import func
from sqlalchemy import not_, or_, nullslast, exc
from functools import partial

search_logger = get_logger("searches")
search_factory = Blueprint("search", __name__, static_folder="static", template_folder="templates")

    
@search_factory.route('/search_query', methods=['GET'])
def search_for_id():
    #Check if query string is there
    input =  request.args.get('search_query')
    search_logger.info(f"searching for {input}")
    file_name = 'search/datasets/generic_items_raw_1801.csv'
    search_array = np.loadtxt(file_name, delimiter=',', usecols=range(0,7), unpack=True, dtype=str, skiprows=1)

    result_id = run_search(input, search_array, multi=True)
    match_index = np.where(search_array[0]==result_id)[0][0]
    return_payload = {
        "id": result_id,
        "name": str(search_array[1][match_index]),
        "rarity": search_array[2][match_index],
        "index_name": str(search_array[6][match_index])
    }
    return jsonify(return_payload)

class SearchForm(FlaskForm):
    search_query = StringField('search_query',validators=[DataRequired()])
    submit = SubmitField('Search')

@search_factory.route('/basic_search')
def basic_search():
    form = SearchForm(meta={'csrf': False})
    return render_template('search.html',form=form)

@search_factory.route('/search_result')
# Page where user is directed to for viewing of the search result
def search_result():
    data = request.args.get('search_query')
    response_id = run_search(data) #TODO: Refactor needed?

    #Make a GET request to the generic_items_table
    g_item = db.session.query(GenericItems).filter_by(id=response_id).first()
    return render_template('search_result.html', 
        result_id=g_item.id, 
        name=g_item.name, 
        rarity=g_item.rarity, 
        item_index=g_item.item_index, 
        image_uri_normal=g_item.image_uri_normal)


@search_factory.route('/for_validation/<int:id>', endpoint='for_validation_listing_id')
@user_is_logged_in
def for_validation_listing_id(id):
    # Get Ebay Listing
    ebay_listing = db.session.query(EbayListing).filter_by(database_id=id).first()

    if ebay_listing.predicted_generic_id is None:
        return "No prediction yet"

    if ebay_listing.predicted_generic_id_list is None:
        predicted_generic_ids = [ebay_listing.predicted_generic_id]
    else:
        predicted_generic_ids = list(ebay_listing.predicted_generic_id_list).insert(0, ebay_listing.predicted_generic_id)
    #Get all generic items that match the predicted generic id
    g_items = db.session.query(GenericItems).filter(GenericItems.id.in_(predicted_generic_ids)).all()
    
      #Handle Photos
    photo_urls = [ebay_listing.photo_url_1, 
        ebay_listing.photo_url_2, 
        ebay_listing.photo_url_3, 
        ebay_listing.photo_url_4, 
        ebay_listing.photo_url_5]

    photo_file_name = ebay_listing.photo_file_name
    if photo_file_name is not None:
        photo_file_name = photo_file_name.split('/')[1].split('.')[0].split('_')[0] #ebay_anxman_details/324745516667_1.jpg' -> '324745516667jpg
        photo_file_names = [photo_file_name +'_'+ str(i) + '.jpg' for i in range(1,6)]
        s3_urls = [f"https://s3.amazonaws.com/listing-images-pm/img_data/{file_name}" for file_name in photo_file_names]
    else:
        s3_urls = []
    
    # Check if each s3_url is valid, if not remove from the list
    num_processes = 5
   
    pool = multiprocessing.Pool(processes=num_processes)
    result = pool.map(get_status_code, s3_urls)
    pool.close()

    #Remove invalid urls
    valid_s3_urls = [x for x,y in zip(s3_urls,result) if y==200]

    content = {
        "generic_items": g_items,
        "listing_id": ebay_listing.database_id,
        "listing_title": ebay_listing.title,
        "winning_bid": ebay_listing.winning_bid,
        "seller_name": ebay_listing.seller_name,
        "num_of_bids": ebay_listing.number_of_bids,
        "listing_url": ebay_listing.url,
        "listing_date": ebay_listing.listing_date,
        "listing_photo_urls": photo_urls,
        "valid_s3_urls": valid_s3_urls,
    }

    return render_template('for_validation.html', content=content)


@search_factory.route('/for_validation', methods=['GET','POST'])
@user_is_logged_in
def for_validation():
    user_id = session['user_id']
    # TODO: Fit into single query with a JOIN + filter round listingfeedback and users 
    # Get listings where user has approved
    user_rated_listings = db.session.query(ListingFeedback.listing_id).filter(
        ListingFeedback.user_id==user_id).all()

    #Get the most expensive generic_items that have not been rated by the user
    ebay_listing = db.session.query(EbayListing).filter(
        EbayListing.database_id.notin_([x.listing_id for x in user_rated_listings])). \
        filter(EbayListing.winning_bid != None). \
        filter(EbayListing.predicted_generic_id != None). \
        order_by(EbayListing.winning_bid.desc()).limit(1).first()
    
    #If there is no listing, return
    if ebay_listing is None:
         return jsonify({"status": "failed", "message": "No listings to approve"})

    #Get predicted value
    predicted_generic_id = ebay_listing.predicted_generic_id
    if predicted_generic_id is None:
        return jsonify({"status": "failed", "message": "No predicted generic id"})

    #Get Sub predictions inside the predicted_generic_id_list columns
    try:
        sub_predictions = ebay_listing.predicted_generic_id_list
        if sub_predictions is None:
            predictions = [predicted_generic_id]
        else:
            sub_predictions = [int(x) for x in sub_predictions.split(",")]
            predictions = [predicted_generic_id] + sub_predictions

    except ValueError:
        search_logger.debug("No Sub predicitions")
        predictions = [predicted_generic_id]
        

    #Get the generic item(s)
    g_items = db.session.query(GenericItems.name, 
        GenericItems.rarity, 
        GenericItems.item_index,
        GenericItems.image_uri_normal,
        GenericItems.id).filter(
        GenericItems.id.in_(predictions)).limit(10).all()

    if g_items is None:
        return jsonify({"status": "failed", "message": "Could not match generic item"})
    elif isinstance(g_items, list):
        #Convert list of listings to a dictionary
        g_items = [dict(name=x.name, rarity=x.rarity, item_index=x.item_index, image_uri_normal=x.image_uri_normal, id=x.id) for x in g_items]
        # g_item = g_items.pop(0)
        # columns = list(g_item.keys())
        # sub_g_items = g_items

    #Handle Photos
    photo_urls = [ebay_listing.photo_url_1, 
        ebay_listing.photo_url_2, 
        ebay_listing.photo_url_3, 
        ebay_listing.photo_url_4, 
        ebay_listing.photo_url_5]

    photo_file_name = ebay_listing.photo_file_name
    if photo_file_name is not None:
        photo_file_name = photo_file_name.split('/')[1].split('.')[0].split('_')[0] #ebay_anxman_details/324745516667_1.jpg' -> '324745516667jpg
        photo_file_names = [photo_file_name +'_'+ str(i) + '.jpg' for i in range(1,6)]
        s3_urls = [f"https://s3.amazonaws.com/listing-images-pm/img_data/{file_name}" for file_name in photo_file_names]
    else:
        s3_urls = []
    
    # Check if each s3_url is valid, if not remove from the list
    num_processes = 5
   
    pool = multiprocessing.Pool(processes=num_processes)
    result = pool.map(get_status_code, s3_urls)
    pool.close()

    #Remove invalid urls
    valid_s3_urls = [x for x,y in zip(s3_urls,result) if y==200]

    # Put the content needed into a dict
    # Repack needed parameters
    content = {
        "generic_items": g_items,
        "listing_id": ebay_listing.database_id,
        "listing_title": ebay_listing.title,
        "winning_bid": ebay_listing.winning_bid,
        "seller_name": ebay_listing.seller_name,
        "num_of_bids": ebay_listing.number_of_bids,
        "listing_url": ebay_listing.url,
        "listing_date": ebay_listing.listing_date,
        "listing_photo_urls": photo_urls,
        "valid_s3_urls": valid_s3_urls,
    }

    return render_template('for_validation.html', content=content)

class ValidateListing(FlaskForm):
    listing_id = IntegerField('listing_id', validators=[DataRequired()])
    user_selected_generic_id = IntegerField('user_selected_generic_id', validators=[DataRequired()])
    user_comment = StringField('user_comment', validators=[Optional()])
    is_match = BooleanField('is_match', validators=[Optional()])


@search_factory.route('/validate_listing', methods=['POST'])
@user_is_logged_in
def validate_listing():
    #This updates the ebay_listing values
    form = ValidateListing(meta={'csrf': False})
    if form.validate_on_submit():
        listing_id = form.listing_id.data
        
        # If user clicks `Match`, the current predicted_generic_id is the user_selected_generic_id
        # Otherwise, the user_selected_generic_id is None
        if form.is_match.data:
            user_selected_generic_id = form.user_selected_generic_id.data
        else:
            user_selected_generic_id = None

        user_comment = form.user_comment.data
        search_logger.info("Validating listing")
        search_logger.info(f"listing_id: {listing_id}")
        search_logger.info(f"user_selected_generic_id: {user_selected_generic_id}")
        search_logger.info(f"user_comment: {user_comment}")
        
        #Update the listing
        ebay_listing = db.session.query(EbayListing).filter_by(database_id=listing_id).first()
    
        ebay_listing.user_approved = True
        # Create a new entry in the ListingFeedback table
        new_feedback = ListingFeedback(
            listing_id=listing_id,
            user_id=session['user_id'],
            user_comment=user_comment,
            user_selected_generic_id=user_selected_generic_id,
        )

        db.session.add(new_feedback)
        db.session.commit()
        return redirect(url_for('search.for_validation'))
            
    else:
        search_logger.debug(f"ERROR: Validate Listing form is Not Valid. {form.errors}")
        return redirect(url_for('search.for_validation'))


class SearchLogForm(FlaskForm):
    search_query = StringField('search_query',validators=[DataRequired()])
    predicted_id = IntegerField('predicted_id', validators=[DataRequired()])
    is_correct = BooleanField('is_correct')
    correct_id = IntegerField('correct_id', validators=[Optional()])
    date_created = IntegerField('date_created')
    submit = SubmitField('Search')

def get_status_code(url):
    # For multiprocessing_convenience
    # Returns the status code of url
    result = requests.head(url)
    return result.status_code


def process_chunk(chunk):
    # For import_ebay_listing multiprocessing to work, 
    # we need to pass the db processing function as a lambda

    for index, row in chunk.iterrows():            
        ### ROW MODIFICATIONS
        if row['Best Offer'] == 'No':
            best_offer = False
        elif row['Best Offer'] == 'Yes':
            best_offer = True
        else:
            print(f"Skipping row. Cannot Convert Best Offer {row['Best Offer']}to boolean")
            continue
        
        #Convert all values of pd.isnull to None
        row = row.where(pd.notnull(row), None)

        # Convert Winning Bid (US $10.10) format to a float value
        if row['Winning bid'] is not None:
            try:
                winning_bid = row['Winning bid']
                tags = ['GBP ', 'US $', 'C $', 'AU $'] #TODO Apply currency conversion
                for tag in tags:
                    winning_bid = winning_bid.replace(tag, '')
                    winning_bid = winning_bid.replace(',', '')
                row['Winning bid'] = float(winning_bid)
            except:
                print(f"Skipping row. Cannot convert Winning Bid {row['Winning bid']} to float")
                continue

        ### OBJECT MAPPING
        try:
            #Mapping to database structure
            ebay_listing = EbayListing(
                    url=row['URL'],
                    title=row['title'],
                    winning_bid=row['Winning bid'],
                    auction_type = row['TYPE'],
                    number_of_bids=row['No of Bids'],
                    best_offer=best_offer,
                    seller_name=row['Seller'],
                    seller_feedback=row['Seller Feedback'],
                
                    listing_date=row['Date'],
                    photo_url_1 = row['Photo 1 Url'],
                    photo_url_2 = row['Photo 2 Url'],
                    photo_url_3 = row['Photo 3 Url'],
                    photo_url_4 = row['Photo 4 Url'],
                    photo_url_5 = row['Photo 5 Url'],
                    photo_file_name = row ['Photo 1 Local'],
                    )

        except Exception as e:
            print(f"Skipping row. {e}")
            continue
        
        while True:
            try: 
                print(f"Trying to add to DB EbayID: {ebay_listing.database_id}")
                db.session.add(ebay_listing)
                db.session.commit()
                print(f"Added to database {ebay_listing.title}")
                search_logger.debug(f"Added to database {ebay_listing.title}")
                break
            except exc.IntegrityError as e:
                db.session.rollback()
                if 'duplicate key value violates unique constraint' in str(e):
                    # Get the largest id in the table\
                    max_id = db.session.query(func.max(EbayListing.database_id)).scalar()
                    ebay_listing.database_id = max_id + 1
                    print(f"adjusting max_id from {max_id} to {max_id+1}")
                    #search_logger.debug(f"adjusting max_id from {max_id} to {max_id+1}")

    
        # TODO Tried bulk_save but couldnt get it to work properly
        # Add to database
        # db.session.insert(ebay_listing)
        # db.session.commit()
    
    return True
        
@search_factory.cli.command('import_ebay_listing')
@click.option('--csv_file', default=None, help='The CSV file to import')
def import_ebay_listing(csv_file):

    if csv_file is None:
        return click.echo('Please provide a CSV file to import')

    #Get number of current listings:
    current_listings = db.session.query(EbayListing.database_id).count()
    
    # Create custom date parser to handle the date format in the csv
    custom_date_parser = lambda x: datetime.strptime(x, "%m/%d/%Y %H:%M %p")

    # Read The csv file
    df = pd.read_excel(csv_file,parse_dates=['Date'],date_parser=custom_date_parser)
    
    # Create as many processes as there are CPUs on your machine
    num_processes = multiprocessing.cpu_count()
    num_processes = 1
    # Calculate the chunk size as an integer
    chunk_size = int(df.shape[0]/num_processes)
    chunks = [df.iloc[df.index[i:i + chunk_size]] for i in range(0, df.shape[0], chunk_size)]
    cols= list(df.columns)


    # Check if columns match to expected
    exp_cols = ['URL','title','Winning bid','TYPE',
        'No of Bids','Best Offer','Seller','Seller Feedback',
        'Date','Photo 1 Url','Photo 1 Local','Photo 2 Url',
        'Photo 2 Local','Photo 3 Url','Photo 3 Local',
        'Photo 4 Url','Photo 4 Local','Photo 5 Url','Photo 5 Local']

    if cols != exp_cols:
        search_logger.debug('Columns do not match expected')
        return

    #Modify our session to be scoped session.
    from sqlalchemy.orm import scoped_session
    from flask import _app_ctx_stack
    from models.data_models import SessionLocal
    db.session = scoped_session(SessionLocal, scopefunc=_app_ctx_stack.__ident_func__)

    # create our pool with `num_processes` processes
    pool = multiprocessing.Pool(processes=num_processes)

    # apply our function to each chunk in the list
    ebay_objs = pool.map(process_chunk, chunks)
    pool.close()
    pool.join()
    # ret_val = process_chunk(df)
    # if not ret_val:
    #     search_logger.debug(f'Importing failed')
    new_listings = db.session.query(EbayListing.database_id).count()
    print(f'Done. Added {new_listings - current_listings} new listings')
    search_logger.debug(f'Done. Added {new_listings - current_listings} new listings')
    
    
@search_factory.cli.command('predict_ebay_listing')
@click.option('--number', '-n', type=int, default=None)
def predict_ebay_listing(number):
    tic = time.time()
    idx = 0

    #Pre loading the search_array so that run_search doens't have  to in every loop
    file_name = 'search/datasets/generic_items_raw_1801.csv'
    search_array = np.loadtxt(file_name, delimiter=',', usecols=range(0,7), unpack=True, dtype=str, skiprows=1)

    while True:
        # Get one ebay listing from the database
        ebay_listing = db.session.query(EbayListing).filter(EbayListing.title.isnot(None), EbayListing.predicted_generic_id.is_(None)).first()
        
        listing_title = ebay_listing.as_dict()['title']
        listing_id = ebay_listing.as_dict()['database_id']

        if ebay_listing is None: 
            search_logger.debug('Skipping row. Ebay Listing is None')
            continue
        if pd.isnull(listing_title): 
            search_logger.debug('Skipping row. Listing Title is None')
            continue

        # Make a search_query to run_search
        search_logger.info('Running search for: ' + listing_title)
        result_id =  run_search(listing_title, search_array)
        search_logger.info(f"Predicted result id: {result_id,}")

        # Update the database with the predicted result id
        ebay_listing.predicted_generic_id = result_id
        db.session.commit()
        print(f"Modified listing ID: {listing_id}")
        print(f"Listing ID Title: {listing_title}")
        print(f"Predicted result id: {result_id}")

        idx += 1
        if number is None:
            continue
        if idx >= number:
            break

    toc = time.time()
    search_logger.info(f'It took {toc-tic:.2f} seconds to run {idx} searches')


@search_factory.cli.command('predict_ebay_listing_multi')
@click.option('--number', '-n', help="How many number of searches to run", type=int, default=None)
@click.option('--processors', '-p', type=int, default=None)
@click.option('--multi', '-m', type=int, default=None, help="Number of results the search should return on each search")
def predict_ebay_listing_multi(number, processors, multi):
    tic = time.time()
    idx = 0

    #Pre loading the search_array so that run_search doens't have  to in every loop
    file_name = 'search/datasets/generic_items_raw_1801.csv'
    search_array = np.loadtxt(file_name, delimiter=',', usecols=range(0,7), unpack=True, dtype=str, skiprows=1)

    while True:
        if processors is None:
            num_processes = multiprocessing.cpu_count()
        elif processors <= 0:
            raise ValueError('Number of processors cannot be 0')
        else:
            num_processes = processors

        # Get multiple listing from the database
        ebay_listing_list = db.session.query(EbayListing).filter(EbayListing.title.isnot(None)) \
            .filter(or_(EbayListing.predicted_generic_id.is_(None), func.length(EbayListing.predicted_generic_id_list) <= 8)) \
            .order_by(nullslast(EbayListing.winning_bid.desc())).limit(num_processes).all()

        if len(ebay_listing_list) == 0:
            print("No more listings to predict")
            break 

        listing_titles=[]
        listing_ids=[]
        for listing in ebay_listing_list:
            if listing.as_dict()['title'] is not None or listing.as_dict()['title'] != "":
                listing_titles.append(listing.as_dict()['title'])
                listing_ids.append(listing.as_dict()['database_id'])
            else:
                search_logger.info(f"Skipping entry {listing.as_dict()['database_id']} as there is no title")

        # Add multiprocessing
        pool = multiprocessing.Pool(processes=num_processes)
        results = pool.map(partial(run_search,search_array=search_array, multi=multi), listing_titles)
        pool.close()
        
        for i, (result, listing) in enumerate(zip(results, ebay_listing_list)):

            if isinstance(result, str): #Assumes that a string is one result
                listing.predicted_generic_id = result
                search_logger.info(f"Modified listing ID: {listing_ids[i]}")
                search_logger.info(f"Listing ID Title: {listing_titles[i]}")
                search_logger.info(f"Predicted result id: {result[0]}")

                #Get generic Item info
                card_name = db.session.query(GenericItems.name).filter(GenericItems.id == result).first()
                search_logger.info(f"Predicted title: {card_name} \n")

            elif isinstance(result, list): #Assume that there are several resutls if this is list
                card_name =  db.session.query(GenericItems.name).filter(GenericItems.id.in_(result)).all()
                #The first result will be in listing.predicted_generic_id and the rest will be in listing.predicted_generic_id_list
                listing.predicted_generic_id = result[0]
                listing.predicted_generic_id_list = ','.join(result[1:])
                print(f"# of Sub predictions: {len(result)-1}")
                
            db.session.commit() #Db is being modified even without the db.session.commit()??
            print(f"Modified listing ID: {listing_ids[i]}")
            print(f"Listing ID Title: {listing_titles[i]}")
            print(f"Predicted result id: {result}")
            print(f"Predicted title: {card_name}")
            
            print("\n")
            idx+=1

        toc = time.time()
        search_logger.info(f'It took {toc-tic:.2f} seconds to run {idx} searches')
        print(f'It took {toc-tic:.2f} seconds to run {idx} searches')

        if number is None:
            continue
        if idx >= number:
            break




