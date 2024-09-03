"""
DbAbstractor: Database abstraction layer for MongoDb and DynamoDb
"""
from __future__ import annotations
from decimal import Decimal
import json

# from flask import current_app
# from Chalice import current_app

from bson.json_util import dumps, ObjectId
from werkzeug.local import LocalProxy

import pymongo
import boto3
import botocore

from genericsuite.util.app_logger import (
    log_debug,
    log_error,
    log_warning,
)
# from lib.models.dynamodb_table_structures \
#     import dynamodb_table_structures, \
#     DEFAULT_WRITE_CAPACITY_UNITS, DEFAULT_READ_CAPACITY_UNITS

from genericsuite.config.config import Config, is_local_service
from genericsuite.util.request_handler import RequestHandler

# ----------------------- Factory Methods -----------------------


DEBUG = False

DEFAULT_WRITE_CAPACITY_UNITS = 1
DEFAULT_READ_CAPACITY_UNITS = 1


class ObjectFactory:
    """
    Factory class for creating the different database objects.
    """
    def __init__(self):
        self._builders = {}

    def register_builder(self, key, builder):
        """
        Register the object (builder) for the given key (database).

        Args:
            key (str): The key for the database object.
            builder (DbAbstract): The database object (builder).

        Returns:
            None
        """
        self._builders[key] = builder

    def create(self, key, **kwargs):
        """
        Returns the given builder (database object) for the given key.

        Args:
            key (str): The key for the database object.
            **kwargs (dict): The keyword arguments for the database object.

        Returns:
            DbAbstract: The database object (builder).
        """
        builder = self._builders.get(key)
        if not builder:
            raise ValueError(key)
        return builder(**kwargs)


# ----------------------- Db Abstract -----------------------


class DbAbstract:
    """
    Database abstract super class
    """
    def __init__(self, app_config, **_ignored):
        self._app_config = app_config
        self._db = self.get_db_connection()
        # self.create_tables()

    def get_db(self):
        """
        Returns the database object.

        Returns:
            Object: The database object.
        """
        return self._db

    def get_db_connection(self):
        """
        Returns the database connection object.

        Returns:
            Object: The database connection object.
        """
        return {}

    def test_connection(self) -> str:
        """
        Test the database connection.

        Returns:
            str: The test result.
        """
        return dumps({})

    def list_collections(self, collection_name: str = None) -> list:
        """
        List the collections in the database.

        Returns:
            list: The list of collections.
        """
        return []

    def collection_stats(self, collection_name: str = None):
        """
        Get the collection statistics.

        Args:
            collection_name (str): the collection name. None means
            get all collections stats. Defaults to None.

        Returns:
            str: The collection(s) statistics.
        """
        return dumps(self.list_collections(collection_name))

    def create_tables(self) -> bool:
        """
        Create the tables in the database.
        """
        return True

    def table_exists(self, table_name: str) -> bool:
        """
        Check if the table exists in the database.

        Args:
            table_name (str): The name of the table.

        Returns:
            bool: True if the table exists, False otherwise.
        """
        return True


# ----------------------- MongoDb  -----------------------


class MongodbService(DbAbstract):
    """
    MongoDb service class
    """

    def get_db_connection(self):
        """
        Returns the database connection object.

        Returns:
            Object: The database connection object.
        """
        _ = DEBUG and \
            log_debug(
                "DB_ABSTRACTOR | MongodbService | get_db_connection" +
                # f"\n | DB_CONFIG: {self._app_config.DB_CONFIG}" +
                " | Starting...")
        client = pymongo.MongoClient(self._app_config.DB_CONFIG['mongodb_uri'])
        _ = DEBUG and \
            log_debug(
                "DB_ABSTRACTOR | MongodbService | get_db_connection" +
                f"\n | client: {client}" +
                "\n | DB Client OK...")
        db_connector = client.get_database(
            self._app_config.DB_CONFIG['mongodb_db_name'])
        _ = DEBUG and \
            log_debug(
                "DB_ABSTRACTOR | MongodbService | get_db_connection" +
                f"\n | db_connector: {db_connector}" +
                "\n | DB Connector OK...")
        return db_connector

    def test_connection(self) -> str:
        """
        Test the database connection.

        Returns:
            str: The test result.
        """
        return dumps(self._db.list_collection_names())

    def collection_stats(self, collection_name: str = None) -> str:
        """
        Get the collection statistics.

        Args:
            collection_name (str): the collection name. None means
            get all collections stats. Defaults to None.

        Returns:
            str: the MongoDb 'collstats' for all or the given collection
        """
        return dumps(self._db.command('collstats', collection_name))


class MongodbServiceBuilder(DbAbstract):
    """
    Builder class for MongoDb.
    """
    def __init__(self):
        self._instance = None

    def __call__(self, app_config, **_ignored):
        if not self._instance:
            self._instance = MongodbService(app_config)
        return self._instance


# ----------------------- DynamoDb  -----------------------


class DynamoDbUtilities:
    """
    DynamoDb Utilities class
    """
    def new_id(self):
        """
        Generate mongodb styled "_id"
        """
        # google: python generate unique _id like mongodb
        # https://www.geeksforgeeks.org/generating-random-ids-using-uuid-python/
        # id = uuid.uuid1()
        # uuid1() includes the used of MAC address of computer,
        # and hence can compromise the privacy,
        # even though it provides UNIQUENES.
        # return id.hex
        # RESULT: bson.errors.InvalidId: '48a8b1a021b611edbf5a0e4c731ac1c1'
        # is not a valid ObjectId, it must be a 12-byte input or a
        # 24-character hex string | vs 6302ded424b11a2032d7c562
        # SOLUTION: https://api.mongodb.com/python/1.11/api/bson/objectid.html
        return str(ObjectId())

    def id_addition(self, row):
        """
        Convert _id to be mongodb styled,
        for example to send it to the react frontend
        expecting it as a $oid
        """
        if 'id' in row:
            row['_id'] = ObjectId(row['id'])
        elif '_id' in row and isinstance(row['_id'], str):
            # row['id'] = row['_id']
            row['_id'] = ObjectId(row['_id'])
        return row

    def id_conversion(self, key_set):
        """
        To avoid error working internally with mongodb styled "_id"
        """
        if DEBUG:
            log_debug('**** id_conversion | key_set BEFORE: ' + str(key_set))
        if '_id' in key_set and not isinstance(key_set['_id'], str):
            key_set['_id'] = str(key_set['_id'])
        if DEBUG:
            log_debug('**** id_conversion | key_set AFTER: ' + str(key_set))
        return key_set

    def convert_floats_to_decimal(self, data):
        """
        To be used before sending dict to DynamoDb for inserts/updates
        """
        # return json.loads(json.dumps(item), parse_float=Decimal)
        #   --> TypeError: Object of type Decimal is not JSON serializable
        # return json.loads(json.dumps(item, default=float))
        #   --> Error updating Item [UO_ERR_020]: Float types are not
        #       supported. Use Decimal types instead.
        if isinstance(data, dict):
            return {k: self.convert_floats_to_decimal(v)
                    for k, v in data.items()}
        elif isinstance(data, list):
            return [self.convert_floats_to_decimal(item) for item in data]
        elif isinstance(data, float):
            return Decimal(str(data))
        else:
            return data

    def remove_decimal_types(self, item: dict, projection: dict = None):
        """
        To be used before sending responses to entity
        """
        if not projection:
            projection = {}
        if DEBUG:
            log_debug('====> REMOVE_DECIMAL_TYPES' +
                      f' | projection: {projection}' +
                      f' | item BEFORE: {item}')
        # Convert MongoDB _id Object to str
        item = self.id_conversion(item)
        # Convert Decimal to floats
        item = json.loads(json.dumps(item, default=float))
        # Convert _id to be mongodb styled
        item = self.id_addition(item)
        # Applying MongoDB like projection (replacing the use of DymanoDb's
        # ProjectionExpression)
        item = {k: v for k, v in item.items() if projection.get(k, 1) == 1}
        if DEBUG:
            log_debug('====> REMOVE_DECIMAL_TYPES | item AFTER: ' + str(item))
        return item

    def remove_decimal_types_list(self, items: list, projection: dict = None):
        """
        To be used before sending responses to entity as a list
        """
        if items is None:
            _ = DEBUG and \
                log_debug('remove_decimal_types_list | None result: []')
            return []
        return [self.remove_decimal_types(item, projection) for item in items]


class DynamoDbFindIterator(DynamoDbUtilities):
    """
    Dynamodb find iterator
    """
    def __init__(self, data_set):
        if DEBUG:
            log_debug(
                '>>--> DynamoDbFindIterator | __init__() | data_set: ' +
                str(data_set)
            )
        self._data_set = data_set
        self._skip = 0
        self._limit = None
        self._num = None

    def skip(self, skip):
        """
        Set the skip value
        """
        if DEBUG:
            log_debug('>>--> DynamoDbFindIterator | skip() | skip: ' +
                      str(skip))
        self._skip = skip
        return self

    def limit(self, limit):
        """
        Set the limit value
        """
        if DEBUG:
            log_debug(
                '>>--> DynamoDbFindIterator | limit() | limit: ' + str(limit)
            )
        self._limit = limit
        return self

    def __iter__(self):
        self._num = self._skip
        if DEBUG:
            log_debug(
                '>>--> DynamoDbFindIterator | __iter__() | self.num: ' +
                str(self._num)
            )
        return self

    def __next__(self):
        if DEBUG:
            log_debug(
                '>>--> DynamoDbFindIterator | __next__() | self.num: ' +
                str(self._num) + ' | len(self._data_set): ' +
                str(len(self._data_set))
            )
        if isinstance(self._data_set, dict):
            if self._num > 0:
                raise StopIteration
            self._num += 1
            return self.remove_decimal_types(
                self.id_addition(self._data_set)
            )
        if (not self._limit or self._num <= self._limit) and \
           self._data_set and self._num < len(self._data_set):
            # _result = self.convert_floats_to_decimal(
            #   self.id_addition(self._data_set[self._num])
            # )
            _result = self.remove_decimal_types(
                self.id_addition(self._data_set[self._num])
            )
            if DEBUG:
                log_debug(
                    '>>--> DynamoDbFindIterator | __next__() | _result: ' +
                    str(_result)
                )
            # _result = self.id_addition(self._data_set[self._num])
            self._num += 1
            return _result
        raise StopIteration

    def sort(self, column: str, direction: str):
        """
        Sort the data set
        """
        if isinstance(self._data_set, dict):
            return self
        if self._data_set is None:
            self._data_set = []
        else:
            self._data_set.sort(
                key=lambda data_set: data_set.get(column),
                reverse=(direction != 'asc'))
        return self


class DynamoDbTableAbstract(DynamoDbUtilities):
    """
    DynamoDb Table Abstract class
    """
    def __init__(self, item_structure, db_conection):
        if DEBUG:
            log_debug(
                '>>--> DynamoDbTableAbstract | __init__ | item_structure: ' +
                str(item_structure)
            )
        self._prefix = item_structure['prefix']
        self._table_name = item_structure['TableName']
        self._key_schema = None
        self._attribute_definitions = None
        self._global_secondary_indexes = None
        self._db_conection = db_conection
        self.inserted_id = None
        self.modified_count = None
        self.deleted_count = None

    def get_table_definitions(self):
        """
        The first time the table is used, get the table definitions
        """
        # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/dynamodb/client/describe_table.html
        response = self._db_conection.meta.client.describe_table(
            TableName=self.get_table_name()
        )
        _ = DEBUG and log_debug(f'|||---> get_table_definitions: {response}')
        item_structure = response['Table']
        self._key_schema = item_structure['KeySchema']
        self._attribute_definitions = item_structure['AttributeDefinitions']
        self._global_secondary_indexes = \
            item_structure.get('GlobalSecondaryIndexes', [])

    def get_table_name(self):
        """
        Get the table name, adding the prefix
        """
        table_name = f'{self._prefix}{self._table_name}'
        _ = DEBUG and log_debug(f'|||---> get_table_name: {table_name}')
        return table_name

    def get_key_schema(self):
        """
        Get the table key schema
        """
        if self._key_schema is None:
            self.get_table_definitions()
        return self._key_schema

    def get_attribute_definitions(self):
        """
        Get the table attribute definitions
        """
        if self._attribute_definitions is None:
            self.get_table_definitions()
        return self._attribute_definitions

    def get_global_secondary_indexes(self):
        """
        Get the table global secondary indexes
        """
        if self._global_secondary_indexes is None:
            self.get_table_definitions()
        return self._global_secondary_indexes

    def element_name(self, element_name):
        """
        Get the element's attribute name 'AttributeName'
        """
        if DEBUG:
            log_debug('|||---> element_name: ' + str(element_name))
        # return element_name['AttributeName'] \
        #   if element_name['AttributeName'] != '_id' else 'id'
        return element_name['AttributeName']

    def get_conditions(self, key, value):
        """
        Get the conditions for the DynamoDB query.
        Handles the mongoDB conditions:
            key=value, $regex, $eq, $ne, $gt, $gte, $lt, $lte, $in, $nin

        Args:
            key (str): the key to search for
            value (any): the value to search for. If value is a dict,
                it contains the conditions to apply. E.g.
                {'$regex': '.*any_value.*', '$options': 'si'}
                {'$eq': 'any_value'}
                {'$ne': 'any_value'}
                {'$gt': 'any_value', '$lt': 'any_value'}
                {'$gte': 'any_value', '$lte': 'any_value'}
                {'$in': ['any_value', 'any_value']}
                {'$nin': ['any_value', 'any_value']}

        Returns:
            list: a list of conditions to apply to the query, each one is a
                dict with the following keys:
                    'attr': the attribute name
                    'key': the key name for the condition
                    'comp_oper': the comparison operator
                    'value': the value to compare against
                    'function': the function to apply (if any)
        """
        conditions = []
        if not isinstance(value, dict):
            conditions.append({
                'attr': key,
                'key': key,
                'comp_oper': '=',
                'value': value,
            })
        else:
            # https://www.mongodb.com/docs/manual/reference/operator/query-comparison/
            # https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Query.FilterExpression.html
            # https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Query.KeyConditionExpressions.html
            # https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Expressions.OperatorsAndFunctions.html#Expressions.OperatorsAndFunctions.Syntax
            if '$regex' in value:
                # It's a regex. E.g. 'attribute_name':
                #     {'$regex': '.*any_value.*', '$options': 'si'}
                conditions.append({
                    'attr': key,
                    'key': f'{key}Rg',
                    'value': value['$regex'].replace('.*', ''),
                    'function': f'contains ({key}, :{key}Rg)',
                })
            if '$eq' in value:
                conditions.append({
                    'attr': key,
                    'key': f'{key}Eq',
                    'comp_oper': '=',
                    'value': value['$eq'],
                })
            if '$ne' in value:
                conditions.append({
                    'attr': key,
                    'key': f'{key}Ne',
                    'comp_oper': '<>',
                    'value': value['$ne'],
                })
            if '$gt' in value:
                conditions.append({
                    'attr': key,
                    'key': f'{key}Gt',
                    'comp_oper': '>',
                    'value': value['$gt'],
                })
            if '$gte' in value:
                conditions.append({
                    'attr': key,
                    'key': f'{key}Gte',
                    'comp_oper': '>=',
                    'value': value['$gt'],
                })
            if '$lt' in value:
                conditions.append({
                    'attr': key,
                    'key': f'{key}Lt',
                    'comp_oper': '<',
                    'value': value['$lt'],
                })
            if '$lte' in value:
                conditions.append({
                    'attr': key,
                    'key': f'{key}Lte',
                    'comp_oper': '<=',
                    'value': value['$lte'],
                })
            if '$in' in value or '$nin' in value:
                # https://stackoverflow.com/questions/40283653/how-to-use-in-statement-in-filterexpression-using-array-dynamodb
                cond_key = '$in' if '$in' in value else '$nin'
                i = 0
                values = {}
                key_list = []
                for v in value[cond_key]:
                    i += 1
                    key = f'{key}In{i}'
                    key_list.append(f':{key}')
                    values[key] = v
                    # values[key] = f'"{v}"' if isinstance(v, str) else v
                conditions.append({
                    'value': values,
                    'function':
                        ('NOT ' if '$nin' in value else '') +
                        f"{key} IN ({','.join(key_list)})",
                })
        return conditions

    def get_cond_exp_val(self, item):
        """
        Get the condition expression values for a DynamoDB operation.

        Args:
            item (dict): A dictionary representing the item to search for.

        Returns:
            tuple: A tuple containing the condition values dictionary, the
                   condition expression string and the attribute names.
        """
        condition_values = {}
        expresion_parts = []
        attr_names = {}
        for key in item.keys():
            conditions = self.get_conditions(key, item[key])
            group_char = ''
            inner_separator = ''
            for condition in conditions:
                attr = condition.get('attr')
                key = condition.get('key')
                comp_oper = condition.get('comp_oper')
                value = condition.get('value')
                multiple = condition.get('multiple')
                function = condition.get('function')
                if multiple is None:
                    group_char = ''
                    open_group = ''
                    close_group = ''
                elif multiple:
                    group_char = '(' if group_char == '' else ')'
                    open_group = '(' if group_char == '(' else ''
                    close_group = ')' if group_char == ')' else ''
            # Populates the condition values (to be used as the
            # ExpressionAttributeValues parameter)
            if value:
                if not isinstance(value, dict):
                    value = {key: value}
                for key_name, key_value in value.items():
                    condition_values = condition_values | \
                        {':' + key_name: key_value}
            # Populates the condition expressions (to be used as the
            # KeyConditionExpression or FilterExpression parameter)
            if function is None:
                # It's a condition
                expresion_parts.append(
                    f'{inner_separator}' +
                    f'{open_group}#{attr}_ {comp_oper} :{key}{close_group}')
                # Set an attribute name to be passed in the
                # ExpressionAttributeNames parameter calling the scan, query
                # or updat_item DynamoDB operations, to avoid errors like:
                # "Invalid UpdateExpression: Attribute name is a reserved
                # keyword; reserved keyword: language"
                attr_names[f'#{attr}_'] = attr
            else:
                # It's a function call
                expresion_parts.append(
                    f'{inner_separator}' +
                    f'{open_group}{function}{close_group}')
            # It has more than one condition
            if multiple is not None:
                inner_separator = condition.get('separator', 'AND') + ' '
        return condition_values, expresion_parts, attr_names

    def get_condition_expresion_values(self, data_list, separator=' AND '):
        """
        Generate the condition expression values for a DynamoDB operation.

        Args:
            data_list (list): A list of dictionaries, where each dictionary
                              represents one item's attributes for the
                              condition.
            separator (str): The separator to use between conditions.
            Defaults to ' AND '.

        Returns:
            tuple: A tuple containing the condition values dictionary, the
                   condition expression string and the attribute names.
        """
        condition_values = {}
        expresion_parts = []
        attr_names = {}
        _ = DEBUG and log_debug(
            '|||---> get_condition_expresion_values | ' +
            f'data_list: {data_list} | separator: {separator}')
        for item in data_list:
            _ = DEBUG and log_debug('|||---> get_condition_expresion_values' +
                                    f' | item: {item}')
            if '$and' in item or '$or' in item:
                separator = '$or' if '$or' in item else '$and'
                for subitem in item[separator]:
                    _ = DEBUG and log_debug(
                        '|||---> get_condition_expresion_values' +
                        f' | subitem: {subitem}')
                    condition_values, expresion_parts, attr_names = \
                        self.get_cond_exp_val(subitem)
            else:
                condition_values, expresion_parts, attr_names = \
                    self.get_cond_exp_val(item)
        separator = ' OR ' if '$or' in separator else ' AND ' \
            if '$and' in separator else separator
        condition_expresion = separator.join(expresion_parts)
        return condition_values, condition_expresion, attr_names

    def get_primary_keys(self, query_params):
        """
        Look for keys in partition/sort key
        """
        keys = list(filter(lambda key:
                    query_params.get(self.element_name(key)) is not None,
                    self.get_key_schema()))
        keys = list(map(lambda key: {self.element_name(key):
                    query_params.get(self.element_name(key))}, keys))
        return keys[0] if len(keys) > 0 else None

    def get_global_secondary_indexes_keys(self, query_params):
        """
        Look for keys in global secondary indexes
        """
        reduced_indexes = [
            {
                'name': global_index["IndexName"],
                'keys':
                    list(
                        map(
                            lambda key: self.element_name(key),
                            global_index["KeySchema"]
                        )
                    )
            } for global_index in self.get_global_secondary_indexes()
        ]

        query_keys = list(query_params.keys())

        index_item = list(
            filter(
                lambda index: set(query_keys).issubset(index['keys']),
                reduced_indexes
            )
        )

        keys = None
        index_name = None
        if index_item:
            index_name = index_item[0]['name']
            keys = list(
                map(
                    lambda key: {key: query_params[key]}, index_item[0]['keys']
                )
            )

        if DEBUG:
            log_debug(
                '|-|--> get_global_secondary_indexes_keys | keys: ' +
                str(keys) +
                ' | reduced_indexes: ' + str(reduced_indexes) +
                ' | index_name: ' +
                str(index_name) + ' | query_keys: ' + str(query_keys))
        return keys, index_name

    def generic_query(self, query_params: dict, projection: dict = None,
                      query_type: str = 'find', select: str = None) -> list:
        """
        Perform a query on the DynamoDB table from MongoDb style query params.

        Args:
            query_params (dict): The filter for the MongoDb query.
            projection (dict): The projection for the query.
                Uses the ProjectionExpression attribute.
                Defaults to an empty dictionary.
            query_type (str): query type: 'find' get one or more items,
                'find_one': get one item.
            select (str): The select for the query.
                Possible values: 'ALL_ATTRIBUTES' | 'ALL_PROJECTED_ATTRIBUTES'
                | 'SPECIFIC_ATTRIBUTES' | 'COUNT'.
                Defaults to None, meaning ALL_ATTRIBUTES.

        Returns:
            list: The result of the query.
        """
        if not projection:
            projection = {}
        select = select or 'ALL_ATTRIBUTES'
        projection_expression = None
        if select == 'SPECIFIC_ATTRIBUTES':
            # Assumes the specific attributes to retrieve are in the
            # projection parameter with a value of 1
            projection_expression = (",".join([k for k, v
                                     in projection.items() if v == 1]))
        select = select.upper()
        if DEBUG:
            log_debug(
                f'>>--> generic_query() | table: {self.get_table_name()}' +
                f' | query_params: {query_params}' +
                f' | projection: {projection}' +
                f' | query_type: {query_type}' +
                f' | select: {select}')

        table = self._db_conection.Table(self.get_table_name())

        if not query_params or len(query_params) == 0:
            response = table.scan()
            if select == "COUNT":
                count = len(response.get('Items', []))
                _ = DEBUG and \
                    log_debug(f'generic_query | COUNT 4: {count}')
                return count
            _ = DEBUG and \
                log_debug('generic_query | response.get(Items):' +
                          f' {response.get("Items")}')
            return self.remove_decimal_types_list(
                response.get('Items', []), projection)

        top_and_or = '$and' in query_params or '$or' in query_params
        keys = None

        if not top_and_or:
            query_params = self.id_conversion(query_params)
            keys = self.get_primary_keys(query_params)
            if keys:
                # Get only one item
                _ = DEBUG and log_debug('generic_query | ===> Keys found: ' +
                                        str(keys))
                # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/dynamodb/table/get_item.html
                params = {
                    'Key': keys,
                }
                if projection_expression:
                    params['ProjectionExpression'] = projection_expression
                response = table.get_item(**params)
                _ = DEBUG and log_debug(response)
                if select == "COUNT":
                    count = 1 if response and response.get('Item') else 0
                    _ = DEBUG and \
                        log_debug(f'generic_query | COUNT 1: {count}')
                    return count
                return self.remove_decimal_types(response.get('Item', {}),
                                                 projection)
            keys, index_name = \
                self.get_global_secondary_indexes_keys(query_params)

        if not keys:
            condition_values, condition_expresion, attr_names = \
                self.get_condition_expresion_values([query_params])
            if DEBUG:
                log_debug(
                    'generic_query | ' +
                    'No keys found... perform fullscan | condition_values: ' +
                    str(condition_values) + ' | condition_expresion: ' +
                    str(condition_expresion)
                )
            # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/dynamodb/table/scan.html
            params = {
                'ExpressionAttributeValues': condition_values,
                'Select': select,
            }
            if condition_expresion:
                params['FilterExpression'] = condition_expresion
            if projection_expression:
                params['ProjectionExpression'] = projection_expression
            if attr_names:
                params['ExpressionAttributeNames'] = attr_names
            response = table.scan(**params)
            if query_type == 'find_one':
                # Get only one item
                if select == "COUNT":
                    count = 1 if response and response.get('Items') and \
                        len(response.get('Items')) > 0 else 0
                    _ = DEBUG and \
                        log_debug(f'generic_query | COUNT 2: {count}')
                    return count
                return self.remove_decimal_types(
                    response.get('Items')[0] if response and
                    response.get('Items') and
                    len(response.get('Items')) > 0 else {},
                    projection)
            # Get more than one item
            if select == "COUNT":
                count = len(response.get('Items', []))
                _ = DEBUG and \
                    log_debug(f'generic_query | COUNT 3: {count}')
                return count
            return self.remove_decimal_types_list(
                response.get('Items', []), projection)

        if DEBUG:
            log_debug(f'generic_query | ===> secondary Keys found: {keys}')
        condition_values, condition_expresion, attr_names = \
            self.get_condition_expresion_values(keys)
        if DEBUG:
            log_debug(
                'generic_query | ' +
                '===> secondary Keys pre query elements | condition_values: ' +
                str(condition_values) + ' | condition_expresion:' +
                str(condition_expresion)
            )
        params = {
            'IndexName': index_name,
            'ExpressionAttributeValues': condition_values,
            'KeyConditionExpression': condition_expresion,
            'Select': select,
        }
        if condition_expresion:
            params['FilterExpression'] = condition_expresion
        if projection_expression:
            params['ProjectionExpression'] = projection_expression
        if attr_names:
            params['ExpressionAttributeNames'] = attr_names
        response = table.query(**params)
        if DEBUG:
            log_debug(response)
        if query_type == 'find_one':
            # Get only one item
            return self.remove_decimal_types(
                response.get('Items', [])[0], projection)
        # Get more than one item
        return self.remove_decimal_types_list(response.get('Items', []),
                                              projection)

    def find(self, query_params, projection=None):
        """
        Translate MongoDb 'find' to DynamoDb 'query' and returns the iterator

        The MongoDb call style:

        resultset['resultset'] = db.users.find({}, projection).skip(
            int(skip)
        ).limit(int(limit))
        """
        if not projection:
            projection = {}
        if DEBUG:
            log_debug(
                '>>--> find() | table: ' + self.get_table_name() +
                ' | query_params: ' + str(query_params) + ' | projection: ' +
                str(projection)
            )
        return DynamoDbFindIterator(
            self.generic_query(query_params, projection, query_type='find'))

    def find_one(self, query_params, projection=None):
        """
        Translate MongoDb 'find_one' to DynamoDb 'query'' and returns the
        result.

        The MongoDb call style:

        resultset['resultset'] = db.users.find_one({'_id': id}, projection)
        """
        if not projection:
            projection = {}
        if DEBUG:
            log_debug(
                '>>--> find_one() | table: ' + self.get_table_name() +
                ' | query_params: ' + str(query_params) + ' | projection: ' +
                str(projection)
            )
        return self.generic_query(query_params, projection,
                                  query_type='find_one')

    def insert_one(self, new_item):
        """
        Translate MongoDb 'insert_one' to DynamoDb 'put_item' and returns
        the result.

        The MongoDb call style:

        resultset['resultset']['_id'] = str(
            db.users.insert_one(json).inserted_id
        )
        """
        table = self._db_conection.Table(self.get_table_name())
        self.inserted_id = None
        new_item['_id'] = self.new_id()
        new_item = self.convert_floats_to_decimal(new_item)
        _ = DEBUG and log_debug(f'insert_one | new_item: {new_item}')
        try:
            result = table.put_item(Item=new_item)
            self.inserted_id = new_item['_id']
            if DEBUG:
                log_debug(
                    '>>--> RESULT insert_one() | table: ' +
                    self.get_table_name() +
                    ' | new_item: ' + str(new_item) + ' | self.inserted_id: ' +
                    str(self.inserted_id) + ' | result: ' + str(result)
                )
        except botocore.exceptions.ClientError as err:
            log_error(
                'insert_one: Error creating Item [IO_ERR_010]: ' + str(err))
            raise err
        except Exception as err:
            log_error(
                'insert_one: Error creating Item [IO_ERR_020]: ' + str(err))
            raise err
        return self

    def replace_one(self, key_set, update_set_original):
        """
        Translate MongoDb 'replace_one' to DynamoDb 'update_item' and returns
        the result.

        The MongoDb call style:
            (see update_one)
        """
        # Replace what is was in the item
        return self.update_one(key_set, update_set_original)
        # return self.update_one(key_set, {'$set': update_set_original})

    def update_one(self, key_set, update_set_original):
        """
        Translate MongoDb 'update_one' to DynamoDb 'update_item' and returns
        the result.

        The MongoDb call style:

        Case 1: $set
        # Update the item, preserving the attributes not present in
        # the updated_record

        resultset['resultset']['rows_affected'] = str(
          db.users.update_one(
             {'_id': ObjectId(record['_id'])},
             {'$set': updated_record}
          ).modified_count
        )

        Case 2: $addToSet
        # Add a new element to an array in the item

        resultset['resultset']['rows_affected'] = str(
          db.users.update_one(
              {'_id': ObjectId(json[parent_key_field])},
              {'$addToSet': {array_field: json[array_field]}}
          ).modified_count
        )

        Case 3: $pull
        # Remove an existing element from an array in the item

        resultset['resultset']['rows_affected'] = str(
          db.users.update_one(
              {'_id': ObjectId(json[parent_key_field])},
              {'$pull': {
                  array_field: {
                      array_key_field: \
                        json[array_field_in_json][array_key_field]
                  }
              }}
          ).modified_count
        )

        Case 4: none of the above
        # Replace what is was in the item

        resultset['resultset']['rows_affected'] = str(
          db.users.update_one(
             {'_id': ObjectId(record['_id'])},
             updated_record
          ).modified_count
        )


        """
        if DEBUG:
            log_debug(
                '>>--> update_one() | table: ' + self.get_table_name() +
                f' | key_set: {key_set}')
        table = self._db_conection.Table(self.get_table_name())
        key_set = self.convert_floats_to_decimal(self.id_conversion(key_set))
        self.modified_count = None
        keys = self.get_primary_keys(key_set)
        _ = DEBUG and log_debug(f'>>--> update_one() | keys: {keys}')
        if not keys:
            log_warning('update_one: No partition keys found [UO_ERR_010]')
            return False

        result = None
        if '$set' in update_set_original or \
           '$addToSet' in update_set_original or \
           '$pull' in update_set_original:
            try:
                result = table.get_item(Key=keys)
                _ = DEBUG and log_debug('>>--> update_one() | result:' +
                                        f' {result}')
            except Exception as err:
                log_error('update_one: Error getting existing Item' +
                          f' [UO_ERR_030]: {str(err)}')
                return False
            if not result.get('Item'):
                log_error('update_one: Item not found [UO_ERR_040]')
                return False

        _ = DEBUG and log_debug('>>--> update_one() | update_set_original:' +
                                f' {update_set_original}')
        if '$set' in update_set_original:
            # Update the item, preserving the attributes not present in
            # the update_set_original
            update_set = result['Item'].update(update_set_original['$set'])
        elif '$addToSet' in update_set_original:
            # Add a new element to an array in the item
            array_field, array_value = next(
                iter(update_set_original['$addToSet'].items())
            )
            if array_field in result['Item']:
                result['Item'][array_field].append(array_value)
            else:
                result['Item'][array_field] = [array_value]
            update_set = result['Item']
        elif '$pull' in update_set_original:
            # Remove an existing element from an array in the item
            array_field, array_value = next(
                iter(update_set_original['$pull'].items())
            )
            if array_field in result['Item']:
                result['Item'][array_field].remove(array_value)
            update_set = result['Item']
        else:
            # Replace what is was in the item
            update_set = update_set_original

        # To avoid the error:
        # "Float types are not supported. Use Decimal types instead.""
        update_set = self.convert_floats_to_decimal(update_set)

        # Don't include the PK / SK (Primary Key / Sort Key)
        update_set = {k: v for k, v in update_set.items() if k not in keys}

        # Prepare update expresions and values
        expression_attribute_values, update_expression, attr_names = \
            self.get_condition_expresion_values([update_set], ', ')

        _ = DEBUG and log_debug(
            '>>--> update_one()' +
            f'\n| update_set: {update_set}' +
            f'\n| expression_attribute_values: {expression_attribute_values}' +
            f'\n| update_expression: {update_expression}'
        )

        try:
            if DEBUG:
                log_debug(
                    '>>--> BEFORE update_one()' +
                    f' | table: {self.get_table_name()}' +
                    f'\n| update_set: {update_set}' +
                    f'\n| keys: {keys}' +
                    f'\n| self.modified_count: {self.modified_count}' +
                    '\n| expression_attribute_values: ' +
                    f'{expression_attribute_values}' +
                    f'\n| update_expression: {update_expression}'
                )
            params = {
                'Key': keys,
                'UpdateExpression': "SET " + update_expression,
                'ExpressionAttributeValues': expression_attribute_values,
                'ReturnValues': "UPDATED_NEW"
            }
            if attr_names:
                params['ExpressionAttributeNames'] = attr_names
            result = table.update_item(**params)
            self.modified_count = 1
            if DEBUG:
                log_debug(
                    '>>--> RESULT update_one() | table: ' +
                    self.get_table_name() +
                    ' | update_set: ' + str(update_set) + ' | keys: ' +
                    str(keys) +
                    ' | self.modified_count: ' + str(self.modified_count) +
                    ' | expression_attribute_values: ' +
                    str(expression_attribute_values) +
                    ' | update_expression: ' +
                    str(update_expression) + ' | result: ' + str(result)
                )
            return self
        except Exception as err:
            log_error(
                'update_one: Error updating Item [UO_ERR_020]: ' + str(err))
        return False

    def delete_one(self, key_set):
        """
        Translate MongoDb 'delete_one' to DynamoDb 'delete_item' and returns
        the result.

        The MongoDb call style:

        resultset['resultset']['rows_affected'] = str(db.users.delete_one(
          {'_id': ObjectId(user_id)}).deleted_count
        )
        """
        if DEBUG:
            log_debug(
                '>>--> delete_one() | table: ' + self.get_table_name() +
                ' | key_set: ' + str(key_set)
            )
        table = self._db_conection.Table(self.get_table_name())
        key_set = self.id_conversion(key_set)
        self.deleted_count = None
        keys = self.get_primary_keys(key_set)
        if not keys:
            log_warning('delete_one: No partition keys found [DO_ERR_010]')
            return False
        try:
            result = table.delete_item(Key=keys)
            self.deleted_count = 1
            if DEBUG:
                log_debug(
                    '>>--> RESULT delete_one() | table: ' +
                    self.get_table_name() +
                    ' | key_set: ' + str(key_set) + ' | keys: ' + str(keys) +
                    ' | self.deleted_count: ' + str(self.deleted_count) +
                    ' | result: ' + str(result)
                )
            return self
        except Exception as err:
            log_error(
                'delete_one: Error updating Item [DO_ERR_020]: ' + str(err)
            )
        return False

    def count_documents(self, filter):
        """
        Translate MongoDb 'count_documents' to DynamoDb 'scan' and returns
        the result.

        The MongoDb call style:

        resultset['resultset']['count'] = str(
            db.collection_name.count_documents(filter)
        )
        """
        return self.generic_query(query_params=filter, query_type='find',
                                  select="COUNT")


class DynamodbServiceSuper(DbAbstract, DynamoDbUtilities):
    """
    Dynamodb Service super class
    """
    def get_db_connection(self):
        """
        Get the DynamoDB connection
        """
        # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/dynamodb.html
        self._db_params = {}
        if is_local_service():
            self._db_params['endpoint_url'] = \
                self._app_config.DB_CONFIG['mongodb_uri']
        self._db = boto3.resource('dynamodb', **self._db_params)
        self._prefix = self._app_config.DB_CONFIG['dynamdb_prefix']
        self.create_table_name_propeties()
        return self._db

    def create_table_name_propeties(self):
        """
        Create DynamoDb table name class propeties so tables can be retrieved
        as a subscript (like MongoDB tables) using the __getitem__() method.
        """
        item_list = self.list_collections(prefix=self._prefix)
        for item_name in item_list:
            item_props = {
                "TableName": item_name.replace(self._prefix, ''),
                "prefix": self._prefix,
            }
            if DEBUG:
                log_debug(
                    '||| create_table_name_propeties' +
                    f'\n>>--> Setting property: {item_name}' +
                    f' | item_props: {item_props}')
            setattr(
                self,
                item_name,
                DynamoDbTableAbstract(item_props, self._db)
            )

    def list_collection_names(self):
        """
        Returns a list with the collection (table) names
        """
        return map(lambda item_name: item_name, self.list_collections())

    def get_db(self):
        """
        Returns the database object.

        Returns:
            Object: The database object. For DynamoDb, it must returns this
                Class as a whole.
        """
        return self

    def test_connection(self):
        """
        Test the database connection. If the table list can be retrieved,
        the connection is OK.

        Returns:
            str: A JSON string with the table list.
        """
        return dumps(self.list_collection_names(prefix=self._prefix))

    def create_tables(self, dynamodb_table_structures: dict):
        """
        Create the tables in the DynamoDB database.
        """
        default_provisioned_throughput = {
            'ReadCapacityUnits': DEFAULT_READ_CAPACITY_UNITS,
            'WriteCapacityUnits': DEFAULT_WRITE_CAPACITY_UNITS
        }
        item_list = dynamodb_table_structures.keys()
        for item_name in item_list:
            item_props = dynamodb_table_structures.get('Table')
            if not item_props:
                continue
            item_name = item_props["TableName"]
            if DEBUG:
                log_debug('>>--> Creating Dynamodb Table: ' + item_name)
            if self.table_exists(item_name):
                continue
            # Create table in Dynamodb
            table = self._db.create_table(
                TableName=item_name,
                KeySchema=item_props['KeySchema'],
                AttributeDefinitions=item_props
                ['AttributeDefinitions'],
                ProvisionedThroughput=item_props.get(
                    'provisioned_throughput', default_provisioned_throughput
                ),
                GlobalSecondaryIndexes=item_props.get(
                    'GlobalSecondaryIndexes', []
                ),
            )
            # Wait until the table exists.
            table.wait_until_exists()
            # Print out some data about the table.
            if DEBUG:
                log_debug(
                    '>>--> Dynamodb Table: ' + item_name +
                    ' CREATED! - table.item_count: ' + str(table.item_count)
                )

        return True

    def table_exists(self, table_name: str) -> bool:
        """
        Check if the table exists in the database.

        Args:
            table_name (str): The name of the table.

        Returns:
            bool: True if the table exists, False otherwise.
        """
        try:
            self._db.Table(table_name).table_status
        except self._db.meta.client.exceptions.ResourceNotFoundException:
            return False
        return True


class DynamodbService(DynamodbServiceSuper):
    """
    Class for DynamodbService.
    """
    def list_collections(self, collection_name: str = None,
                         prefix: str = None):
        """
        List all or filtered tables in the DynamoDB database.

        Args:
            collection_name (str): The name of one table to filter by.
            prefix (str): The prefix of the tables to filter by.

        Returns:
            list: A list of table names.
        """
        try:
            # Initialize an empty list to hold table names
            table_names = []
            # Use the DynamoDB client to list tables
            # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/dynamodb/client/list_tables.html
            response = self._db.meta.client.list_tables()
            _ = DEBUG and \
                log_debug(f'||| list_collections | response: {response}')
            # Extract table names from the response and add them to the list
            table_names.extend(
                [tn for tn in response.get('TableNames', [])
                 if not prefix or (prefix and tn.startswith(prefix))]
            )
            # Check if there are more tables to fetch
            while 'LastEvaluatedTableName' in response:
                # Fetch more tables starting from the last evaluated table name
                response = self._db.meta.client.list_tables(
                    ExclusiveStartTableName=response['LastEvaluatedTableName']
                )
                # Extract the next set of table names and add them to the list
                table_names.extend(
                    [tn for tn in response.get('TableNames', [])
                     if not prefix or (prefix and tn.startswith(prefix))]
                )
            # Optionally, filter table names if a collection_name is provided
            if collection_name:
                table_names = [name for name in table_names
                               if name == collection_name]
            # Return the list of table names
            _ = DEBUG and \
                log_debug(f'||| list_collections | table_names: {table_names}')
            return table_names
        except Exception as err:
            # Log the exception and return an empty list in case of an error
            log_debug(f"Error fetching table names: {str(err)}")
            return []

    def __getitem__(self, item_name):
        """
        Get the table object using the subscript operator.
        """
        table_name = f"{self._prefix}{item_name}"
        _ = DEBUG and \
            log_debug(f'||| __getitem__ | item_name: {item_name} |' +
                      f' table_name: {table_name}')
        return getattr(self, table_name)


class DynamodbServiceBuilder(DbAbstract):
    """
    Builder class for DynamodbService.
    """
    def __init__(self):
        self._instance = None

    def __call__(self, app_config: Config, **_ignored):
        if not self._instance:
            self._instance = DynamodbService(app_config)
        return self._instance


# ----------------------- Db General -----------------------


# Create a single instance of RequestHandler
# to be used throughout the module
request_handler = RequestHandler()


def set_db_request(request):
    """
    Set the request object for the database.
    This is used to get the current Request object.

    Args:
        request: The request object.

    Returns
        None.
    """
    request_handler.set_request(request)


def get_db_factory():
    """
    Get the database factory for the current database engine.

    Returns
        The database factory.

    Raises
        Exception: If the database engine is not supported.
    """
    settings = Config()
    factory = ObjectFactory()
    current_db_engine = settings.DB_ENGINE
    if DEBUG:
        log_debug(f'>>>--> current_db_engine = {current_db_engine}')
        # log_debug(f'>>>--> settings.DB_CONFIG = {settings.DB_CONFIG}')
    factory.register_builder('DYNAMO_DB', DynamodbServiceBuilder())
    factory.register_builder('MONGO_DB', MongodbServiceBuilder())
    return factory.create(current_db_engine, app_config=settings)


db_factory = LocalProxy(get_db_factory)


def get_db_engine():
    """
    Get the current database engine.
    """
    return db_factory.get_db()


db = LocalProxy(get_db_engine)


def test_connection():
    """
    Test database connection
    """
    return db_factory.test_connection()


# DB utilities


def verify_required_fields(fields: dict, required_fields: list,
                           error_code: str):
    """
    Verify if all the required fields are present in the fields dictionary.

    Args:
        fields (dict): The dictionary containing the fields.
        required_fields (list): The list of required fields.
        error_code (str): The error code to be returned.

    Returns:
        The resultset dictionary containing the error, error_message,
        and resultset. If there are no errors, the resultset will be empty
        and error = False. If there are errors, error = True and error_message
        will contain the missing fields.
    """
    resultset = dict(
        {
            'error': False,
            'error_message': '',
            'resultset': {}
        }
    )
    for element in required_fields:
        if element not in fields:
            # resultset['error_message'] = '{}{}{}'.format(
            #     resultset['error_message'],
            #     ', ' if resultset['error_message'] != '' else '', element
            # )
            resultset['error_message'] = f"{resultset['error_message']}" + \
                f"{', ' if resultset['error_message'] != '' else ''}{element}"
    if resultset['error_message']:
        resultset['error_message'] = 'Missing mandatory elements:' + \
            f" {resultset['error_message']} {error_code}."
        resultset['error'] = True
    return resultset


def get_order_direction(direction: str):
    """
    Get the order direction.

    Args:
        direction (str): The direction to be returned.

    Returns:
        The order direction with the MongoDb constants.
    """
    return pymongo.ASCENDING if direction == "asc" else pymongo.DESCENDING
