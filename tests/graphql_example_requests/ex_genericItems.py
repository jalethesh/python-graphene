query_genericItems_1 = """{
  genericItems(page: 4, perPage: 20) {
    id
    imageUriPng
    itemIndex
  }
}"""

query_genericItems_partialFilter = """
{
  genericItems(partialName: "Sliv") {
    id
    name
    scryfallUri
  }
}

"""

query_generic_items_with_id = """
{
  genericItems(databaseId: 1048369) {
    id
    name
    scryfallCardId
  }
}
"""

query_generic_items_with_id_list = """
{
  genericItems(databaseId: [1048369,1048361,1048319]) {
    id
    name
    scryfallCardId
    itemIndex
  }
}
"""