## What is this project? 

Our vision is to:

1) Ingest all Magic the Gathering card information from all sources
2) Ingest all available MTG pricing information (buylists, ebay, pwcc, self created)
3) Create a pricing engine that predicts the value of every card
4) Create a collection tracking tool
5) Create a marketplace
6) Create the best tools for sellers
7) Expand to other TCGs
8) Beat TCGPlayer
9) Go Public


# Purplemana info:
Website: www.purplemana.com
Discord: https://www.purplemana.com/discord
Handle: anxman


##  Database structure:

- genericItems:  Table with all items, unique key on item_index (meaning duplicate scyfall_card_id is possible b/c foil/nonfoil variants)
- offers:  Table with all grouped offers per item_index
- offersHistory:  Table with all individual offers from merchants for each card joined, with offer
- itemCollections: a list of realItems, tied to a user
- realItems: a genericItem tied to a user and a itemCollection
- users: a local reference to the Wordpress user account, no authentication details, but contains authorization roles and serves as a reference for itemCollections


## Deployment


To ingest cards from scryfall:

1) flask scryfall download_bulk_json default_cards
2) flask scryfall convert_json_to_csv default_cards.json default_cards.csv
3) flask scryfall divide_csv default_cards.csv to_process.csv 10000
4) flask scryfall csv_to_db to_process.csv processed.csv

Repeat steps 3 and 4 until complete

Note that there is an error with cards that have "///" in the title b/c Python is not escaping them correctly.


To ingest data from mtgban:

flask buylist download_mtgban_offers

Note: This seems to be working correctly now!

## AWS celery-redis notes and setup 
See aws-celery-redis-notes.txt
 
 
## Graphql schema
see schema.json

   
  
