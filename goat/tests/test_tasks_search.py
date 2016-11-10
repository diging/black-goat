import unittest, mock, types

from goat import tasks
from goat.models import *
from django.contrib.auth.models import User

with open('goat/tests/authorities/conceptpower.json') as f:
    configuration = f.read()


class TestTaskSearch(unittest.TestCase):
    def setUp(self):
        self.user = User.objects.create(username='testUser')
        self.authority = Authority.objects.create(
            name="testAuthority",
            added_by=self.user,
            configuration=configuration,
            namespace='http://www.digitalhps.org/'
        )
        self.viaf = Authority.objects.create(
            name='VIAF',
            added_by=self.user,
            namespace='http://viaf.org/viaf/'
        )

    @mock.patch('requests.get')
    def test_search(self, mock_get):
        class MockResponse(object):
            def __init__(self, content):
                self.content = content

        with open('goat/tests/mock_responses/cp_search.xml', 'r') as f:
            mock_get.return_value = MockResponse(f.read())
        path = 'http://chps.asu.edu/conceptpower/rest/ConceptLookup/test/noun'
        query = {'q': 'test'}
        results, _ = tasks.search(self.user, self.authority, query, None)

        self.assertEqual(len(results), 5)
        for result in results:
            self.assertIsInstance(result, Concept)

        identities = Identity.objects.all()
        self.assertEqual(identities.count(), 1)
        


    def tearDown(self):
        for model in [User, Concept, Authority, Identity, IdentitySystem,
                      SearchResultSet]:
            model.objects.all().delete()
