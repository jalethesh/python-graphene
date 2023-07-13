import pandas as pd
from models.data_models import db, SetModel
df = pd.read_csv('datasets/2021_05_28__08_43pwccmarketplace - 2021_05_28__08_43pwccmarketplace.csv').to_dict('records')


primary_words = [x['Title'].split(' ')[0] for x in df]
print(list(set(primary_words)))
def categorize_title(title):
    primary_title = title.split(' ')[0]
    starts_with_date = False
    try:
        starts_with_date = int(primary_title[:4]) in range(1990, 2030)
    except Exception as ex:
        pass

    if 'Lot' in primary_title:
        return 'lot'
    elif starts_with_date:
        return 'date'
    elif 'Hoard' in primary_title:
        return 'hoard'
    else:
        return 'special'


def extract_lot(datum):
    title = datum['working']
    first_word = title.split(' ')[0]
    if 'Lot' not in first_word and 'Hoard' not in first_word:
        return datum
    datum['lot'] = title.split(' ')[0]
    datum['working'] = ' '.join(title.split(' ')[1:])
    return datum


def extract_year(datum):

    starts_with_date = False
    try:
        starts_with_date = int(datum['working'][:4]) in range(1990, 2030)
        datum['year'] = datum['working'].split(' ')[0]
        datum['working'] = ' '.join(datum['working'].split(' ')[1:])
        return datum
    except Exception as ex:
        # print(ex)
        return datum

def extract_collectible(datum):

    collectible_string = 'Magic The Gathering '
    alt_string = 'Magic the Gathering '
    if collectible_string in datum['working']:
        datum['collectible'] = 'Magic The Gathering'
        datum['working'] = datum['working'].replace(collectible_string, '')
    elif alt_string in datum['working']:
        datum['collectible'] = 'Magic The Gathering'
        datum['working'] = datum['working'].replace(alt_string, '')
    datum['working'] = datum['working'].replace('MTG ', '') # strip this out
    return datum


def extract_set(datum):
    
    dbsets = db.session.query(SetModel).all()

    print(dbsets)

    return dbsets


def extract_suffix(datum):
    suffix_first_words = ['R', 'R1', 'R2', 'C', 'P', 'PSA', 'PSA/DNA', 'DNA', 'BGS', 'C', 'U', 'U1', 'U2', 'U3', 'V',
                          'V1', 'V2', 'V3', 'CGC', 'AUTO',
                          'C1', 'C2', 'C3', 'C4', 'C5', 'C11']

    words = datum['working'].split(' ')
    suffix_start = len(words)
    for suffix_word in suffix_first_words:
        try:
            suffix_index = words.index(suffix_word)
            if suffix_index < suffix_start:
                suffix_start = suffix_index
        except:
            pass
    datum['working'] = ' '.join(words[:suffix_start])
    datum['condition'] = ' '.join(words[suffix_start:])
    if suffix_start < len(words):
        datum['name'] = datum['working']


data = []
counters = { 'working': 0, 'lot': 0, 'year': 0, 'collectible': 0, 'edition': 0, 'name': 0, 'condition': 0, 'uncleaned': 0}
for item in df:
    title = item['Title']
    datum = {'working': title, 'lot': None, 'year': None, 'collectible': None, 'edition': None, 'name': None, 'condition': None, 'uncleaned': title}

    extract_lot(datum)
    extract_year(datum)
    extract_collectible(datum)
    extract_set(datum)
    extract_suffix(datum)
    data.append(datum)
    for key in datum:
        if datum[key]:
            counters[key] += 1
    if datum['name'] and 'C1' in datum['name']:
        print(datum)


pd.DataFrame(data).to_csv('myfile.csv', index=False)
print(counters)