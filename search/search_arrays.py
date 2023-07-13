import numpy as np

STOP_WORDS = ['psa','mtg', 'magic the gathering', 'the gathering', 'the' ,'to', 'card', 'magic']

SET_TYPES = ['token', 
'set',
'core',
'promo',
'draft_innovation',
'draft innovation'
'box',
'commander',
'masters',
'starter',
'duel_deck',
'duel'
'duel deck'
'funny',
'planechase',
'masterpiece',
'premium_deck',
'premium',
'premium deck'
'memorabilia',
'spellbook',
'vanguard',
'vault',
'from the vault',
'from_the_vault',
'archenemy',
'NULL',
'treasure_chest',
'treasure'
'treasure chest'
]

RARITY = ['uncommon',
'common',
'rare',
'mythic',
'special',
'NULL',
'bonus',
'regular',
]


file_name = 'search/datasets/generic_items_full.csv'

def get_set_names():
    arr = np.loadtxt(file_name, delimiter=',', usecols=range(0,6), unpack=True, dtype=str, skiprows=1)
    sn = arr[1]
    b =   [x.replace('"', "") for x in sn]
    return b

def get_years():
    a = list(range(1990,2025,1))
    return [str(x) for x in a]

SET_NAMES = get_set_names()
YEARS = get_years()