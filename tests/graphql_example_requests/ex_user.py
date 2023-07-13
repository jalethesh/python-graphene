# userId 1 does not exist, returns null user
query_user1 = """
{
  user(userId: 1) {
    id
    username
    itemCollections {
      edges {
        node {
          id
          userId
        }
      }
    }
  }
}
"""
# 701 is dylan's administrator account
# you can only see these user details if you are also an admin
query_user2 = """
{
  user(userId: 701) {
    id
    username
    itemCollections {
      edges {
        node {
          id
          userId
        }
      }
    }
  }
}
"""
# 714 is dylan's customer role account
# this will be the typical query from the front end
# if the front end needs to pull user information for the current user
# here we are pulling all the item collections and cards for the current user
query_user3 = """
{
  user(userId: 714) {
    id
    username
    itemCollections {
      edges {
        node {
          id
          userId
          realItems {
            edges {
              node {
                id
                itemCollectionsId
              }
            }
          }
        }
      }
    }
  }
}
"""

mutate_updateUser_1 ="""
mutation {
  updateUser(databaseId: 10, updateJson: "{'password_hash':'55'}") {
    ok
    debug
  }
}
"""