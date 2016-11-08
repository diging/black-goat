import unittest, mock, types

from goat.authorities import AuthorityManager

with open('goat/tests/authorities/conceptpower.json') as f:
    configuration = f.read()


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
        mock_get.return_value = """
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
            """
        expected_endpoint = 'http://chps.asu.edu/conceptpower/rest/Concept'
        manager = AuthorityManager(configuration)
        func = manager._generic('get')

        result = func(id=1)
        self.assertEqual(mock_get.call_count, 1)
        self.assertEqual(mock_get.call_args[0][0], expected_endpoint)
        self.assertIsInstance(result, dict)
        self.assertIn('type', result)
        self.assertIn('name', result)
        self.assertIn('description', result)

    def test_generic_nonsense(self):
        manager = AuthorityManager(configuration)
        with self.assertRaises(NotImplementedError):
            manager._generic('nonsense')
