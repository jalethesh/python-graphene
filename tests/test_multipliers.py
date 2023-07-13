from tests.graphql_example_requests.ex_merchants_condition_multiplier import query_merchants_condtion_multiplier
import json


def show_multipliers(client):
    query = query_merchants_condtion_multiplier
    url = f'http://localhost:5000/graphql-api?query={query}'
    res = client.post(url)
    data = json.loads(res.data.decode('utf-8'))
    print('response:', data['data']['merchantsConditionMultiplier'][0])
    result_ok = data['data']['merchantsConditionMultiplier'][0]
    assert result_ok
    return result_ok
