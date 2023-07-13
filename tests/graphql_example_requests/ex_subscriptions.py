create_sub = """mutation createSub($subscriberId: Int!, $userId: Int!) {
  createSubscription(subscriberId: $subscriberId, userId: $userId) {
    subscription {
      id
      subscriberId
      userId
      genericItemId
    }
    debug
    ok
  }
}"""

delete_sub = """mutation delSub($id: Int!){
  deleteSubscription(id: $id) {
    ok
    debug
  }
}"""