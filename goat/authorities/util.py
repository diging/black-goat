"""
Helper functions for parsing authority descriptions.
"""

import re, requests
import lxml.etree as ET


def parse_xml_path(path_string, nsmap={}):
    """
    Generate a callable object that will retrieve data of interest from an
    :class:`lxml.etree.Element`\.

    Parameters
    ----------
    path_string : str
        See docs for how this should be written. TODO: write the docs.
    nsmap: dict
        See the ``lxml.etree`` docs.

    Returns
    -------
    function
    """

    path, attribute = re.match('([^\[]+)(\[.+\])?', path_string).groups()
    if '[' in path and not attribute:
        raise ValueError("Malformed path: attribute references must come at"
                         " the very end of the path.")

    path = path.split('/')

    # Path can be arbitrarily deep, so we use recursion here to chain .find()
    #  calls from the root element to the deepest child.
    def _get(elem, tags):
        if not tags:    # Bottomed out; recursion stops.
            return elem
        this_tag, multiple = re.match('([^\*]+)(\*)?', tags.pop()).groups()
        base = _get(elem, tags)
        if type(base) is list:
            _apply = lambda b, t, meth: [getattr(c, meth)(t, nsmap) for c in b]
        else:
            _apply = lambda b, t, meth: getattr(b, meth)(t, nsmap)
        if multiple:
            return _apply(base, this_tag, 'findall')
        return _apply(base, this_tag, 'find')

    # Decide how to obtain the final value of interest.
    if attribute:
        _data = lambda e: e.attrib.get(attribute[1:-1], None).strip()
    else:
        _data = lambda e: e.text.strip()

    def _call(elem):
        base = _get(elem, path)
        if type(base) is list:
            return [_data(child) for child in base]
        return _data(base)
    return _call


def generate_request(config, glob={}):
    """
    Generate a function that performs an HTTP request based on the configuration
    in ``config``.

    Parameters
    ----------
    config : dict
    glob : dict

    Returns
    -------
    function
        Expects keyword arguments defined in the configuration. If provided,
        ``headers`` will be pulled out and passed as headers in the request.
    """
    try:
        path_partial = config.get('path')
    except KeyError:
        raise ValueError("Malformed configuration: no path specified.")
    method = config.get("method", "GET")    # GET by default.
    parameters = {param['accept']: param['send']
                  for param in config.get("parameters", [])}
    required = {param['accept'] for param in config.get("parameters", [])
                if param.get('required', False)}

    format_keys = re.findall('\{([^\}]+)\}', path_partial)
    fmt = {k: v for k, v in glob.iteritems() if k in format_keys}
    full_path = path_partial.format(**fmt)

    def _call(**params):
        """
        Perform the configured request.

        Parameters
        ----------
        params : kwargs
        """
        headers = params.pop('headers', {})
        for param in required:
            if param not in params:
                raise TypeError('expected parameter %s' % param)

        params = {parameters.get(k):v for k, v in params.iteritems()
                  if k in parameters}
        if method == 'GET':
            return requests.get(full_path, params=params, headers=headers)
        elif method == 'POST':
            return requests.post(full_path, data=params, headers=headers)
    return _call


def parse_result(config, data, path_parser=parse_xml_path, glob={}, nsmap={}):
    base_path = config.get('path', None)
    parsed_data = {}
    for parameter in config.get('parameters'):
        path = parameter.get('path')
        if base_path:
            path = '/'.join([base_path, path])
        func = path_parser(path, nsmap)
        parsed_data[parameter.get('name')] = func(data)
    return parsed_data


def parse_raw_xml(raw):
    return ET.fromstring(raw)
