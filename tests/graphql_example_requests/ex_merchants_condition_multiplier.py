from graphql_service import queries


query_merchants_condtion_multiplier = """
{
	merchantsConditionMultiplier {
	id
    conditionId
    merchant
	}
}
"""