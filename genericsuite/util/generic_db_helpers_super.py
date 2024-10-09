"""
Generic Database Helper super class
"""
from uuid import uuid4

from bson.json_util import ObjectId

from genericsuite.util.framework_abs_layer import get_current_framework
from genericsuite.util.app_logger import log_debug, log_error
from genericsuite.util.config_dbdef_helpers import get_json_def_both
from genericsuite.util.utilities import (
    get_standard_base_exception_msg,
    get_default_resultset,
    get_query_params,
    get_request_body,
)
from genericsuite.util.db_abstractor import (
    # set_db_request,
    db,
)
from genericsuite.util.passwords import Passwords


DEBUG = False


class GenericDbHelperSuper:
    """
    Generic Database Helper super class
    """
    # def __init__(self, json_file, request=None, db_type=None) -> None:
    def __init__(self, json_file, request=None, blueprint=None, db_type=None
                 ) -> None:

        # set_db_request(request)

        self.error_message = None
        self.json_file = json_file
        self.cnf_db = get_json_def_both(json_file)

        # log_debug(f">>> self.cnf_db: {self.cnf_db}")

        self.blueprint = blueprint
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
                    log_debug("||| GenericDbHelper | self.table_obj:" +
                              f" {self.table_obj}")
            except BaseException as error:
                self.error_message = "ERROR connecting to Database:" + \
                                     f" {str(error)}"
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

    def get_current_user(self) -> str:
        """
        Get the current user Id from the Request

        Returns:
            str: the current user Id from the JWT Request
        """
        if get_current_framework() == 'chalice':
            return self.request.user["public_id"]
        else:
            return self.request.user.public_id

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

    def run_specific_func(self, action, resultset):
        """
        Runs the specific function for the given action.

        Args:
            action (str): The action to run the specific function for.
            resultset (dict): The resultset to be passed to the specific
            function.

        Returns:
            dict: The resultset returned by the specific function.
        """
        specific_func_name = self.cnf_db.get('specific_function', None)
        if specific_func_name:
            specific_func = self.blueprint.get_current_app().custom_data.get(
                specific_func_name
            )
            if not specific_func:
                raise Exception(f"Specific function {specific_func_name}" +
                                " not found.")
            action_data = {
                'action': action,
                'resultset': resultset,
                'cnf_db': self.cnf_db,
            }
            resultset = specific_func(self.blueprint, action_data)
        return resultset

    # ----- Normal row operations.

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

    # ----- Array row operations.

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
