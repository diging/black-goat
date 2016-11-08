from goat.authorities.util import *

import unittest, mock, json
import lxml.etree as ET


class TestGenerateRequest(unittest.TestCase):
    """
    :meth:`goat.authorities.util.generate_request` should return a callable
    that will dispatch a request with provided parameters and/or headers.
    """

    @mock.patch('requests.get')
    def test_get(self, mock_get):
        """
        By default, will generate a callable that performs a GET request using
        the configured parameters.
        """
        config = {
            "path": "{endpoint}/Concept",
            "parameters": [
                {
                    "accept": "id",
                    "send": "sendid",
                    "required": True,
                },
            ]
        }
        glob = {"endpoint": "http://chps.asu.edu/conceptpower/rest",}
        func = generate_request(config, glob=glob)
        result = func(id="testID")

        expected_endpoint = 'http://chps.asu.edu/conceptpower/rest/Concept'
        args, kwargs = mock_get.call_args

        self.assertEqual(mock_get.call_count, 1)
        self.assertEqual(args[0], expected_endpoint)
        self.assertIn('sendid', kwargs['params'])
        self.assertIn('headers', kwargs)

    @mock.patch('requests.post')
    def test_post(self, mock_post):
        """
        If a POST request, will call ``requests.post`` with ``data``.
        """
        config = {
            "method": "POST",
            "path": "{endpoint}/Concept",
            "parameters": [
                {
                    "accept": "id",
                    "send": "sendid",
                    "required": True,
                },
            ]
        }
        glob = {"endpoint": "http://chps.asu.edu/conceptpower/rest",}
        func = generate_request(config, glob=glob)
        result = func(id="testID")

        expected_endpoint = 'http://chps.asu.edu/conceptpower/rest/Concept'
        args, kwargs = mock_post.call_args

        self.assertEqual(mock_post.call_count, 1)
        self.assertEqual(args[0], expected_endpoint)
        self.assertIn('data', kwargs)
        self.assertIn('sendid', kwargs['data'])
        self.assertIn('headers', kwargs)

    @mock.patch('requests.get')
    def test_get_required(self, mock_get):
        """
        If a paramter is required, a TypeError will be raised if the callable
        does not receive it.
        """
        config = {
            "path": "{endpoint}/Concept",
            "parameters": [
                {
                    "accept": "id",
                    "send": "id",
                    "required": True,
                },
            ]
        }
        glob = {"endpoint": "http://chps.asu.edu/conceptpower/rest",}
        func = generate_request(config, glob=glob)
        with self.assertRaises(TypeError):
            result = func()

    @mock.patch('requests.get')
    def test_get_not_required(self, mock_get):
        """
        If a paramter is not required (default), no error will be raised if the
        function does not receive it.
        """
        config = {
            "path": "{endpoint}/Concept",
            "parameters": [
                {
                    "accept": "id",
                    "send": "id",
                },
            ]
        }
        glob = {"endpoint": "http://chps.asu.edu/conceptpower/rest",}
        func = generate_request(config, glob=glob)
        try:
            result = func()
        except TypeError:
            self.fail()


class TestParseXMLPath(unittest.TestCase):
    def test_no_namespace_no_attrib(self):
        """
        The default behavior of :meth:`goat.authorities.util.parse_xml_path`
        is to return a callable that, when passed an :class:`ET.Element`\,
        finds the element with specified name and returns its value (presumably
        CDATA).
        """
        root = ET.Element('root')
        field = ET.Element('afieldname')
        field.text = 'avalue'
        root.append(field)
        path = "afieldname"

        self.assertEqual(parse_xml_path(path)(root), field.text)

    def test_no_namespace_no_attrib_multiple(self):
        """

        """
        root = ET.Element('root')
        field = ET.Element('afieldname')
        field.text = 'avalue'
        field2 = ET.Element('afieldname')
        field2.text = 'asecondvalue'
        root.append(field)
        root.append(field2)
        path = "afieldname*"

        result = parse_xml_path(path)(root)

        self.assertEqual(result[0], field.text)
        self.assertEqual(result[1], field2.text)

    def test_no_namespace_no_attrib_multiple_levels(self):
        """
        The path can have several levels, separated by '/' characters.
        """
        root = ET.Element('root')
        parent = ET.Element('parent')
        field = ET.Element('afieldname')
        field.text = 'avalue'
        parent.append(field)
        root.append(parent)
        path = "parent/afieldname"

        self.assertEqual(parse_xml_path(path)(root), field.text)

    def test_no_namespace_no_attrib_multiple_levels_multivalue(self):
        """
        Iteration can happen at any level of the path.
        """
        root = ET.Element('root')
        parent = ET.Element('parent')
        parent2 = ET.Element('parent')
        field = ET.Element('afieldname')
        field.text = 'avalue'
        field2 = ET.Element('afieldname')
        field2.text = 'asecondvalue'
        parent.append(field)
        parent2.append(field2)
        root.append(parent)
        root.append(parent2)
        path = "parent*/afieldname"

        result = parse_xml_path(path)(root)
        self.assertEqual(result[0], field.text)
        self.assertEqual(result[1], field2.text)

    def test_no_namespace_with_attribute(self):
        """
        If an attribute name is included in square brackets, will return the
        value of that attribute rather than the CDATA child of the matched
        element.
        """
        root = ET.Element('root')
        field = ET.Element('afieldname')
        field.text = 'avalue'
        field.attrib['test'] = 'foo'
        root.append(field)
        path = "afieldname[test]"
        self.assertEqual(parse_xml_path(path)(root), field.attrib['test'])

    def test_namespace_no_attrib(self):
        """
        Should be able to navigate namespaced paths.
        """
        NS = 'http://test.com/'
        nsmap = {'test': NS}
        root = ET.Element(ET.QName(NS, 'root'))

        field = ET.Element(ET.QName(NS, 'afieldname'))
        field.text = 'avalue'
        root.append(field)
        path = "test:afieldname"

        self.assertEqual(parse_xml_path(path, nsmap)(root), field.text)
