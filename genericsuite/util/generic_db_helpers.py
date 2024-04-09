"""
Generic Database Helper, to handle all operations over a given table.
"""
from typing import Optional
from itertools import islice
from uuid import uuid4
import json
import re

from bson.json_util import dumps, ObjectId

from genericsuite.util.app_logger import log_debug, log_error
from genericsuite.util.config_dbdef_helpers import get_json_def_both
from genericsuite.util.datetime_utilities import (
    current_datetime_timestamp,
    get_date_range_filter,
)
from genericsuite.util.utilities import (
    get_standard_base_exception_msg,
    get_default_resultset,
    get_query_params,
    get_request_body,
    email_verification,
    sort_list_of_dicts,
)
from genericsuite.util.db_abstractor import (
    # set_db_request,
    db,
    verify_required_fields,
    get_order_direction,
)
from genericsuite.util.nav_helpers import (
    put_total_pages_in_resultset,
    put_total_pages_from_resultset
)
from genericsuite.util.passwords import Passwords

DEBUG = False


class GenericDbHelper:
    """
    Generic Database Helper, to handle all operations over a given table.
    """
    def __init__(self, json_file, request=None, db_type=None) -> None:

        # set_db_request(request)

        self.error_message = None
        self.json_file = json_file
        self.cnf_db = get_json_def_both(json_file)

        # log_debug(f">>> self.cnf_db: {self.cnf_db}")

        self.request = request
        self.query_params = get_query_params(self.request)
        self.request_body = get_request_body(self.request)

        self.table_name = json_file
        self.name = json_file.capitalize()
        self.title = f"{json_file.capitalize()}s"
        self.table_obj = None

        self.table_type = None
        self.sub_type = None
        self.array_field = None
        self.array_field_key = None
        self.parent_key_field = None
        self.parent_key_names = []

        self.allow_duplicates = False
        self.mandatory_filters = []

        if db_type:
            self.db_type = db_type
        else:
            self.db_type = 'db'
            self.table_name = self.cnf_db['table_name']
            self.name = self.cnf_db.get('name', self.name)
            self.title = self.cnf_db.get('title', self.title)
            try:
                _ = DEBUG and \
                    log_debug(f"||| GenericDbHelper | db: {db}")
                self.table_obj = db[self.table_name]
                _ = DEBUG and \
                    log_debug(f"||| GenericDbHelper | self.table_obj: {self.table_obj}")
            except BaseException as error:
                self.error_message = f"ERROR connecting to Database: {str(error)}"
                log_error(self.error_message)
            if not self.error_message:
                self.allow_duplicates = self.cnf_db.get('allow_duplicates',
                                                        False)
                self.mandatory_filters = self.replace_special_vars(
                    self.cnf_db.get('mandatoryFilters', {})
                )
                # table_type: could be ["main_table"] | "child_listing"
                self.table_type = self.cnf_db.get('type', "main_table")
                # table_type: could be [""] | "array"
                self.sub_type = self.cnf_db.get('subType', "")
                # Examples of array sub_type's child_listing definitions:
                # array_field = 'food_times'
                # array_field_key = 'food_moment_id'
                # parent_key_field = 'user_id'
                if self.table_type == "child_listing" and \
                   self.sub_type == "array":
                    self.array_field = self.cnf_db.get('array_name')
                    self.array_field_key = self.cnf_db['primaryKeyName']
                    self.parent_key_names = self.cnf_db['parentKeyNames']
                    self.parent_key_field = \
                        self.cnf_db['parentKeyNames'][0]['parameterName']

    def listing_projection_exclusions(self) -> dict:
        """
        This method returns the projection dictionary for excluding fields
        from the listing resultset.

        Returns:
            dict: The projection dictionary for excluding fields.
            The dictionary keys are the field names and the values are 0.
            e.g. {'field_name': 0, 'field_name2': 0}
            e.g. {} (empty dictionary)
        """
        projection = {k: 0 for k in self.cnf_db.get(
            'projection_exclusion', []
        )}
        if DEBUG:
            log_debug('listing_projection_exclusions |' +
                      f' projection: {projection}')
        return projection

    def listing_disabled_columns_projection(self) -> dict:
        """
        This method returns the projection dictionary for fields
        that have no "listing": True in the listing configuration
        or the column is included in the projection_exclusion list.
        so they will be excluded from the database query result.

        Returns:
            dict: The projection dictionary for the listing resultset.
            The dictionary keys are the field names and the values are 0.
            e.g. {'field_name': 0, 'field_name2': 0}
            e.g. {} (empty dictionary)
        """
        projection = {
            k["name"]: 0 for k in self.cnf_db.get('fieldElements', [])
            if not k.get("listing", False) or
            k["name"] in self.cnf_db.get('projection_exclusion', [])
        }
        if DEBUG:
            log_debug('listing_disabled_columns_projection |' +
                      f' projection: {projection}')
        return projection

    def add_mandatory_filters(
        self,
        listing_filter: dict,
        combinator: str = None
    ) -> dict:
        """
        This method adds mandatory filters to the listing filter
        and returns the updated filter. Mandatory filters will be
        ALWAYS included as equality (==) filter with the $and
        combinator in each condition, whether it's a "like" or
        normal condition). E.g. 

        self.mandatory_filters:{'user_id': 'XXXX'}

        listing_filter BEFORE: {'meal_date': {'$lte': 946702800.0,
        '$gte': 946616400.0}, 'observations': {'$regex':
        '.*sancocho.*', '$options': 'si'}, 'user_id': 'XXXX'}

        mandatory_filter_to_add: [{'user_id': 'XXXX'}]

        listing_filter AFTER: {'$or': [{'$and': [{'user_id': 'XXXX'},
        {'meal_date': {'$lte': 946702800.0, '$gte': 946616400.0}}]},
        {'$and': [{'user_id': 'XXXX'}, {'observations':
        {'$regex': '.*sanncocho.*', '$options': 'si'}}]}]}

        Args:
            listing_filter (dict): The original listing filter.
            combinator (str): The condition combinator for the filter.
            Defaults to "$and".

        Returns:
            dict: The updated listing filter with mandatory filters added.
        """
        if not combinator:
            combinator = "$and"
        if DEBUG:
            log_debug("add_mandatory_filters | self.mandatory_filters:" +
                      f"{self.mandatory_filters}")
            log_debug("add_mandatory_filters | listing_filter BEFORE:" +
                      f" {listing_filter}")
        if self.mandatory_filters.keys() != listing_filter.keys():
            # Mandatory filters will be ALWAYS included as
            # equality (==) filter with the $and combinator
            # in each "like" condition
            mandatory_filter_to_add = [
                {k: v} for k, v in self.mandatory_filters.items()
            ]
            # Filter multiple "like" conditions with the
            # specified combinator "$and" or "$or"
            if len(listing_filter) == 0 and len(mandatory_filter_to_add) == 0:
                listing_filter = {}
            elif len(listing_filter) == 0:
                listing_filter = {
                    "$and": [
                        {k: v} for k, v in self.mandatory_filters.items()
                    ]
                }
            else:
                listing_filter = {
                    combinator: [
                        {k: v} if len(mandatory_filter_to_add) == 0
                        else {'$and': list(mandatory_filter_to_add + [{k: v}])}
                        for k, v in listing_filter.items()
                        if k not in self.mandatory_filters
                    ]
                }
            if DEBUG:
                log_debug("add_mandatory_filters | mandatory_filter_to_add:" +
                          f" {mandatory_filter_to_add}")
        if DEBUG:
            log_debug("add_mandatory_filters | listing_filter AFTER:" +
                      f" {listing_filter}")
        return listing_filter

    def fetch_list(
        self,
        skip: int,
        limit: int,
        like_query_params: Optional[dict] = None,
        combinator: Optional[str] = None,
        order_param: str = None,
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
        if not like_query_params:
            like_query_params = {}
        if not combinator:
            combinator = '$and'
        resultset = get_default_resultset()

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
            log_debug(f"FETCH_LIST | resultset: {resultset}")
        return resultset

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
        if not projection:
            projection = {}
        resultset = get_default_resultset()

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

        return resultset

    def fetch_row_raw(self, row_id: str, projection: dict = None) -> dict:
        """
        Fetches a row from the database based on the given row_id
        and returns it without applying dumps() to the 'resultset'
        element.

        Args:
            row_id (str): The ID of the row to fetch.
            projection (dict, optional): The projection to apply to the
            fetched row.

        Returns:
            dict: The resultset containing the fetched row.
        """
        resultset = get_default_resultset()
        if not projection:
            projection = {}

        try:
            str_id = ObjectId(row_id)
        except ValueError:
            resultset['error_message'] = \
                f'Id `{row_id}` is invalid [FUR1].'
        except BaseException as err:
            resultset['error_message'] = \
                get_standard_base_exception_msg(err, 'FUR2')
            # raise

        if resultset['error_message']:
            resultset['error'] = True
            return resultset

        try:
            resultset['resultset'] = self.table_obj.find_one(
                {'_id': str_id}, projection
            )
        except BaseException as err:
            resultset['error_message'] = \
                get_standard_base_exception_msg(err, 'FUR3')
            resultset['error'] = True

        return resultset

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
        if DEBUG:
            log_debug("fetch_row_by_entryname_raw: " +
                      f"entry_name: {entry_name}" +
                      f" | entry_value: {entry_value}" +
                      f" | resultset: {resultset}")
        return resultset

    def passwords_encryption_on_update(
        self,
        record: dict,
        updated_record: dict,
        password_fields: list,
    ) -> dict:
        """
        Encrypts password fields in the updated record based on the original
        record.

        Args:
            record (dict): The original record containing the unencrypted
            password fields.
            updated_record (dict): The updated record where the password
            fields will be encrypted.
            password_fields (list): The list of password fields to be
            encrypted.

        Returns:
            dict: The resultset containing the updated record with encrypted
            password fields.
        """
        psw_class = Passwords()
        if DEBUG:
            log_debug('BEGIN passwords_encryption_on_update | ' +
                      f'password_fields: {password_fields} | ' +
                      f'record: {record}')
        resultset = get_default_resultset()
        existing_row = None
        for field in password_fields:
            if field in record and record[field]:
                updated_record[field] = psw_class.encrypt_password(
                    record[field]
                )
            else:
                if existing_row is None:
                    existing_row = self.fetch_row_raw(
                        record['_id'], {field: 1}
                    )
                    if existing_row['error']:
                        resultset['error_message'] = \
                            existing_row['error_message']
                        resultset['error'] = True
                        return resultset
                updated_record[field] = \
                    existing_row['resultset'][field]
        resultset['updated_record'] = updated_record
        if DEBUG:
            log_debug('END passwords_encryption_on_update | ' +
                      f'resultset: {resultset}')
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
        if DEBUG:
            log_debug(f'>>>---> Create {self.table_name} | ' +
                      f'pk_name: {pk_name} | pk_value: {str(pk_value)}')
        if pk_name == '_id' and pk_value:
            pk_value = ObjectId(pk_value)
        # Verify if the item already exists
        db_row = self.fetch_row_by_entryname_raw(pk_name, pk_value, filters)
        if db_row['resultset']:
            if DEBUG:
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

        return resultset

    def get_mandatory_fields(self, record: dict,
                             is_create: bool = False) -> list:
        """
        Returns the list of mandatory fields names existing in the
        given record, based on the required condition in the
        fieldElements and mandatory_fields configurations.

        Args:
            record (dict): record which mandatory fields are to be determined.
            is_create: bool, optional
                Indicates if the undergoing action is creation.
                Default is False.
                This condition is needed to handle the "_id" element:
                if "_id" is required and ...
                "_id" is in record and is creation or
                "_id" is not in record and is not creation
                then "_id" will be included as mandatory field.

        Returns:
            list
                A list of mandatory fields for the record.
        """
        mandatory_fields = ['creation_date', 'update_date']
        mandatory_fields.extend(self.cnf_db.get('mandatory_fields', []))
        for element in self.cnf_db['fieldElements']:
            element_name = element['name']
            if not element.get('required', False):
                continue
            if element.get('required', False) \
               and element.get('type', "") == "_id":
                if "_id" in record and not is_create:
                    continue
                if "_id" not in record and is_create:
                    continue
            if element_name not in mandatory_fields:
                mandatory_fields.append(element_name)
        return mandatory_fields

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
        options = {} if options is None else options
        if self.cnf_db.get('updateItem'):
            options["update_item"] = self.cnf_db.get('updateItem')
        mandatory_fields = self.get_mandatory_fields(record)
        updated_record = dict(record)
        updated_record['update_date'] = current_datetime_timestamp()

        if DEBUG:
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

        if DEBUG:
            log_debug(f'>>>---> PERFORM Update {self.table_name}' +
                      f' | ID: {record["_id"]}')

        try:
            if options.get("update_item", "0") == "0":
                op_result = self.table_obj.replace_one(
                    {'_id': ObjectId(record['_id'])},
                    updated_record
                ).modified_count
            else:
                op_result = self.table_obj.update_one(
                    {'_id': ObjectId(record['_id'])},
                    {'$set': updated_record}
                ).modified_count
            resultset['resultset']['rows_affected'] = str(op_result)
        except BaseException as err:
            resultset['error_message'] = \
                get_standard_base_exception_msg(err, 'UU2')
            resultset['error'] = True

        if DEBUG:
            log_debug(f'>>>---> Update {self.table_name} | ' +
                      f'updated_record (after): {updated_record}')

        return resultset

    def delete_row(self, remove_id: str) -> dict:
        """
        Deletes a existing row in the database.

        Args:
            remove_id (str): id of the row to be deleted.

        Returns:
            dict: The resultset containing the number of affected rows.
        """
        resultset = get_default_resultset()

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
        except BaseException as err:
            resultset['error_message'] = \
                get_standard_base_exception_msg(err, 'DU2')
            resultset['error'] = True

        return resultset

    # ----- array row operations. Example: food_times

    def get_parent_keys_from_url(self) -> dict:
        """
        Get parent key values from the url's query parameters

        Returns:
            dict: The parent key values from the URL parameters.
        """
        parent_id_values = {
            v["parentElementName"]:
                self.query_params.get(v['parameterName'])
            for v in self.parent_key_names
            if self.query_params.get(v['parameterName'])
        }
        return parent_id_values

    def get_parent_key_fieldnames(self) -> list:
        """
        Get parent key names from the columns configuration.

        Returns:
            list: The parent key field names.
        """
        return [v['parameterName'] for v in self.parent_key_names]

    def get_parent_keys(self, data: dict) -> dict:
        """
        Get parent key values from given row.

        Args:
            data (dict): row with the column's values.

        Returns:
            dict: The parent key values from the row.
        """
        parent_keys = {
            v["parentElementName"]:
                data[v['parameterName']]
            for v in self.parent_key_names
        }
        if "id" in parent_keys:
            # {'_id': ObjectId(data[self.parent_key_field])}
            parent_keys["_id"] = ObjectId(parent_keys["id"])
            del parent_keys["id"]
        return parent_keys

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
        if not like_query_params:
            like_query_params = {}
        if not combinator:
            combinator = '$and'
        resultset = get_default_resultset()
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
            if DEBUG:
                log_debug('')
                log_debug(f'fetch_array_rows | lf: {lf}')
                log_debug(f'fetch_array_rows | all_filters: {all_filters}')
                log_debug('')
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
        return resultset

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
        if DEBUG:
            log_debug('')
            log_debug('add_array_item_to_row - data')
            log_debug(data)
            log_debug('')
        resultset = get_default_resultset()
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
        except BaseException as err:
            resultset['error_message'] = \
                get_standard_base_exception_msg(err, 'AFTTU1')
            resultset['error'] = True
        return resultset

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
        if DEBUG:
            log_debug('')
            log_debug('remove_array_item_from_row - data')
            log_debug(data)
            log_debug('')
        array_field_in_json = self.array_field
        if f'{array_field_in_json}_old' in data:
            # This is for older entry deletion,
            # when the key field has been changed
            array_field_in_json = f'{array_field_in_json}_old'
        if DEBUG:
            log_debug('')
            log_debug(f'$pull from "{self.array_field}", ' +
                      f'array_field_key={self.array_field_key}')
            log_debug(f'array_field_in_json={array_field_in_json}, ' +
                      'key value to REMOVE=' +
                      f'{data[array_field_in_json][self.array_field_key]}')
            log_debug('')
        resultset = get_default_resultset()
        pull_element = {
            self.array_field: {
                self.array_field_key:
                    data[array_field_in_json][self.array_field_key]
            }
        }
        if DEBUG:
            log_debug(f'pull_element={pull_element}')

        parent_keys = self.get_parent_keys(data)

        if DEBUG:
            log_debug(f'parent_keys: {parent_keys}')
            log_debug('')
        try:
            resultset['resultset']['rows_affected'] = str(
                self.table_obj.update_one(
                    parent_keys,
                    {'$pull': pull_element}
                ).modified_count
            )
        except BaseException as err:
            resultset['error_message'] = \
                get_standard_base_exception_msg(err, 'RFTTU')
            resultset['error'] = True
        return resultset

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
        if DEBUG:
            log_debug('')
            log_debug('get_array_item_in_row - array_item_id:' +
                      f' {str(array_item_id)}' +
                      f' | parent_keys: {str(parent_keys)}')
        find_criteria = dict(parent_keys)
        find_criteria.update({
            self.array_field: {
                '$elemMatch': {
                    self.array_field_key: array_item_id
                }
            },
        })
        if DEBUG:
            log_debug('self.table_obj | find_criteria:')
            log_debug(find_criteria)
            log_debug('')
        resultset = get_default_resultset()
        try:
            resultset['resultset']['rows_count'] = str(
                self.table_obj.count_documents(find_criteria)
            )
        except BaseException as err:
            resultset['error_message'] = \
                get_standard_base_exception_msg(err, 'GFMIU-010')
            resultset['error'] = True
        if DEBUG:
            log_debug(f">>--> get_array_item_in_row | resultset: {resultset}")
        return resultset

    def get_current_user(self) -> str:
        """
        Get the current user Id from the Request

        Returns:
            str: the current user Id from the JWT Request
        """
        return self.request.user["public_id"]

    def replace_special_vars(self, params: dict) -> dict:
        """
        Returns the params record replacing special value tokens.
        E.g. {CurrentUserId} will be replaced with the current user Id.

        Args:
            params (dict): record (item data) to be processed.
                E.g. {'name': 'John', 'age': '30', 'gender': 'male'}
                or {'name': 'John', 'age': '30', 'gender': '{CurrentUserId}'}
        Returns:
            dict: record (item data) replacing special value tokens.
        """
        response = {
            k: self.get_current_user() if v == "{CurrentUserId}" else v
            for k, v in params.items()
        }
        # if DEBUG:
        #     log_debug("replace_special_vars | params:" +
        #               f" {params} | response: {response}")
        return response

    def get_field_element(self, fieldname: str) -> dict:
        """
        Get one column configuration from 'fieldElements'

        Args:
            fieldname (str): field name.

        Returns:
            dict: field (attribute) definition or an empty dict
                if the field is not found.
        """
        # if DEBUG:
        #     log_debug(f">>> get_field_element | fieldname: {fieldname}" +
        #               f" | fieldElements: {self.cnf_db.get('fieldElements')}"
        #               )
        field_element = [v for v in self.cnf_db.get('fieldElements', [])
                         if v.get('name') == fieldname]
        # Returns an empty dict if the field is not found
        # to handle eventual invalid fieldnames passed in the endpoint call.
        return field_element[0] if field_element else {}

    def is_datefield(self, fieldname: str) -> bool:
        """
        Determine if a column is a date.

        Args:
            fieldname (str): field name.

        Returns:
            bool: True if the column is a date, False otherwise.
        """
        return self.get_field_element(fieldname).get('type') \
            in ['date', 'datetime-local']

    def uuid_generator_check(self, data: dict, key_fieldname: str,
                             array_field: str) -> dict:
        """
        Checks if the key_fieldname has a "uuid_generator" attribute
        in the fieldElements configuration. If it does, and the
        key_fieldname is not present in the data[array_field] or
        if it is present but empty, it generates a UUID4 and assigns
        it to data[array_field][key_fieldname].

        IMPORTANT: data[array_field] must have only ONE the item,
        the one that ID (key_fieldname) will be assigned.

        Args:
            data (dict): The JSON data to be checked and updated.
            key_fieldname (str): The field name to be checked for
            UUID generation.
            array_field (str): The field name of the array to be checked
            and updated.

        Returns:
            dict: The updated JSON data with UUID4 assigned if necessary.
        """
        field_element = self.get_field_element(key_fieldname)
        if 'uuid_generator' not in field_element:
            return data
        if ((key_fieldname not in data[array_field] or
             (key_fieldname in data[array_field] and
              not data[array_field][key_fieldname]))):
            data[array_field][key_fieldname] = str(uuid4())
        return data

    def get_sort_config(self, order_param: str = None) -> (str, str):
        """
        Returns the column name and direction for sorting based on the
        query parameter "order" or default configuration
        "primaryKeyName", if not, assumes "_id".

        Returns:
            (str, str): Tuple with the column name and direction for sorting.
        """
        if order_param:
            order_str = order_param
        elif self.query_params.get('order'):
            order_str = self.query_params.get('order')
        else:
            order_str = self.cnf_db.get(
                'defaultOrder',
                self.cnf_db.get('primaryKeyName', "_id")
            )
        if "|" not in order_str:
            order_str += "|asc"
        [column_name, direction] = order_str.split("|")

        if DEBUG:
            log_debug("")
            log_debug(f">> GET_SORT_CONFIG | column_name: {column_name}," +
                      f" direction: {direction}")
            log_debug("")

        return column_name, direction
