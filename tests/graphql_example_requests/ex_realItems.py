mutate_create = """mutation {
  createRealItem(itemId: 123, itemCollectionsId: 456) {
    realItem {
      databaseId
      itemCollectionsId
      condition
    }
  }
}
"""

mutate_update = """mutation updateRealItemCondition($databaseId: Int!, $condition: String!) {
  updateRealItem(databaseId:$databaseId, condition:$condition) {
    realItem {
      databaseId
      sku
      condition
      fmv
    }
    ok
    debug
  }
}
"""

mutate_delete = """mutation {
  deleteRealItem(databaseId:123) {
    ok
    debug
  }
}"""

add_real_item = """mutation addRealItem($itemId: Int!, $itemListId: Int!) {
  createRealItem(itemId: $itemId, itemListId: $itemListId) {
    realItem {
      databaseId
      itemCollectionsId
      condition
      itemListId
    }
  ok
  debug
  }
}
"""

upd_real_item = """mutation updateRealItem($databaseId: Int!, $sku: String!) {
  updateRealItem(databaseId: $databaseId, sku: $sku) {
    ok
    debug
    realItem {
      databaseId
      sku
    }
  }
}
"""

upd_real_item_userlist = """mutation updateRealItem($databaseId: Int!, $userList: String!) {
  updateRealItem(databaseId: $databaseId, userList: $userList) {
    ok
    debug
    realItem {
      databaseId
      userList
    }
  }
}
"""

upd_real_item_item_list_id = """mutation updateRealItem($databaseId: Int!, $itemListId: Int!) {
  updateRealItem(databaseId: $databaseId, itemListId: $itemListId) {
    ok
    debug
    realItem {
      databaseId
      itemListId
    }
  }
}
"""

del_real_item = """mutation delRealItem($databaseId: Int!) {
  deleteRealItem(databaseId: $databaseId) {
    ok
    debug
  }
}
"""

paged_real_items = """query getSingleRealItem($page: Int!, $perPage: Int!) {
  realItems(page: $page, perPage: $perPage) {
    databaseId
  }
}
"""

single_real_item = """query getSingleRealItem($userId: Int!) {
  realItems(page: 0, perPage: 1, userId: $userId) {
    databaseId
    owner
  }
}
"""

real_items_by_status = """query realItemsByStatus($status: String!) {
  realItems(status: $status) {
    databaseId
    status
  }
}
"""
