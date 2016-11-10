"""
Helper functions for parsing authority descriptions.
"""

import re, requests
import lxml.etree as ET


def is_multiple(tag):
    """
    Detect the multi-value flag (``*``) in a path part (``tag``).

    Parameters
    ----------
    tag : str

    Returns
    -------
    tuple
        tag name (str), multiple (bool)
    """
    return re.match(ur'([^\*]+)(\*)?', tag).groups()


def get_recursive_pathfinder(nsmap={}):
    """
    Generate a recursive function that follows the path in ``tags``, starting
    at ``elem``.
    """

    def _get(elem, tags):
        """
        Parameters
        ----------
        elem : :class:`lxml.etree.Element`
        tags : list
        """
        if not tags:    # Bottomed out; recursion stops.
            return elem

        this_tag, multiple = is_multiple(tags.pop())
        base = _get(elem, tags)
        if type(base) is list:
            _apply = lambda b, t, meth: [getattr(c, meth)(t, nsmap) for c in b]
        else:
            _apply = lambda b, t, meth: getattr(b, meth)(t, nsmap)
        if multiple:
            return _apply(base, this_tag, 'findall')
        return _apply(base, this_tag, 'find')
    return _get


def content_picker_factory(env):
    """
    Generates a function that retrives the CDATA content or attribute value of
    an :class:`lxml.etree.Element`\.

    Parameters
    ----------
    env : dict

    Returns
    -------
    function
    """
    attribute, sep = env.get('attribute', False), env.get('sep', None)
    _separator = lambda value: [v.strip() for v in value.split(sep)] if sep else value
    if attribute:
        _picker = lambda e: _separator(getattr(e, 'attrib', {}).get(attribute[1:-1], u'').strip().decode('utf-8'))
    else:
        _picker = lambda e: _separator(getattr(getattr(e, 'text', u''), 'strip', lambda: u'')().decode('utf-8'))
    return _picker


def passthrough_picker_factory(env):
    """
    Generates a function that simply returns a passed
    :class:`lxml.etree.Element`\.

    Parameters
    ----------
    env : dict

    Returns
    -------
    function
    """
    return lambda e: e


def decompose_path(path_string):
    """
    Split a path string into its constituent parts.

    Parameters
    ----------
    path_string : str

    Returns
    -------
    path : list
    attribute : str or None
    """
    if '|' in path_string:
        try:
            path_string, sep = path_string.split('|')
        except ValueError:
            raise ValueError("Malformed path: only one separator reference"
                             " (|) allowed.")
    else:
        sep = None

    path, attribute = re.match(ur'([^\[]+)(\[.+\])?', path_string).groups()
    if '[' in path and not attribute:
        raise ValueError("Malformed path: attribute references must come at"
                         " the very end of the path.")

    path = path.split('/')
    return path, attribute, sep


def parse_xml_path(path_string, nsmap={}, picker_factory=content_picker_factory):
    """
    Generate a function that will retrieve data of interest from an
    :class:`lxml.etree.Element`\.

    Parameters
    ----------
    path_string : str
        See docs for how this should be written. TODO: write the docs.
    nsmap: dict
        See the ``lxml.etree`` docs.
    picker_factory : function


    Returns
    -------
    function
    """

    path, attribute, sep = decompose_path(path_string)

    # Path can be arbitrarily deep, so we use recursion here to chain .find()
    #  calls from the root element to the deepest child.
    _get = get_recursive_pathfinder(nsmap=nsmap)

    # Decide how to obtain the final value of interest.
    _picker = picker_factory(locals())

    def _apply(obj):    # No empty values.
        value = _picker(obj)
        if value and (not type(value) is list or value[0]):
            return value

    def _call(elem):
        base = _get(elem, path)
        if type(base) is list:
            return [_apply(child) for child in base]
        return _apply(base)
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

    format_keys = re.findall(ur'\{([^\}]+)\}', path_partial)
    fmt = {k: v for k, v in glob.iteritems() if k in format_keys}

    def _get_path(extra={}):
        fmt.update(extra)
        return path_partial.format(**fmt)

    def _call(**params):
        """
        Perform the configured request.

        Parameters
        ----------
        params : kwargs

        Returns
        -------

        """
        headers = params.pop('headers', {})
        for param in required:
            if param not in params:
                raise TypeError('expected parameter %s' % param)

        params = {parameters.get(k):v for k, v in params.iteritems()
                  if k in parameters}

        extra = {key: params.pop(key, '') for key in format_keys
                 if key not in fmt}    # Don't overwrite.

        if method == 'GET':
            request_method = requests.get
            payload = {'params': params, 'headers': headers}
        elif method == 'POST':
            request_method = requests.post
            payload = {'data': params, 'headers': headers}
        return request_method(_get_path(extra), **payload).content
    return _call


def parse_result(config, data, path_parser=parse_xml_path, glob={}, nsmap={}):
    """
    Extract data from an :class:`lxml.etree.Element` using a configuration
    schema.

    Parameters
    ----------
    config : dict
    data : :class:`lxml.etree.Element`
    path_parser : function
    glob : dict
    nsmap : dict

    Returns
    -------
    list
    """
    base_path = config.get('path', None)
    _, multiple = is_multiple(base_path)
    if base_path:
        _parser = parse_xml_path(base_path, nsmap=nsmap,
                                 picker_factory=passthrough_picker_factory)
        base_elems = _parser(data)
    else:
        base_elems = [data]

    data = []
    base_elems = [base_elems] if not type(base_elems) is list else base_elems
    for base_elem in base_elems:
        parsed_data = {}
        for parameter in config.get('parameters'):
            func = path_parser(parameter.get('path'), nsmap)
            parsed_data[parameter.get('name')] = func(base_elem)
        data.append(parsed_data)
    if not multiple:
        assert len(data) == 1
        return data[0]
    return data


# This isn't particularly special at the moment, but makes it easier to swap
#  out parsers later, or add additional logic.
def parse_raw_xml(raw):
    """
    Parse raw XML response content.

    Parameters
    ----------
    raw : unicode

    Returns
    -------
    :class:`lxml.etree.Element`
    """
    if type(raw) is str:
        raw = raw.decode('utf-8')
    return ET.fromstring(raw)
