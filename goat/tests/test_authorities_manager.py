import unittest, mock, types

from goat.authorities import AuthorityManager, ConceptSearchResult

with open('goat/tests/authorities/conceptpower.json') as f:
    configuration = f.read()

with open('goat/tests/authorities/viaf.json') as f:
    viaf_configuration = f.read()


class TestAuthorityManager(unittest.TestCase):
    def test_init(self):
        try:
            manager = AuthorityManager(configuration)
        except:
            self.fail('cannot initialize AuthorityManager')

        self.assertIn('get', manager.methods)
        self.assertIsInstance(manager.configuration, dict)

    def test_get_globs(self):
        manager = AuthorityManager(configuration)
        self.assertIsInstance(manager._get_globs(), dict)

    def test_get_method_config(self):
        manager = AuthorityManager(configuration)
        self.assertIsInstance(manager._get_method_config('get'), dict)

    def test_get_nsmap(self):
        manager = AuthorityManager(configuration)
        nsmap = manager._get_nsmap(manager._get_method_config('get'))
        self.assertIsInstance(nsmap, dict)
        self.assertIn('digitalHPS', nsmap)

    def test_generic(self):
        manager = AuthorityManager(configuration)
        func = manager._generic('get')
        self.assertIsInstance(func, types.FunctionType)

    @mock.patch('requests.get')
    def test_generic_get(self, mock_get):
        class MockResponse(object):
            def __init__(self, content):
                self.content = content
                self.status_code = 200

        mock_get.return_value = MockResponse("""
            <conceptpowerReply xmlns:digitalHPS="http://www.digitalhps.org/">
                <digitalHPS:conceptEntry>
                   <digitalHPS:id
                      concept_id="CON273fb179-b256-4401-b094-614a5e215692"
                      concept_uri="http://www.digitalhps.org/concepts/CON273fb179-b256-4401-b094-614a5e215692">
                          http://www.digitalhps.org/concepts/CON273fb179-b256-4401-b094-614a5e215692
                   </digitalHPS:id>
                   <digitalHPS:lemma>
                       Adolf Ziegler
                   </digitalHPS:lemma>
                   <digitalHPS:pos>
                       NOUN
                   </digitalHPS:pos>
                   <digitalHPS:description>
                       German embryo modeler in late 19th century
                   </digitalHPS:description>
                   <digitalHPS:conceptList>
                       Persons
                   </digitalHPS:conceptList>
                   <digitalHPS:creator_id>mueller</digitalHPS:creator_id>
                   <digitalHPS:equal_to>http://viaf.org/viaf/38882290</digitalHPS:equal_to>
                   <digitalHPS:modified_by/>
                   <digitalHPS:similar_to/>
                   <digitalHPS:synonym_ids/>
                   <digitalHPS:type
                             type_id="986a7cc9-c0c1-4720-b344-853f08c136ab"
                             type_uri="http://www.digitalhps.org/types/TYPE_986a7cc9-c0c1-4720-b344-853f08c136ab">
                       E21 Person
                   </digitalHPS:type>
                   <digitalHPS:deleted>false</digitalHPS:deleted>
                   <digitalHPS:wordnet_id/>
                </digitalHPS:conceptEntry>
            </conceptpowerReply>
            """)
        expected_endpoint = 'https://chps.asu.edu/conceptpower/rest/Concept'
        manager = AuthorityManager(configuration)
        func = manager._generic('get')

        result = func(id=1)
        self.assertEqual(mock_get.call_count, 1)
        self.assertEqual(mock_get.call_args[0][0], expected_endpoint)

        self.assertIn('concept_type', result)
        self.assertIn('name', result)
        self.assertIn('description', result)

    @mock.patch('requests.get')
    def test_generic_search(self, mock_get):
        class MockResponse(object):
            def __init__(self, content):
                self.content = content
                self.status_code = 200

        with open('goat/tests/mock_responses/cp_search.xml', 'r') as f:
            mock_get.return_value = MockResponse(f.read())
        path = 'https://chps.asu.edu/conceptpower/rest/ConceptSearch'
        manager = AuthorityManager(configuration)
        func = manager._generic('search')

        results = func(q='test')
        self.assertEqual(mock_get.call_count, 1)
        self.assertEqual(mock_get.call_args[0][0], path)
        self.assertEqual(len(results), 5)
        for result in results:
            self.assertIn('concept_type', result)
            self.assertIn('name', result)
            self.assertIn('description', result)

    @mock.patch('requests.get')
    def test_search(self, mock_get):
        class MockResponse(object):
            def __init__(self, content):
                self.content = content
                self.status_code = 200

        with open('goat/tests/mock_responses/cp_search.xml', 'r') as f:
            mock_get.return_value = MockResponse(f.read())
        path = 'https://chps.asu.edu/conceptpower/rest/ConceptLookup/test/noun'
        manager = AuthorityManager(configuration)
        results = manager.search({'q': 'test'})

        self.assertEqual(len(results), 5)
        for result in results:
            self.assertIsInstance(result, ConceptSearchResult)

    def test_generic_nonsense(self):
        manager = AuthorityManager(configuration)
        with self.assertRaises(NotImplementedError):
            manager._generic('nonsense')



class TestAuthorityManagerVIAF(unittest.TestCase):
    def test_init(self):
        try:
            manager = AuthorityManager(viaf_configuration)
        except:
            self.fail('cannot initialize AuthorityManager')

        self.assertIn('get', manager.methods)
        self.assertIsInstance(manager.configuration, dict)

    def test_get_globs(self):
        manager = AuthorityManager(viaf_configuration)
        self.assertIsInstance(manager._get_globs(), dict)

    def test_get_method_config(self):
        manager = AuthorityManager(viaf_configuration)
        self.assertIsInstance(manager._get_method_config('get'), dict)

    def test_get_nsmap(self):
        manager = AuthorityManager(viaf_configuration)
        nsmap = manager._get_nsmap(manager._get_method_config('get'))
        self.assertIsInstance(nsmap, dict)
        self.assertIn('viaf', nsmap)

    def test_generic(self):
        manager = AuthorityManager(viaf_configuration)
        func = manager._generic('get')
        self.assertIsInstance(func, types.FunctionType)

    @mock.patch('requests.get')
    def test_generic_get(self, mock_get):
        class MockResponse(object):
            def __init__(self, content):
                self.content = content
                self.status_code = 200

        with open('goat/tests/mock_responses/viaf_get.xml', 'rb') as f:
            mock_get.return_value = MockResponse(f.read())
        expected_endpoint = 'http://viaf.org/viaf/1/viaf.xml'
        manager = AuthorityManager(viaf_configuration)
        func = manager._generic('get')

        result = func(local_id=1)
        self.assertEqual(mock_get.call_count, 1)
        self.assertEqual(mock_get.call_args[0][0], expected_endpoint)

        self.assertIn('concept_type', result)
        self.assertIn('name', result)

    @mock.patch('requests.get')
    def test_generic_search(self, mock_get):
        class MockResponse(object):
            def __init__(self, content):
                self.content = content
                self.status_code = 200

        with open('goat/tests/mock_responses/viaf_search.json', 'r') as f:
            mock_get.return_value = MockResponse(f.read())
        path = "http://viaf.org/viaf/AutoSuggest"
        manager = AuthorityManager(viaf_configuration)
        func = manager._generic('search')

        results = func(q='test')
        self.assertEqual(mock_get.call_count, 1)
        self.assertEqual(mock_get.call_args[0][0], path)
        self.assertEqual(len(results), 10)

        for result in results:
            self.assertIn('concept_type', result)
            self.assertIn('name', result)
            self.assertIn('description', result)

    @mock.patch('requests.get')
    def test_search(self, mock_get):
        class MockResponse(object):
            def __init__(self, content):
                self.content = content
                self.status_code = 200

        with open('goat/tests/mock_responses/viaf_search.json', 'r') as f:
            mock_get.return_value = MockResponse(f.read())

        path = "http://viaf.org/viaf/AutoSuggest"
        manager = AuthorityManager(viaf_configuration)
        results = manager.search({'q': 'test'})

        self.assertEqual(len(results), 10)
        for result in results:
            self.assertIsInstance(result, ConceptSearchResult)

    def test_generic_nonsense(self):
        manager = AuthorityManager(viaf_configuration)
        with self.assertRaises(NotImplementedError):
            manager._generic('nonsense')
