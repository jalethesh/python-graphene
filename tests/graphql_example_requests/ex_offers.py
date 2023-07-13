# latest offer set for a given card

# get a list of offers and their corresponding OffersHistory entries (offer by merchant) and card info
# offers returns a single offer always
query_offers_by_generic_item = """query OffersByGenericItemId($genericItemId: Int!){
  offers(genericItemId: $genericItemId) {
    id
    scryfallCardId
    itemId
    genericItems {
      edges {
        node {
          scryfallCardId
        }
      }
    }
    offersHistory {
      edges {
        node {
          id
          offersId
          scryfallCardId
          amount
        }
      }
    }
  }
}
"""
