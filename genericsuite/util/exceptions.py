# from chalice.app import (
#     UnauthorizedError,
#     BadRequestError,
#     ChaliceViewError,
#     ForbiddenError,
# )


# class GoAwayError(ChaliceViewError):
#     STATUS_CODE = 410


# class OverrideErrMsgMixin(Exception):

#     def __init__(self, msg: str = ''):  # noqa
#         self.msg = msg


# class QueryNotFound(GoAwayError, OverrideErrMsgMixin):
#     """Not found"""


# class QueryForbidden(ForbiddenError, OverrideErrMsgMixin):
#     """Query that field ss not allowed"""


# class QueryUnauthorized(UnauthorizedError, OverrideErrMsgMixin):
#     """Not authenticated """


# class QueryError(BadRequestError, OverrideErrMsgMixin):
#     """Generic Query Validation Failure"""


# class InternalError(ChaliceViewError, OverrideErrMsgMixin):
#     """Generic internal server error"""
