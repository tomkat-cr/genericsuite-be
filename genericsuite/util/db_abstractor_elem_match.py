from genericsuite.util.app_logger import log_debug

DEBUG = False


class DbAbstractorElemMatch:
    """
    Database abstract class for $elemMatch support for cases where the database
    does not support $elemMatch natively or cannot be mimicked by a SQL query
    (e.g. Supabase) or where the performance is not optimal.
    """

    def _extract_elem_match(self, query_params: dict) -> tuple:
        """
        Extract $elemMatch conditions from query_params.

        Args:
            query_params: The original query parameters

        Returns:
            Tuple of (cleaned_query_params, elem_match_conditions)
        """
        if not query_params:
            return query_params, {}

        elem_match_conditions = {}
        cleaned_params = {}

        for key, value in query_params.items():
            if isinstance(value, dict) and "$elemMatch" in value:
                elem_match_conditions[key] = value["$elemMatch"]
            else:
                cleaned_params[key] = value

        _ = DEBUG and log_debug(
            f"_extract_elem_match | cleaned_params: {cleaned_params}"
            f" | elem_match_conditions: {elem_match_conditions}")

        return cleaned_params, elem_match_conditions

    def _filter_elem_match(self, items, elem_match_conditions):
        """
        Filter items based on $elemMatch conditions.

        Args:
            items: List of items, single item dict, or empty dict to filter
            elem_match_conditions: Dict mapping field_name to match conditions

        Returns:
            Filtered items (same type as input)
        """
        if not elem_match_conditions:
            return items

        is_single = isinstance(items, dict)
        if is_single and not items:
            return items

        items_list = [items] if is_single else items
        if not items_list:
            return items

        filtered_items = []
        for item in items_list:
            matches = True
            for field_name, match_conditions in elem_match_conditions.items():
                if field_name not in item:
                    matches = False
                    break

                array_field = item[field_name]
                if not isinstance(array_field, list):
                    matches = False
                    break

                found_match = False
                for element in array_field:
                    if isinstance(element, dict):
                        element_matches = all(
                            # TO TEST THE OPPOSITE LOGIC:
                            # element[k] != v
                            element.get(k) == v
                            for k, v in match_conditions.items()
                        )
                        if element_matches:
                            found_match = True
                            break
                    elif element == match_conditions:
                        found_match = True
                        break

                if not found_match:
                    matches = False
                    break

            if matches:
                filtered_items.append(item)

        _ = DEBUG and log_debug(
            f"_filter_elem_match | input count: {len(items_list)}"
            f" | output count: {len(filtered_items)}")

        if is_single:
            return filtered_items[0] if filtered_items else {}
        return filtered_items
