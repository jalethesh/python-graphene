query_itemLists_read = """query userItemLists {  
    itemLists {
        databaseId
        userId
        name
    }

}
"""

mutation_create_itemLists = """
mutation createItemList($name: String!) {
  createItemList(name: $name) {
    itemList {
        databaseId
    }
    ok
    debug
  }
}
"""
mutation_update_itemLists = """
mutation updateItemList($databaseId: Int!, $name: String!) {
  updateItemList(databaseId: $databaseId, name: $name) {
      ok
      debug
  }
}
"""

mutation_delete_itemLists = """
mutation deleteItemList($databaseId: Int!) {
  deleteItemList(databaseId: $databaseId) {
    ok
    debug
  }
}

"""