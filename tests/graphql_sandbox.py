from graphene import ObjectType, String, Schema, Field, Mutation, Boolean


class Person(ObjectType):
    class Meta:
        description = 'A human'

    # implicitly mounted as Field
    first_name = String(default_value="<firstname>")
    # explicitly mounted as Field
    last_name = Field(String, default_value="<lastname>")

    # overwriting the default resolver
    def resolve_last_name(self, info):
        return self.last_name[::-1]


class CreatePerson(Mutation):
    class Arguments:
        first_name = String()
        last_name = String()

    ok = Boolean()
    person = Field(lambda: Person)

    def mutate(root, info, first_name, last_name):
        person = Person(first_name=first_name, last_name=last_name)
        ok = True
        return CreatePerson(person=person, ok=ok)


people = [Person(first_name="Mark", last_name="Aychdfdfdfd"), Person(first_name="Jake", last_name="Allll")]
class UpdatePerson(Mutation):
    class Arguments:
        first_name = String()
        last_name = String()

    ok = Boolean()
    person = Field(lambda: Person)

    def mutate(root, info, first_name, last_name):
        person = [x for x in people if x.first_name=="Mark"][0]
        person.first_name = first_name
        ok = True
        return UpdatePerson(person=person, ok=ok)


class Query(ObjectType):
    # this defines a Field `hello` in our Schema with a single Argument `name`
    hello = String(name=String(default_value="stranger"))
    goodbye = String()
    my_best_friend = Field(Person)
    who_isnt_my_best_friend = Field(Person)
    person = Field(Person)

    # our Resolver method takes the GraphQL context (root, info) as well as
    # Argument (name) for the Field and returns data for the query Response
    def resolve_hello(self, info, name):
        print("in hello resolver")
        return f'Hello {name}!'

    def resolve_goodbye(self, info):
        print("in goodbye resolver")
        return 'See ya!'

    def resolve_person(self, info):
        myPerson = Person()
        return myPerson

    def resolve_who_isnt_my_best_friend(self, info):
        print("in enemy resolver")
        enemy = Person(first_name="Mark", last_name="Aych")
        return enemy

    def resolve_my_best_friend(self, info):
        print("in bf resolver")
        myPerson = Person(first_name="Jake", last_name="Alongi")
        return myPerson


class Mutation(ObjectType):
    create_person = CreatePerson.Field()
    update_person = UpdatePerson.Field()


schema = Schema(query=Query, mutation=Mutation)

# we can query for our field (with the default argument)
query_string = '{ hello }'
result = schema.execute(query_string)
print(result.data['hello'])
# "Hello stranger!"

# or passing the argument in the query
query_with_argument = '{ hello(name: "GraphQL") }'
result = schema.execute(query_with_argument)
print(result.data['hello'])
# "Hello GraphQL!"

query_string = '{ person {firstName} }'
result = schema.execute(query_string)
print(result)

query_string = '{ myBestFriend { firstName, lastName } }'
result = schema.execute(query_string)
print(result)

query_string = '{ whoIsntMyBestFriend { firstName, lastName } }'
result = schema.execute(query_string)
print(result)

query_string = """  mutation myFirstMutation {
                        createPerson(firstName:"John", lastName:"Adams") {
                            person {
                                firstName,
                                lastName
                            }
                            ok
                        }
                    }"""
result = schema.execute(query_string)
print(result)

query_string = """  mutation ASecondMutation {
                        updatePerson(firstName:"John", lastName:"Adams") {
                            person {
                                firstName,
                                lastName
                            }
                            ok
                        }
                    }"""
result = schema.execute(query_string)
print(result)



import json
introspection_dict = schema.introspect()

# Print the schema in the console
# intro_json = json.loads(introspection_dict)
# formatted_json = json.dumps(intro_json)
# print(formatted_json)

# Or save the schema into some file
with open('schema.json', 'w') as fp:
    # pretty_schema = json.dumps(introspection_dict)
    json.dump(introspection_dict, fp, indent=2, separators=(',', ':'))
    print("finished writing file")

# cleaned_schem = {}
# queries = {}
# mutations = {}
# for type in introspection_dict['__schema']['types']:
#     if '__' in type['name'] or type['kind'] == 'SCALAR':
#         continue
#
#     if type['name'] != 'Mutation' and type['name'] != 'Query':
#         continue
#
#     # print(type)
#     # args = type['fields']['args']
#     # print(args)
#     for field in type['fields']:
#         # arg_names = [x['name'] for x in field['args']]
#         # arg_types = [x['type']['name'] for x in field['args']]
#         for arg in field['args']:
#             arg['type'] = arg['type']['name']
#         del field['type']
#         del field
#         print(field)

# for field in mutations['fields']:
#     print(field)
# for field in queries['fields']:
#     print(field)


# subscriptions not available until graphene 3
# print(f"async subscription tests")
#
# import asyncio
# from datetime import datetime
# from graphene import ObjectType, String, Schema, Field
#
# # Every schema requires a query.
# class Query(ObjectType):
#     hello = String()
#
#     def resolve_hello(root, info):
#         return "Hello, world!"
#
# class Subscription(ObjectType):
#     time_of_day = String()
#
#     async def subscribe_time_of_day(root, info):
#         while True:
#             yield datetime.now().isoformat()
#             await asyncio.sleep(1)
#
# schema = Schema(query=Query, subscription=Subscription)
#
# async def main(schema):
#     subscription = 'subscription { timeOfDay }'
#     result = await schema.subscribe(subscription)
#     async for item in result:
#         print(item.data['timeOfDay'])
#
# asyncio.run(main(schema))