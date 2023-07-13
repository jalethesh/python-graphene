
query_itemCollections_1 = """{
  itemCollections
  {
    databaseId
    id
    name
  }
}
"""


mutation_itemCollections_create = """
mutation TestMutation {
  createCollection(name: "Another Testing Collection") {
    ok
    debug
    collection {
      id
      databaseId
      trashed
    }
  }
}
"""

mutation_itemCollections_name_update = """
mutation AnotherTestMutation{
  updateCollection(databaseId:33, name:"bigger") {
    ok
    debug
    collection {
      id
      name
    }
  }
}
"""

# this mutation just sets the "trashed" field on the collection to True
mutation_itemCollections_delete = """
mutation deleteCollection {
  deleteCollection(databaseId: 29) {
    ok
    debug
  }
}
"""

query_itemCollections_read = """
query readUserCollection($collectionId: Int!) {
  itemCollections(collectionId: $collectionId) {
    databaseId
    userId
  }
}
"""

query_itemCollection_realItems_number_read = """
query itemCollection($id: Int!, $collectionId: Int! ) {
  itemCollections(userId: $id, collectionId: $collectionId) {
    name
    count
  }
}
"""
