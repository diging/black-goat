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
    def local_identifier(self):
        return self.extra.get('local_identifier', None)

    @property
    def identities(self):
        return self.extra.get('identities', None)

    @property
    def description(self):
        return self.extra.get('description', None)

    @property
    def concept_type(self):
        return self.extra.get('concept_type', None)

    @property
    def raw(self):
        return self.extra.get('raw', None)


def _get_method_params(cfg):
    return [prm.get('accept') for prm
            in cfg.get('response', {}).get('parameters', {})]


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
        response_type = config.get('response', {}).get('type', 'xml').lower()

        if response_type not in ['xml', 'json']:
            raise NotImplementedError('No parser for %s' % response_type)

        if response_type == 'xml':
            parse_raw = parse_raw_xml
            parse_path = parse_xml_path
        elif response_type == 'json':
            parse_raw = parse_raw_json
            parse_path = parse_json_path

        request_func = generate_request(config, self._get_globs())

        def _call(*args, **kwargs):
            return parse_result(config.get('response'),
                                parse_raw(request_func(*args, **kwargs)),
                                parse_path,
                                self._get_globs(),
                                self._get_nsmap(config))
        _call.parameters = _get_method_params(config)
        return _call

    def __getattr__(self, name):
        if name in self.methods:
            return self._generic(name)
        return super(AuthorityManager, self).__getattr__(name)

    def accepts(self, method, *params):
        config = self._get_method_config(method)
        accepted = {p.get('accept', '') for p in config.get('parameters', [])}
        return all([param in accepted for param in params])

    def get(self, identifier=None, local_identifier=None):
        """
        Get a concept record from the configured authority.

        Although both ``identifier`` and ``local_identifier`` are declared as
        optional, it is a good idea to pass them both and let the configuration
        sort things out.

        Parameters
        ----------
        identifier : str
            Used to populate the ``id`` parameter in the request.
        local_identifier : str
            Used to populate the ``local_id`` parameter in the request.

        Returns
        -------
        dict
        """
        _call = self._generic('get')
        if identifier and 'id' in _call.parameters:
            return _call(id=identifier)
        elif local_identifier and 'local_id' in _call.parameters:
            return _call(local_id=local_identifier)

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
