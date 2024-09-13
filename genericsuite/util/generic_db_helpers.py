"""
Generic Database Helper, to handle all operations over a given table.
"""
from typing import Optional, Union
from itertools import islice
import json
import re

from bson.json_util import dumps, ObjectId

from genericsuite.util.app_logger import log_debug
from genericsuite.util.datetime_utilities import (
    current_datetime_timestamp,
    get_date_range_filter,
)
from genericsuite.util.utilities import (
    get_standard_base_exception_msg,
    get_default_resultset,
    email_verification,
    sort_list_of_dicts,
)
from genericsuite.util.db_abstractor import (
    verify_required_fields,
    get_order_direction,
)
from genericsuite.util.nav_helpers import (
    put_total_pages_in_resultset,
    put_total_pages_from_resultset
)
from genericsuite.util.passwords import Passwords
from genericsuite.util.generic_db_helpers_super import GenericDbHelperSuper


DEBUG = False


class GenericDbHelper(GenericDbHelperSuper):
    """
    Generic Database Helper, to handle all operations over a given table.
    """
    def fetch_list(
        self,
        skip: int,
        limit: int,
        like_query_params: Optional[dict] = None,
        combinator: Optional[str] = None,
        order_param: Optional[Union[str, None]] = None,
    ) -> dict:
        """
        Fetches a list of items from the table based on
        the provided skip, limit, SQL-like filtering params and
        query parameters.

        Args:
            skip (int): The number of items to skip.
            limit (int): The maximum number of items to return.
                Zero means no limit.
            like_query_params (dict): The elements and its values to filter
                the items as SQL LIKE.
            combinator (str): condition combinator for the filter.
                It could be $and, $or, $not. Defaults to $and.

        Returns:
            dict: The resultset containing the list of items.
            Mandatory filters will be applied.
        """
        resultset = get_default_resultset()
        if self.error_message:
            resultset['error_message'] = self.error_message
            resultset['error'] = True
            return resultset

        if not like_query_params:
            like_query_params = {}
        if not combinator:
            combinator = '$and'

        # The resulting will be something like:
        # listing_filter BEFORE: {'meal_date': {'$lte': 946702800.0,
        # '$gte': 946616400.0}, 'observations': {'$regex':
        # '.*sancocho.*', '$options': 'si'}, 'user_id': 'XXXX'}
        listing_filter = {
            # SQL LIKE in MongoDb
            k: {
                '$regex': f".*{v}.*",
                '$options': 'si',
            } if k not in self.mandatory_filters
            and not self.is_datefield(k)
            # Date range
            else get_date_range_filter(v)
            if k not in self.mandatory_filters
            and self.is_datefield(k)
            # Normal filter
            else v
            for k, v in like_query_params.items()
            # Exclude paging and search configuration parameters
            if k not in ['page', 'limit', 'like', 'comb', 'order']
        }

        if '_id' in listing_filter:
            try:
                listing_filter['_id'] = ObjectId(listing_filter['_id'])
            except ValueError:
                resultset['error_message'] = \
                    f"_id `{listing_filter['_id']}` is invalid [FUL3]."
            except BaseException as err:
                resultset['error_message'] = \
                    get_standard_base_exception_msg(err, 'FUL4')

        if resultset['error_message']:
            resultset['error'] = True
            return resultset

        if self.query_params.get("only_listing_cols", "1") == "1":
            # By default, include only listing enabled columns and
            # unprotected columns (those not in projection_exclusions)
            projection = self.listing_disabled_columns_projection()
        else:
            # include only unprotected columns (those not in
            # projection_exclusions)
            projection = self.listing_projection_exclusions()

        # The resulting will be something like:
        # {'$or': [{'$and': [{'user_id': 'XXXX'},
        # {'meal_date': {'$lte': 946702800.0, '$gte': 946616400.0}}]},
        # {'$and': [{'user_id': 'XXXX'}, {'observations':
        # {'$regex': '.*sanncocho.*', '$options': 'si'}}]}]}
        listing_filter = self.add_mandatory_filters(listing_filter, combinator)

        _ = DEBUG and \
            log_debug(f"FETCH_LIST | self.table_name: {self.table_name}" +
                      f"\n | combinator: {combinator}" +
                      f"\n | like_query_params: {like_query_params}" +
                      f"\n | listing_filter: {listing_filter}")

        column_name, direction = self.get_sort_config(order_param)
        _ = DEBUG and \
            log_debug(f"FETCH_LIST 010 | column_name: {column_name}," +
                      f" direction: {direction}")

        try:
            db_result = (
                self.table_obj.find(
                    listing_filter, projection
                )
                .sort(
                    column_name,
                    get_order_direction(direction)
                )
            )
            if skip > 0:
                db_result = db_result.skip(int(skip))
            if limit > 0:
                db_result = db_result.limit(int(limit))
            resultset['resultset'] = dumps(db_result)
            _ = DEBUG and \
                log_debug(f"FETCH_LIST 020 | resultset: {resultset}")
        except BaseException as err:
            resultset['error_message'] = get_standard_base_exception_msg(
                err, 'FUL1'
            )
            resultset['error'] = True
        resultset = put_total_pages_in_resultset(
            self.table_obj,
            listing_filter,
            limit,
            resultset,
            'FUL2'
        )
        _ = DEBUG and \
            log_debug(f"FETCH_LIST 030 | resultset: {resultset}")
        return self.run_specific_func('list', resultset)

    def fetch_row(self, row_id: str, projection: dict = None) -> dict:
        """
        Fetches a row from the database based on the given row_id.

        Args:
            row_id (str): The ID of the row to fetch.
            projection (dict, optional): The projection to apply to the
            fetched row.

        Returns:
            dict: The resultset containing the fetched row.
        """
        resultset = get_default_resultset()
        if self.error_message:
            resultset['error_message'] = self.error_message
            resultset['error'] = True
            return resultset

        if not projection:
            projection = {}

        db_row = self.fetch_row_raw(row_id, projection)
        if not db_row['resultset']:
            resultset['error_message'] = f"Id {row_id} doesn't exist [FU1]."
        elif db_row['error']:
            resultset['error_message'] = db_row['error_message']

        if resultset['error_message']:
            resultset['error'] = True
            return resultset

        try:
            resultset['resultset'] = dumps(db_row['resultset'])
        except BaseException as err:
            resultset['error_message'] = \
                get_standard_base_exception_msg(err, 'FU2')
            resultset['error'] = True

        return self.run_specific_func('read', resultset)

    def fetch_row_by_entryname_raw(
        self,
        entry_name: str,
        entry_value: str,
        filters: dict = None,
    ) -> dict:
        """
        Fetches a row from the database based on the given
        entry_name and entry_value and returns it without
        applying dumps() to the 'resultset' element.

        Args:
            entry_name (str): The name of the entry to filter by.
            entry_value (str): The value of the entry to filter by.
            filters (dict, optional): Additional filters to apply.
            e.g. user_id.

        Returns:
            dict: The resultset containing the fetched row.
        """
        resultset = get_default_resultset()
        if self.error_message:
            resultset['error_message'] = self.error_message
            resultset['error'] = True
            return resultset

        filters = {} if not filters else filters
        filters.update({entry_name: entry_value})
        try:
            resultset['resultset'] = self.table_obj.find_one(
                filters
            )
        except BaseException as err:
            resultset['error_message'] = \
                get_standard_base_exception_msg(err, 'FUBEN1')
            resultset['error'] = True
        _ = DEBUG and \
            log_debug("fetch_row_by_entryname_raw: " +
                      f"entry_name: {entry_name}" +
                      f" | entry_value: {entry_value}" +
                      f" | resultset: {resultset}")
        return resultset

    def create_row(
        self,
        data: dict,
        filters: dict = None,
    ) -> dict:
        """
        Creates a new row in the database based on the given data.

        Args:
            data (dict): The data to be inserted into the database.
            filters (dict, optional): Additional filters to apply in
            pre-create verification.

        Returns:
            dict: The resultset containing the ID of the newly
            created row and the number of affected rows.
        """
        psw_class = Passwords()
        resultset = get_default_resultset()
        if self.error_message:
            resultset['error_message'] = self.error_message
            resultset['error'] = True
            return resultset

        filters = {} if not filters else filters
        data['creation_date'] = data['update_date'] = \
            current_datetime_timestamp()
        # Verify required fields are in the item data supplied
        mandatory_fields = self.get_mandatory_fields(data, is_create=True)
        resultset = verify_required_fields(data, mandatory_fields, '[CU6]')
        if resultset['error_message']:
            resultset['error'] = True
            return resultset
        # Verify emails to be valid for 'email_verification' attribute list
        if self.cnf_db.get('email_verification'):
            resultset = email_verification(
                data,
                self.cnf_db.get('email_verification')
            )
        if resultset['error_message']:
            resultset['error'] = True
            return resultset
        # Add table's mandatoy filters. E.g. user_id
        filters.update({
            k: v for k, v in self.mandatory_filters.items()
        })
        # Set secondary key attribute name and value to verify exisitng item
        pk_name = self.cnf_db.get('creation_pk_name', '_id')
        pk_value = data.get(pk_name, None)
        _ = DEBUG and \
            log_debug(f'>>>---> Create {self.table_name} | ' +
                      f'pk_name: {pk_name} | pk_value: {str(pk_value)}')
        if pk_name == '_id' and pk_value:
            pk_value = ObjectId(pk_value)
        # Verify if the item already exists
        db_row = self.fetch_row_by_entryname_raw(pk_name, pk_value, filters)
        if db_row['resultset']:
            _ = DEBUG and \
                log_debug(f'Create {self.name} | db_row["resultset"]:' +
                          f' {db_row["resultset"]}')
            resultset['error_message'] = \
                f"{self.name} {str(pk_value)} already exists [CU4]."
        elif db_row['error']:
            resultset['error_message'] = db_row['error_message']

        if resultset['error_message']:
            resultset['error'] = True
            return resultset

        # Encrypt passwords
        if self.cnf_db.get('passwords'):
            data = psw_class.passwords_encryption(
                data,
                self.cnf_db['passwords']
            )
        # Creates the new item
        try:
            resultset['resultset']['_id'] = str(
                self.table_obj.insert_one(data).inserted_id
            )
        except BaseException as err:
            resultset['error_message'] = \
                get_standard_base_exception_msg(err, 'CU5')
            resultset['error'] = True
        else:
            resultset['resultset']['rows_affected'] = '1'

        return self.run_specific_func('create', resultset)

    def update_row(self, record: dict, options: dict = None) -> dict:
        """
        Updates a existing row in the database based on the given data.
        If password type fields are configured, it preserves it
        from the original row in case isn't included in the
        modified row (record).
        It figures out the corresponding primary key looking for
        "id" or "_id" in the record columns.

        Args:
            record (dict): The data to be inserted into the database.
            options (dict): options. Defaults to {}.
                "update_item" (str): "1" apply update_one() instead
                    of replace_one(). Defaults to "0"

        Returns:
            dict: The resultset containing the number of affected rows.
        """
        resultset = get_default_resultset()
        if self.error_message:
            resultset['error_message'] = self.error_message
            resultset['error'] = True
            return resultset

        options = {} if options is None else options
        if self.cnf_db.get('updateItem'):
            options["update_item"] = self.cnf_db.get('updateItem')
        mandatory_fields = self.get_mandatory_fields(record)
        updated_record = dict(record)
        updated_record['update_date'] = current_datetime_timestamp()

        _ = DEBUG and \
            log_debug(f'>>>---> Update {self.table_name} | ' +
                      f'updated_record (before): {updated_record}')

        resultset = verify_required_fields(updated_record,
                                           mandatory_fields, '[UU1]')
        if resultset['error']:
            return resultset

        resultset = get_default_resultset()

        if '_id' not in record and 'id' in record:
            # Only one ID should be in the original record, and must be _id,
            # because it's the field used to update the specific ID.
            record['_id'] = record['id']
            del record['id']

        if '_id' in updated_record:
            # To avoid "WriteError('Performing an update on the path '_id'
            # would modify the immutable field '_id'
            del updated_record['_id']
        if 'id' in updated_record:
            del updated_record['id']

        if self.cnf_db.get('passwords'):
            encrypt_pasw_rs = self.passwords_encryption_on_update(
                record, updated_record, self.cnf_db['passwords']
            )
            if encrypt_pasw_rs['error']:
                resultset['error_message'] = encrypt_pasw_rs['error_message']
                resultset['error'] = True
                return resultset
            updated_record = encrypt_pasw_rs['updated_record']

        _ = DEBUG and \
            log_debug(f'>>>---> PERFORM Update {self.table_name}' +
                      f' | ID: {record["_id"]}')

        try:
            if options.get("update_item", "0") == "0":
                # Replace what is was in the item
                op_result = self.table_obj.replace_one(
                    {'_id': ObjectId(record['_id'])},
                    updated_record
                ).modified_count
            else:
                # Update the item, preserving the attributes not present in
                # the updated_record
                op_result = self.table_obj.update_one(
                    {'_id': ObjectId(record['_id'])},
                    {'$set': updated_record}
                ).modified_count
            resultset['resultset']['rows_affected'] = str(op_result)
            # Ensure the _id is returned for the specific function
            resultset['resultset']['_id'] = str(record['_id'])
        except BaseException as err:
            resultset['error_message'] = \
                get_standard_base_exception_msg(err, 'UU2')
            resultset['error'] = True

        _ = DEBUG and \
            log_debug(f'>>>---> Update {self.table_name} | ' +
                      f'updated_record (after): {updated_record}')

        return self.run_specific_func('update', resultset)

    def delete_row(self, remove_id: str) -> dict:
        """
        Deletes a existing row in the database.

        Args:
            remove_id (str): id of the row to be deleted.

        Returns:
            dict: The resultset containing the number of affected rows.
        """
        resultset = get_default_resultset()
        if self.error_message:
            resultset['error_message'] = self.error_message
            resultset['error'] = True
            return resultset

        db_row = self.fetch_row_by_entryname_raw('_id', ObjectId(remove_id))
        if not db_row['resultset']:
            resultset['error_message'] = \
                f"error: {self.name} {remove_id} doesn't exist [DU1]."
        elif db_row['error']:
            resultset['error_message'] = db_row['error_message']

        if resultset['error_message']:
            resultset['error'] = True
            return resultset

        try:
            resultset['resultset']['rows_affected'] = str(
                self.table_obj.delete_one(
                    {'_id': ObjectId(remove_id)}
                ).deleted_count
            )
            # Ensure the _id is returned for the specific function
            resultset['resultset']['_id'] = str(remove_id)
        except BaseException as err:
            resultset['error_message'] = \
                get_standard_base_exception_msg(err, 'DU2')
            resultset['error'] = True

        return self.run_specific_func('delete', resultset)

    # ----- Array row operations.

    def fetch_array_rows(
        self,
        row_id: str,
        filters: dict = None,
        skip: int = 0,
        limit: int = None,
        like_query_params: Optional[dict] = None,
        combinator: Optional[str] = None,
        order_param: str = None,
    ) -> dict:
        """
        Fetches a list of items from a row array based on
        the provided skip, limit, SQL-like filtering params and
        query parameters.

        Args:
            row_id (str): primary key of the row that holds the array field.
            filters (dict): The elements and its values to filter
                the items, e.g. the item ID / Primary Key. Defaults to None.
            skip (int): The number of items to skip.
            limit (int): The maximum number of items to return.
                Zero means no limit.
            like_query_params (dict): The elements and its values to filter
                the items as SQL LIKE.
            combinator (str): condition combinator for the filter.
                It could be $and, $or, $not. Defaults to $and.

        Returns:
            dict: The resultset containing the list of items
            in the row's array.
        """
        resultset = get_default_resultset()
        if self.error_message:
            resultset['error_message'] = self.error_message
            resultset['error'] = True
            return resultset

        if not like_query_params:
            like_query_params = {}
        if not combinator:
            combinator = '$and'
        projection = {
            self.array_field: 1
        }

        db_parent_row = self.fetch_row_raw(row_id, projection)
        if not db_parent_row['resultset']:
            resultset['error_message'] = \
                f'Id {row_id} doesn\'t exist [FUFT1].'
        elif db_parent_row['error']:
            resultset['error_message'] = db_parent_row['error_message']
        if resultset['error_message']:
            resultset['error'] = True
            return resultset

        response = db_parent_row['resultset'].get(self.array_field, [])

        if filters is not None:
            for filter_key in filters:
                response = list(
                    filter(
                        lambda x, key=filter_key: x.get(key) == filters[key],
                        response
                    )
                )

        if len(like_query_params):
            parent_keys = self.get_parent_key_fieldnames()
            lf = {
                # SQL LIKE in MongoDb
                k: {
                    "type": 'regex',
                    "$regex": f".*{v}.*",
                } if not self.is_datefield(k)
                # Date range
                else get_date_range_filter(v, {"type": 'range'})
                if self.is_datefield(k)
                # Normal filter
                else {
                    "value": v
                }
                for k, v in like_query_params.items()
                # Exclude paging and search configuration parameters
                if k not in ['page', 'limit', 'like', 'comb', 'order']
                and k not in parent_keys
            }
            # Create a list of filters based on lf (acronim of listing filters)
            all_filters = [
                lambda x, key=filter_key:
                re.search(lf[key]["$regex"], x.get(key, ''),
                          re.IGNORECASE) is not None
                if lf[key]["type"] == "regex"
                else (x.get(key) <= lf[key]["$lte"] and
                      x.get(key) >= lf[key]["$gte"])
                if lf[key]["type"] == "range"
                else x.get(key) == lf[key]["value"]
                for filter_key in lf
            ]
            _ = DEBUG and \
                log_debug(
                    f'\nfetch_array_rows | lf: {lf}' +
                    f'\nfetch_array_rows | all_filters: {all_filters}\n')
            # Apply filters using OR logic
            response = list(
                filter(
                    lambda x: any(f(x) for f in all_filters),
                    response
                )
            )

        try:
            resultset['resultset'] = dumps(response)
        except BaseException as err:
            resultset['error_message'] = get_standard_base_exception_msg(
                err, 'FUFT2'
            )
            resultset['error'] = True
        # All entries are needed to calculate total pages
        resultset = put_total_pages_from_resultset(
            limit,
            resultset,
        )
        # Now entries are sliced to return only the entries
        # corresponding to the requested page
        limit_for_slice = None if limit == 0 else limit
        response = json.loads(resultset['resultset'])
        response = list(islice(islice(response, skip, None), limit_for_slice))

        # Sort the result
        column_name, direction = self.get_sort_config(order_param)
        response = sort_list_of_dicts(
            data=response,
            column_name=column_name,
            direction=direction
        )

        resultset['resultset'] = dumps(response)
        return self.run_specific_func('list', resultset)

    def add_array_item_to_row(self, data: dict) -> dict:
        """
        Creates a new item in a row array based on the
        given data. It can prevent already existing items
        or allow duplicates.
        The parent row primary key is determined by the
        configuration (see get_parent_keys()) and if the
        "uuid_generator" attribute is in the 'fieldElements'
        configuration, it will generate a UUID4 for the
        key_fieldname (as defined in self.array_field_key).

        Args:
            data (dict): The data to be inserted into the row.

            e.g. the row primary key is "daily_meal_id" and the
            row array is 'meal_ingredients'. In this example
            a new item will be inserted in the array with the
            values of 'food_moment_id', 'calories_value' and
            'calories_unit'.

            {'daily_meal_id': 'XXXX',
             'meal_ingredients':
                {'food_moment_id': 'YYYY',
                 'calories_value': 110,
                 'calories_unit': 'kcal',
                }
            }

        Returns:
            dict: The resultset containing the ID of the newly
            created row and the number of affected rows.
        """
        _ = DEBUG and \
            log_debug('\nadd_array_item_to_row - data' +
                      f'{data}\n')
        resultset = get_default_resultset()
        if self.error_message:
            resultset['error_message'] = self.error_message
            resultset['error'] = True
            return resultset

        parent_keys = self.get_parent_keys(data)

        if not self.allow_duplicates:
            # Get the array field ID, if not exists, returns an error
            try:
                key_value = data[self.array_field].get(self.array_field_key)
            except BaseException as err:
                resultset['error_message'] = \
                    get_standard_base_exception_msg(err, 'AFTTU2')
                resultset['error'] = True
                return resultset
            # Verify array field ID dupes
            if key_value:
                key_existence = self.get_array_item_in_row(key_value,
                                                           parent_keys)
                if key_existence['error']:
                    return key_existence
                if int(key_existence['resultset']['rows_count']) > 0:
                    resultset['error_message'] = \
                        f'error: {self.name} ' + \
                        f'{key_value} already exist [AFTTU3].'
                    resultset['error'] = True
                    return resultset

        # Check UUID generator
        data = self.uuid_generator_check(data, self.array_field_key,
                                         self.array_field)

        # Add the array field ID and time
        add_to_set = {
            self.array_field: data[self.array_field]
        }
        try:
            resultset['resultset']['rows_affected'] = str(
                self.table_obj.update_one(
                    parent_keys,
                    {'$addToSet': add_to_set}
                ).modified_count
            )
            # Ensure the _id is returned for the specific function
            resultset['resultset']['_id'] = str(parent_keys['_id'])
        except BaseException as err:
            resultset['error_message'] = \
                get_standard_base_exception_msg(err, 'AFTTU1')
            resultset['error'] = True
        return self.run_specific_func('create', resultset)

    def remove_array_item_from_row(self, data: dict) -> dict:
        """
        Removes one item in a row array based on the given data.
        The parent row primary key is determined by the
        configuration (see get_parent_keys())

        E.g. 'data' given is:

            {'daily_meal_id': 'XXXX',
             'meal_ingredients':
                {'food_moment_id': 'YYYY',
                 'calories_value': 110,
                 'calories_unit': 'kcal',
                 'id': 'ZZZZ',
                 'quantity': 1, ...
                },
             'meal_ingredients_old':
                {'food_moment_id': 'YYYY',
                 'calories_value': 110,
                 'calories_unit': 'kcal',
                 'id': 'ZZZZ',
                 'quantity': 2, ...
                }
            }

        The self.array_field configuration is "meal_ingredients",
        "meal_ingredients_old" exist in 'data', and
        self.array_field_key configuration is "id",

        So it will $pull (remove) the element 'id': 'ZZZZ'
        as pull_element will be:
            pull_element={'meal_ingredients': {'id': 'ZZZZ'}}
        and parent_keys (row's PK) is: {'_id': ObjectId('XXXX')}

        Args:
            data (dict): The data to be inserted into the row.

        Returns:
            dict: The resultset containing the number of affected rows.
        """
        _ = DEBUG and \
            log_debug('\nremove_array_item_from_row - data' +
                      f'{data}\n')
        resultset = get_default_resultset()
        if self.error_message:
            resultset['error_message'] = self.error_message
            resultset['error'] = True
            return resultset

        array_field_in_json = self.array_field
        if f'{array_field_in_json}_old' in data:
            # This is for older entry deletion,
            # when the key field has been changed
            array_field_in_json = f'{array_field_in_json}_old'
        _ = DEBUG and \
            log_debug(f'\n$pull from "{self.array_field}", ' +
                      f'array_field_key={self.array_field_key}' +
                      f'\narray_field_in_json={array_field_in_json}, ' +
                      'key value to REMOVE=' +
                      f'{data[array_field_in_json][self.array_field_key]}\n')
        pull_element = {
            self.array_field: {
                self.array_field_key:
                    data[array_field_in_json][self.array_field_key]
            }
        }
        _ = DEBUG and \
            log_debug(f'pull_element={pull_element}')

        parent_keys = self.get_parent_keys(data)

        _ = DEBUG and \
            log_debug(f'parent_keys: {parent_keys}\n')
        try:
            resultset['resultset']['rows_affected'] = str(
                self.table_obj.update_one(
                    parent_keys,
                    {'$pull': pull_element}
                ).modified_count
            )
            # Ensure the _id is returned for the specific function
            resultset['resultset']['_id'] = str(parent_keys['_id'])
        except BaseException as err:
            resultset['error_message'] = \
                get_standard_base_exception_msg(err, 'RFTTU')
            resultset['error'] = True
        return self.run_specific_func('delete', resultset)

    def get_array_item_in_row(self, array_item_id: str,
                              parent_keys: dict) -> dict:
        """
        Retrieves the items count in a row's array.

        Args:
            array_item_id (str): The ID of the array item to search for.
            parent_keys (dict): The keys identifying the parent row.

        Returns:
            dict: The resultset containing the count of items in the row.
        """
        _ = DEBUG and \
            log_debug('\nget_array_item_in_row - array_item_id:' +
                      f' {str(array_item_id)}' +
                      f' | parent_keys: {str(parent_keys)}\n')
        resultset = get_default_resultset()
        if self.error_message:
            resultset['error_message'] = self.error_message
            resultset['error'] = True
            return resultset

        find_criteria = dict(parent_keys)
        find_criteria.update({
            self.array_field: {
                '$elemMatch': {
                    self.array_field_key: array_item_id
                }
            },
        })
        _ = DEBUG and \
            log_debug('self.table_obj | find_criteria:' +
                      f'{find_criteria}\n')
        try:
            resultset['resultset']['rows_count'] = str(
                self.table_obj.count_documents(find_criteria)
            )
        except BaseException as err:
            resultset['error_message'] = \
                get_standard_base_exception_msg(err, 'GFMIU-010')
            resultset['error'] = True
        _ = DEBUG and \
            log_debug(f">>--> get_array_item_in_row | resultset: {resultset}")
        return self.run_specific_func('read', resultset)
