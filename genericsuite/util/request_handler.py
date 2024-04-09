""" Class to save the current request object """


class RequestHandler:
    """ Class to save the current request object """

    def __init__(self):
        self.request = None

    def set_request(self, request):
        """ Set the request object """
        self.request = request

    def get_request(self):
        """ Get the request object """
        return self.request

# Usage:


# Create a single instance of RequestHandler to be used throughout a module
# request_handler = RequestHandler()


# def set_local_request(request):
#     request_handler.set_request(request)
