
01/27/2022
1. Main search algorithm now takes in the `multi` argument (default:None).
    This will return a list of integers (Instead of 1 integer value without multi arg)
    

01/24/2022

1. You can now run `flask search predict_ebay_listing` 
    which queries an entry from db.EbayListing and runs a prediction with it.
    Then updates the listing with a prediction_id.
    #TODO: Runs 1 by 1. Apply multiprocessing 
    #TODO: Runs slow. Around 0.7s /search. Speed up

2. Visit the `/for_validation` page which will random query an entry from db.EbayListing who has a prediction_id.
    The listing's info will be displayed on the page alongside the generic_items info matched by the prediction_id.
    User can then confirm that the listing matches the prediction_id and write commments and can submit a user_selected_id.
    #TODO: No user integration yet. CSRF Token bypassed
    #TODO: user_selected_id has no history. Once a user overwrites it, the previous id will be lost. Come up with second table


01/20/202
To run a string search on the generic_items db

# Note current version takes item from csv file. 
# TODO load the data from psql table

1. Run the fuzz_search_cli.py using:
    `python3 search/fuzz_search_cli.py`

    The program will then prompt you for a string to search on
    and will return the matched Card Name and its corresponding ID

Arguments:
You can also run the fuzz_search_cli.py with parameters such as:
    --input / -i: Input the string directly upon launch
    --keep_open: After the first search, ask the user again for a search query


Testing:
Current test file for the cli is in `tests/test_search.py`