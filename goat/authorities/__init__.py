from django.conf import settings

from goat.authorities.util import *

import json


class ConceptSearchResult(object):
    def __init__(self, name='', identifier='', **extra):
        assert isinstance(name, unicode)
        assert isinstance(identifier, unicode)
        self.name = name
        self.identifier = identifier
        self.extra = extra

    @property
    def identities(self):
        return self.extra.get('identities', None)

    @property
    def description(self):
        return self.extra.get('description', None)

    @property
    def concept_type(self):
        return self.extra.get('concept_type', None)



class AuthorityManager(object):
    """
    Configuration-driven manager for authority services.

    Parameters
    ----------
    config : str
        Name of an authority configuration in ``authorities``. Will look for
        ``{path}/{config}.json``.
    path : str
        Location of configurations.

    """

    def __init__(self, configuration):
        self.configuration = json.loads(configuration)
        self.methods = {method.pop('name'):method for method
                        in self.configuration.get("methods")}

    def _get_globs(self):
        return {'endpoint': self.configuration.get('endpoint', '')}

    def _get_nsmap(self, config):
        return {
            ns['prefix']: ns['namespace']
            for ns in config.get('response', {}).get('namespaces', [])
        }

    def _get_method_config(self, name):
        if name not in self.methods:
            raise NotImplementedError('%s not defined in configuration' % name)
        return self.methods.get(name)

    def _generic(self, name):
        """
        Build a method using the configuration identified by ``name``.

        Parameters
        ----------
        name : str
            Must be the name of a method defined in the configuration.

        Returns
        -------
        function
        """
        config = self._get_method_config(name)
        response_type = config.get('type', 'xml')
        if response_type != 'xml':
            raise NotImplementedError('No parser for %s' % config.get('type'))

        request_func = generate_request(config, self._get_globs())

        def _call(*args, **kwargs):
            return parse_result(config.get('response'),
                                parse_raw_xml(request_func(*args, **kwargs)),
                                parse_xml_path,
                                self._get_globs(),
                                self._get_nsmap(config))
        return _call

    def __getattr__(self, name):
        if name in self.methods:
            return self._generic(name)
        return super(AuthorityManager, self).__getattr__(name)

    def get(self, identifier):
        """
        Get a concept record from the configured authority.

        Parameters
        ----------
        identifier : str
            Used to populate the ``id`` parameter in the request.

        Returns
        -------
        dict
        """
        return self._generic('get')(id=identifier)

    def search(self, params):
        """
        Search for concept records in the configured authority.

        Parameters
        ----------
        params : kwargs
            Query parameters used to populate the search request.

        Returns
        -------
        list
        """
        return [ConceptSearchResult(**o) for o in self._generic('search')(**params)]
