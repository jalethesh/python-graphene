
# getting cards within a set
query_sets_1 = """{
  sets(setCode:"lea") {
    code
    genericItems {
      edges {
        node {
          id
          setName
          itemIndex
        }
      }
    }
  }
}
"""

# getting a list of sets
query_sets_2 = """
{
  sets( page:0, perPage:5) {
    code
    id
  }
}
"""