from sys import flags
from thefuzz import fuzz, process
from collections import Counter
import numpy as np
import csv, re, time, os
import pandas as pd
from search_arrays import STOP_WORDS, SET_TYPES, RARITY, SET_NAMES, YEARS
import click

def trim_strings(text, array=None, length=None):
    # Remove words using array
    if array is None:
        text = remove_words(text)
    else:
        text = remove_words(text, array)
    text = remove_special_characters(text) # Remove Special Characters

    if length is None:
        length = 1
    text = remove_characters_of_length(text, length=length) # Remove Characters of length x
    
    return text

def remove_words(text, array=STOP_WORDS):
    text = text.lower()
    return ' '.join([w for w in text.split() if w not in array])

def remove_special_characters(text):
    return(re.sub(r"[^a-zA-Z0-9]+", ' ', text))

def remove_characters_of_length(text, length=1):
    return ' '.join([w for w in text.split() if len(w) > length])

def exact_word_matching(text: str, compare_text:list):
    # Return the amount of time there are similar words in 
    words = text.split(' ')
    compare_text =  compare_text.split(' ')
    score = len(list(set(words) & set(compare_text)))
    return score

def run_search(input, search_array:np = None, multi:int = None):
    """
    Function Input: 
    input: string | Run search input
    search_array: np | Search array to compare against. If None provided, will use default search array
    multi: int | If multi is provided, will return a list of all the matches. If not, will return the first match

    Run the search using filtering and Fuzzy matching
    Once a match is found, return the generic item ID
    
    This functiona assumes that the search_array columns are as follows
    search_array[0]: is the item_id
    search_array[1]: name of card
    search_array[2]: rarity
    search_array[3]: keywords
    search_array[5]: set_type
    search_array[4]: set_name
    search_array[6]: item_index
    """
    if search_array is None:
        # Use the generic items list on file
        #Load the generic_items_full.csv into a numpy array. 
        # TODO # Change this to querying the DB. Has to be efficient
        file_name = 'search/datasets/generic_items_raw_1801.csv'
        search_array = np.loadtxt(file_name, delimiter=',', usecols=range(0,7), unpack=True, dtype=str, skiprows=1)

    if input == None:
        input = click.prompt('Please enter your search string here', type=str)

    tmp_a = list(zip(search_array[1], search_array[2], search_array[4], search_array[5]))
    arr_generic_items = [' '.join(x) for x in tmp_a] #Combine each item into one string

    ## Get rarity and set_type features from the ebay listing
    item=input
    item = remove_special_characters(item)
    item_split = item.lower().split(' ')
    item_split = [word for word in item_split if not word in STOP_WORDS]
    rarity = [word for word in item_split if word in RARITY] # Rarity Check
    set_type = [word for word in item_split if word in SET_TYPES] #Set Check
   
    # Filter the items from generic_items using rarity and set_type 
    rarity_index = [1 if x in rarity else 0 for x in search_array[2]]
    set_type_index = [1 if x in set_type else 0 for x in search_array[5]]
    indices_to_keep = [x|y for x,y in zip(rarity_index, set_type_index)]

    if indices_to_keep.count(1) > 0:
        #Remove the items from arr_generic_items using the indices to keep
        tmp = [x if y==1 else None for x,y in zip(arr_generic_items, indices_to_keep)]
        filtered_arr = [i for i in tmp if i]

        #Do the same for the index so we can keep track
        tmp = [x if y==1 else None for x,y in zip(search_array[0], indices_to_keep)]
        filtered_ids = [i for i in tmp if i]
    else:
        filtered_arr = arr_generic_items
        filtered_ids = search_array[0]

    # From filtered array, refine the strings for each item for better matching
    filtered_arr = [trim_strings(x, array=STOP_WORDS+SET_TYPES+RARITY+YEARS, length=2) for x in filtered_arr]

    # Refine the ebay listing item for better matching
    search_item = (' ').join(item_split)
    search_item = trim_strings(search_item, array=STOP_WORDS+SET_TYPES+RARITY+YEARS,length=2)

    score_match = [exact_word_matching(search_item, result_item) for result_item in filtered_arr]

    if score_match.count(max(score_match)) >= 2:
        #print('Found multiple score_matches')
        # Slice the filtered_arr where the score_match = max(score_match)
        max_score = max(score_match)
        tmp = [y if x >= max_score else None for x,y in zip(score_match, filtered_arr)]
        sf_array = [i for i in tmp if i] #Remove None items

        #Do the same for the filtered_ids
        tmp = [y if x >= max_score else None for x,y in zip(score_match, filtered_ids)]
        id_array = [i for i in tmp if i] #Remove None items

        result = process.extract(search_item, sf_array, limit=20)
        result_items = [x[0] for x in result]
        lev_scores = [x[1] for x in result]

        #if lev_scores.count(max(lev_scores)) > 1 and multi is not None:
        if len(lev_scores) > 1 and multi is not None:
            # KEEPING FOR NOW for evaluation
            # search_logger.info("More than one result found with the same score")
            # results_index = [i for i, x in enumerate(lev_scores) if x>=max(lev_scores)]
            # id_results = [id_array[i] for i in results_index]

            # if len(id_results) > multi:
            #     id_results = id_results[:multi]
            return id_array[:multi]
        else:
            f_result =  result_items[lev_scores.index(max(lev_scores))]
            id_result = id_array[sf_array.index(f_result)]

    
    else:
        f_result = filtered_arr[score_match.index(max(score_match))]
        id_result = filtered_ids[score_match.index(max(score_match))]
    
    return id_result


@click.command()
@click.option('--input', '-i', type = str, prompt='Please enter your search string here', default=None)
@click.option('--keep_open', is_flag = True, default=False)
@click.option('--multi', '-m', type =int, default=None)
def main(input, keep_open, multi):
    #Load the generic_items_full.csv into a numpy array. 
    # TODO # Change this to querying the DB. Has to be efficient
    file_name = 'search/datasets/generic_items_raw_1801.csv'
    arr = np.loadtxt(file_name, delimiter=',', usecols=range(0,7), unpack=True, dtype=str, skiprows=1)

    # Fuzzy matching
    # Match each item of the ebay_items to the generic items list 
    # Once a match is found, return the generic item name
    while True:
        if input is None:
            input = click.prompt('Please enter your search string here')   
        id_result = run_search(input, arr, multi=multi)

        #Put into a list so we can treat the results as the same whether multi is on or not
        if type(id_result) is not list:
            id_result = [id_result]

        #Using the id, get the index and parsing results
        id_results = list(map(int, id_result))
        id_search_array = list(map(int, arr[0]))

        #Find the index of the id_results
        match_indices = [id_search_array.index(x) for x in id_results]

        for idx, match_index in enumerate(match_indices):

            set_result = arr[5][match_index]
            card_name_result = arr[1][match_index]
            item_index_result = arr[6][match_index]

            #Print out results
            print(f'MATCHED CARD ID: {id_result[idx]}' )
            print(f'MATCHED CARD NAME: {card_name_result}' )
            print(f'MATCHED CARD SET: {set_result}')
            print(f'MATCHED ITEM INDEX: {item_index_result}')
            #print(f'With item {item} the result is: \n {f_result} ID: {id_result}')
            input=None
        if keep_open is False:
            break

if __name__ == "__main__":
    main()
