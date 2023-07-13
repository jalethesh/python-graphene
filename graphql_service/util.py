# queries will not return more than 1000 results at a time
from sqlalchemy import desc


def paginate(query, table_object_primary_key, page, per_page, sort_reverse=False):
    if not sort_reverse:
        query = query.order_by(table_object_primary_key)
    else:
        query = query.order_by(desc(table_object_primary_key))

    query = query.offset(page * per_page)
    if per_page > 1000:
        per_page = 1000
    return query.limit(per_page)

class ShippoQuote:
    def __init__(self):
        self.amount = False
        self.estimated_days = False
        self.provider = False
        self.name = False
        self.token = False