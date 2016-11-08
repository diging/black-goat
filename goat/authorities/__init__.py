from goat.authorities.util import *

import json


class AuthorityManager(object):
    """
    Manager for configuration-based authority methods.

    Parameters
    ----------
    config : str
        Name of an authority configuration in ``authorities``. Will look for
        ``authorities/{config}.json``.
    """
    def __init__(self, config):
        with open('authorities/%s.json' % config) as f:
            self.configuration = json.load(f)

        self.methods = {method.pop('name'):method for method
                        in self.configuration.get("methods")}

    def get(self, identifier):
        """
        """
        if 'get' not in methods:
            raise NotImplementedError('Get method defined in configuration')
        request_func = generate_request(methods.get('get'))

    def search(self, params):
        """
        """
        if 'search' not in methods:
            raise NotImplementedError('Search method defined in configuration')
        request_func = generate_request(methods.get('search'))
