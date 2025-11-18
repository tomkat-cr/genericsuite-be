from genericsuite.util.framework_abs_layer import get_current_framework
from genericsuite.util.generic_db_helpers_super import GenericDbHelperSuper
from genericsuite.util.utilities import (
    get_query_params,
    get_request_body,
)


class GenericDbHelperWithRequest(GenericDbHelperSuper):
    """
    Generic Database Helper with request class
    """

    def __init__(self, json_file, request=None, blueprint=None, db_type=None
                 ) -> None:

        self.blueprint = blueprint
        self.request = request
        if self.blueprint and not self.request:
            self.request = self.blueprint.get_current_request()

        self.query_params = get_query_params(self.request) \
            if self.request else {}

        self.request_body = get_request_body(self.request) \
            if self.request else {}

        super().__init__(json_file, db_type)

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
        if specific_func_name and self.blueprint:
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
