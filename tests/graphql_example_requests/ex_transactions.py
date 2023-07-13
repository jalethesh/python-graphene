get_transactions = """query allTransactions {
  transactions {
    databaseId
  }
}
"""

make_transaction = """mutation createNewTransaction($itemListId: Int!) {
    createTransaction(itemListId: $itemListId) {
      ok
      debug
      transaction {
        databaseId
        leftOwner
        rightCredit
        transactionItems { 
          edges { 
            node { 
              databaseId
            }
          }
        }
      }
    }
}
"""

del_transaction = """mutation deleteTransaction($transactionId: Int!) {
  deleteTransaction(transactionId: $transactionId) {
    ok
    debug
  }
}
"""

upd_transaction = """mutation updateATransaction($transactionId: Int!, $leftConfirm: Boolean) {
  updateTransaction(transactionId: $transactionId, leftConfirm: $leftConfirm) {
    transaction {
      status
    }
    ok
    debug
  }
}
"""

upd_transaction_admin_comment = """mutation updateATransaction($transactionId: Int!, $adminComment: String!) {
  updateTransaction(transactionId: $transactionId, adminComment: $adminComment) {
    transaction {
      adminComment
    }
    ok
    debug
  }
}
"""

upd_transaction_right = """mutation updateATransaction($transactionId: Int!, $rightConfirm: Boolean) {
  updateTransaction(transactionId: $transactionId, rightConfirm: $rightConfirm) {
    transaction {
      status
    }
    ok
    debug
  }
}
"""

upd_transaction_status = """mutation updateATransactionStatus($transactionId: Int!, $status: String!, $testing: Boolean) {
  updateTransactionStatus(transactionId: $transactionId, status: $status, testing: $testing) {
    transaction {
      status
    }
    ok
    debug
  }
}
"""

get_transaction_items = """query transactionItemsByTransactionID($transactionId: Int!) {
  transactionItems(transactionId: $transactionId) {
    databaseId
  }
}
"""

make_transaction_item = """mutation addItemToTransaction($transactionId: Int!, $realItemId: Int!, $side: String!) {
  createTransactionItem(transactionId: $transactionId, realItemId: $realItemId, side: $side) {
    ok
    debug
    transactionItem {
      databaseId
    }
  }
}
"""

del_transaction_item = """mutation delItemFromTransaction($transactionItemId: Int!) {
  DeleteTransactionItem(transactionItemId: $transactionItemId) {
    ok
    transactionItem {
      databaseId
    }
  }
}
"""