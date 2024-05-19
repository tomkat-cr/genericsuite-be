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

from genericsuite.util.app_logger import (
    log_debug,
    log_error,
    log_warning,
)
# from lib.models.dynamodb_table_structures \
#     import dynamodb_table_structures, \
#     DEFAULT_WRITE_CAPACITY_UNITS, DEFAULT_READ_CAPACITY_UNITS

from genericsuite.config.config import Config
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
            log_debug("DB_ABSTRACTOR | MongodbService | get_db_connection" + 
                # f"\n | DB_CONFIG: {self._app_config.DB_CONFIG}" +
                " | Starting...")
        client = pymongo.MongoClient(self._app_config.DB_CONFIG['mongodb_uri'])
        _ = DEBUG and \
            log_debug("DB_ABSTRACTOR | MongodbService | get_db_connection" +
                f"\n | client: {client}" +
                "\n | DB Client OK...") 
        db_connector = client.get_database(
            self._app_config.DB_CONFIG['mongodb_db_name'])
        _ = DEBUG and \
            log_debug("DB_ABSTRACTOR | MongodbService | get_db_connection" +
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

    def prepare_item_with_no_floats(self, item):
        """
        To be used before sending dict to DynamoDb for inserts/updates
        """
        return json.loads(json.dumps(item), parse_float=Decimal)

    def remove_decimal_types(self, item):
        """
        To be used before sending responses to entity
        """
        if DEBUG:
            log_debug('====> remove_decimal_types | item BEFORE: ' + str(item))
        item = self.id_conversion(item)
        # item = json.loads(json.dumps(item, default=str))
        item = json.loads(json.dumps(item, default=float))
        item = self.id_addition(item)
        if DEBUG:
            log_debug('====> remove_decimal_types | item AFTER: ' + str(item))
        return item


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
        if (not self._limit or self._num <= self._limit) and \
           self._data_set and self._num < len(self._data_set):
            # _result = self.prepare_item_with_no_floats(
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
        self.set_table_name(item_structure['TableName'])
        self.set_key_schema(item_structure['KeySchema'])
        self.set_global_secondary_indexes(
            item_structure.get('GlobalSecondaryIndexes', [])
        )
        self.set_attribute_definitions(item_structure['AttributeDefinitions'])
        self._db_conection = db_conection
        self.inserted_id = None
        self.modified_count = None
        self.deleted_count = None

    def set_table_name(self, table_name):
        """
        Set the table name
        """
        self._table_name = table_name

    def set_key_schema(self, key_schema):
        """
        Set the table key schema
        """
        self._key_schema = key_schema

    def set_attribute_definitions(self, attribute_definitions):
        """
        Set the table attribute definitions
        """
        self._attribute_definitions = attribute_definitions

    def set_global_secondary_indexes(self, global_secondary_indexes):
        """
        Set the table global secondary indexes
        """
        self._global_secondary_indexes = global_secondary_indexes

    def get_table_name(self):
        """
        Get the table name
        """
        return self._table_name

    def get_key_schema(self):
        """
        Get the table key schema
        """
        return self._key_schema

    def get_attribute_definitions(self):
        """
        Get the table attribute definitions
        """
        return self._attribute_definitions

    def get_global_secondary_indexes(self):
        """
        Get the table global secondary indexes
        """
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
            tuple: A tuple containing the condition values dictionary and the
                   condition expression string.
        """
        # condition_values = list(map(lambda item: list(
        #   map(lambda key: {':'+key: item[key]}, item.keys())
        # ), data_list))
        condition_values = {}
        for item in data_list:
            for key in item.keys():
                condition_values = condition_values | {':' + key: item[key]}
        expresion_parts = list(
            map(
                lambda item:
                list(map(lambda key: key + ' = :' + key, item.keys())),
                data_list
            )
        )
        condition_expresion = separator.join(expresion_parts[0])
        # return condition_values[0][0], condition_expresion
        return condition_values, condition_expresion

    def get_primary_keys(self, query_params):
        """
        Look for keys in partition/sort key
        """
        keys = list(
            filter(
                lambda key: query_params.get(
                    self.element_name(key)
                    # OJO
                    # ) != None, self.get_key_schema()
                ) is not None,
                self.get_key_schema()
            )
        )
        keys = list(
            map(
                lambda key: {
                    self.element_name(key):
                        query_params.get(self.element_name(key))
                }, keys
            )
        )
        return keys[0] if len(keys) > 0 else None

    def get_global_secondary_indexes_keys(self, query_params):
        """
        Look for keys in global secondary indexes
        """
        # reduced_indexes = list(map(lambda global_index: {
        #     global_index["IndexName"]: list(
        #       map(lambda key: self.element_name(
        #           key
        #       ), global_index["KeySchema"])
        #     )
        # }, self.get_global_secondary_indexes()))
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
                str(index_name) + ' | query_keys: ' + str(query_keys)
            )
        return keys, index_name

    def generic_query(self, query_params, proyection=None):
        """
        Perform a query on the DynamoDB table from MongoDb style query params.

        Args:
            query_params (dict): The parameters for the MongoDb query.
            proyection (dict): The projection for the query. Defaults to an
            empty dictionary.

        Returns:
            dict: The result of the query.
        """
        if not proyection:
            proyection = {}
        if DEBUG:
            log_debug(
                '>>--> generic_query() | table: ' + self.get_table_name() +
                ' | query_params: ' + str(query_params) + ' | proyection: ' +
                str(proyection)
            )

        table = self._db_conection.Table(self.get_table_name())

        if not query_params or len(query_params) == 0:
            response = table.scan()
            return response.get('Items') if response else None

        query_params = self.id_conversion(query_params)
        keys = self.get_primary_keys(query_params)

        if keys:
            if DEBUG:
                log_debug('===> Keys found: ' + str(keys))
            response = table.get_item(Key=keys)
            if DEBUG:
                log_debug(response)
            return self.remove_decimal_types(
                response.get('Item')
            ) if response else None

        keys, index_name = self.get_global_secondary_indexes_keys(query_params)

        if not keys:
            condition_values, condition_expresion = \
                self.get_condition_expresion_values([query_params])
            if DEBUG:
                log_debug(
                    'No keys found... perform fullscan | condition_values: ' +
                    str(condition_values) + ' | condition_expresion: ' +
                    str(condition_expresion)
                )
            response = table.scan(
                ExpressionAttributeValues=condition_values,
                FilterExpression=condition_expresion
            )
            return self.remove_decimal_types(
                response.get('Items')[0]
            ) if response else None

        if DEBUG:
            log_debug('===> secondary Keys found: ' + str(keys))
            log_debug(keys)
        condition_values, condition_expresion = \
            self.get_condition_expresion_values(keys)
        if DEBUG:
            log_debug(
                '===> secondary Keys pre query elements | condition_values: ' +
                str(condition_values) + ' | condition_expresion:' +
                str(condition_expresion)
            )
        response = table.query(
            IndexName=index_name,
            ExpressionAttributeValues=condition_values,
            KeyConditionExpression=condition_expresion
        )

        if DEBUG:
            log_debug(response)
        if response and len(response.get('Items', [])) > 0:
            return self.remove_decimal_types(response.get('Items')[0])
        return None

    def find(self, query_params, proyection=None):
        """
        Translate MongoDb 'find' to DynamoDb 'query' and returns the iterator

        The MongoDb call style:

        resultset['resultset'] = db.users.find({}, projection).skip(
            int(skip)
        ).limit(int(limit))
        """
        if not proyection:
            proyection = {}
        if DEBUG:
            log_debug(
                '>>--> find() | table: ' + self.get_table_name() +
                ' | query_params: ' + str(query_params) + ' | proyection: ' +
                str(proyection)
            )
        return DynamoDbFindIterator(
            self.generic_query(query_params, proyection)
        )

    def find_one(self, query_params, proyection=None):
        """
        Translate MongoDb 'find_one' to DynamoDb 'query'' and returns the
        result.

        The MongoDb call style:

        resultset['resultset'] = db.users.find_one({'_id': id}, projection)
        """
        if not proyection:
            proyection = {}
        if DEBUG:
            log_debug(
                '>>--> find_one() | table: ' + self.get_table_name() +
                ' | query_params: ' + str(query_params) + ' | proyection: ' +
                str(proyection)
            )
        return self.generic_query(query_params, proyection)

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
        new_item = self.prepare_item_with_no_floats(new_item)
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
            return self
        except Exception as err:
            log_error(
                'insert_one: Error creating Item [IO_ERR_010]: ' + str(err)
            )
        return False

    def replace_one(self, key_set, update_set_original):
        """
        Translate MongoDb 'replace_one' to DynamoDb 'update_item' and returns
        the result.

        The MongoDb call style:
            (see update_one)
        """
        return self.update_one(key_set, {'$set': update_set_original})

    def update_one(self, key_set, update_set_original):
        """
        Translate MongoDb 'update_one' to DynamoDb 'update_item' and returns
        the result.

        The MongoDb call style:

        Case 1: $set

        resultset['resultset']['rows_affected'] = str(
          db.users.update_one(
             {'_id': ObjectId(record['_id'])},
             {'$set': updated_record}
          ).modified_count
        )

        Case 2: $addToSet

        resultset['resultset']['rows_affected'] = str(
          db.users.update_one(
              {'_id': ObjectId(json[parent_key_field])},
              {'$addToSet': {array_field: json[array_field]}}
          ).modified_count
        )

        Case 3: $pull

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
        """
        if DEBUG:
            log_debug(
                '>>--> update_one() | table: ' + self.get_table_name() +
                ' | key_set: ' + str(key_set)
            )
        table = self._db_conection.Table(self.get_table_name())
        key_set = self.prepare_item_with_no_floats(self.id_conversion(key_set))
        self.modified_count = None
        keys = self.get_primary_keys(key_set)
        if not keys:
            log_warning('update_one: No partition keys found [UO_ERR_010]')
            return False
        if '$set' in update_set_original:
            update_set = update_set_original['$set']
        elif '$addToSet' in update_set_original:
            pass
        elif '$pull' in update_set_original:
            pass
        update_set = self.prepare_item_with_no_floats(update_set)
        expression_attribute_values, update_expression = \
            self.get_condition_expresion_values([update_set], ', ')
        try:
            if DEBUG:
                log_debug(
                    '>>--> BEFORE update_one() | table: ' +
                    self.get_table_name() +
                    ' | update_set: ' + str(update_set) + ' | keys: ' +
                    str(keys) +
                    ' | self.modified_count: ' + str(self.modified_count) +
                    ' | expression_attribute_values: ' +
                    str(expression_attribute_values) +
                    ' | update_expression: ' +
                    str(update_expression)
                )
            result = table.update_item(
                Key=keys,
                UpdateExpression="SET " + update_expression,
                ExpressionAttributeValues=expression_attribute_values,
                ReturnValues="UPDATED_NEW"
            )
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
                'update_one: Error ipdating Item [UO_ERR_020]: ' + str(err)
            )
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
                'delete_one: Error ipdating Item [DO_ERR_020]: ' + str(err)
            )
        return False


class DynamodbServiceSuper(DbAbstract, DynamoDbUtilities):
    """
    Dynamodb Service super class
    """
    def get_db_connection(self):
        self._db = boto3.resource('dynamodb')
        # self.create_table_name_propeties()
        return self._db

    def create_table_name_propeties(self):
        """
        Create DynamoDb table name propeties
        """
        item_list = self.list_collections()
        for item_props in item_list:
            item_name = item_props["TableName"]
            if DEBUG:
                log_debug('>>--> Setting property: ' + item_name)
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
        Test the database connection (fake).

        Returns:
            str: The test result.
        """
        return dumps(self.list_collection_names())

    def create_tables(self):
        """
        Create the tables in the database.
        """
        default_provisioned_throughput = {
            'ReadCapacityUnits': DEFAULT_READ_CAPACITY_UNITS,
            'WriteCapacityUnits': DEFAULT_WRITE_CAPACITY_UNITS
        }
        item_list = self.list_collections()
        for item_props in item_list:
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
    def list_collections(self, collection_name: str = None):
        """
        List all collections in the database.
        """

        try:
            # Initialize an empty list to hold table names
            table_names = []
            # Use the DynamoDB client to list tables
            response = self._db.meta.client.list_tables()
            # Extract table names from the response and add them to the list
            table_names.extend(response.get('TableNames', []))
            # Check if there are more tables to fetch
            while 'LastEvaluatedTableName' in response:
                # Fetch more tables starting from the last evaluated table name
                response = self._db.meta.client.list_tables(
                    ExclusiveStartTableName=response['LastEvaluatedTableName']
                )
                # Extract table names and add them to the list
                table_names.extend(response.get('TableNames', []))
            # Optionally, filter table names if a collection_name is provided
            if collection_name:
                table_names = [name for name in table_names if name == collection_name]
            # Return the list of table names
            return table_names
        except Exception as err:
            # Log the exception and return an empty list in case of an error
            log_debug(f"Error fetching table names: {str(err)}")
            return []


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
