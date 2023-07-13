query_conditions_read = """
{
  conditions {
    id
    usCode
    type
  }
}
"""

mutate_condition_on_real_item = """mutation updateCondtionOnRealItem($condition: String!, $databaseId: Int!) {
  updateRealItem(condition: $condition, databaseId: $databaseId) {
    ok
    debug
  }
}"""