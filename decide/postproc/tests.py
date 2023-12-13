

from rest_framework.test import APIClient
from rest_framework.test import APITestCase

from base import mods


class PostProcTestCase(APITestCase):

    def setUp(self):
        self.client = APIClient()
        mods.mock_query(self.client)

    def tearDown(self):
        self.client = None

    def test_identity(self):
        data = {
            'method': 'IDENTITY',
            'options': [
                { 'option': 'Option 1', 'number': 1, 'votes': 5 },
                { 'option': 'Option 2', 'number': 2, 'votes': 0 },
                { 'option': 'Option 3', 'number': 3, 'votes': 3 },
                { 'option': 'Option 4', 'number': 4, 'votes': 2 },
                { 'option': 'Option 5', 'number': 5, 'votes': 5 },
                { 'option': 'Option 6', 'number': 6, 'votes': 1 },
            ]
        }

        expected_result = [
            { 'option': 'Option 1', 'number': 1, 'votes': 5, 'postproc': 5 },
            { 'option': 'Option 5', 'number': 5, 'votes': 5, 'postproc': 5 },
            { 'option': 'Option 3', 'number': 3, 'votes': 3, 'postproc': 3 },
            { 'option': 'Option 4', 'number': 4, 'votes': 2, 'postproc': 2 },
            { 'option': 'Option 6', 'number': 6, 'votes': 1, 'postproc': 1 },
            { 'option': 'Option 2', 'number': 2, 'votes': 0, 'postproc': 0 },
        ]

        response = self.client.post('/postproc/', data, format='json')
        self.assertEqual(response.status_code, 200)

        values = response.json()
        self.assertEqual(values, expected_result)

    def test_dhondt(self):
        data = {
            'method': 'DHONDT',
            'seats': 20,
            'options': [
                { 'option': 'Option 1', 'number': 1, 'votes': 0, 'deputies': 0},
                { 'option': 'Option 2', 'number': 2, 'votes': 1, 'deputies': 0},
            ]
        }

        expected_result = [
            { 'option': 'Option 2', 'number': 2, 'votes': 1, 'deputies': 20 },
            { 'option': 'Option 1', 'number': 1, 'votes': 0, 'deputies': 0 },
        ]

        response = self.client.post('/postproc/', data, format='json')
        self.assertEqual(response.status_code, 200)

        values = response.json()
        self.assertEqual(values, expected_result)

    def test2_dhondt(self):
        data = {
            'method': 'DHONDT',
            'seats': 150,
            'options': [
                { 'option': 'Option 1', 'number': 1, 'votes': 2000, 'deputies': 0},
                { 'option': 'Option 2', 'number': 2, 'votes': 1200, 'deputies': 0},
                { 'option': 'Option 6', 'number': 6, 'votes': 700, 'deputies': 0},
                { 'option': 'Option 3', 'number': 3, 'votes': 450, 'deputies': 0},
                { 'option': 'Option 4', 'number': 4, 'votes': 350, 'deputies': 0},
                { 'option': 'Option 5', 'number': 5, 'votes': 300, 'deputies': 0},
            ]
        }

        expected_result = [
            { 'option': 'Option 1', 'number': 1, 'votes': 2000, 'deputies': 61},
            { 'option': 'Option 2', 'number': 2, 'votes': 1200, 'deputies': 36},
            { 'option': 'Option 6', 'number': 6, 'votes': 700, 'deputies': 21},
            { 'option': 'Option 3', 'number': 3, 'votes': 450, 'deputies': 13},
            { 'option': 'Option 4', 'number': 4, 'votes': 350, 'deputies': 10},
            { 'option': 'Option 5', 'number': 5, 'votes': 300, 'deputies': 9},
        ]

        response = self.client.post('/postproc/', data, format='json')
        self.assertEqual(response.status_code, 200)

        values = response.json()
        self.assertEqual(values, expected_result)

    def test_webster(self):
        data = {
            'method': 'WEBSTER',
            'seats': 20,
            'options': [
                { 'option': 'Option 1', 'number': 1, 'votes': 0, 'deputies': 0},
                { 'option': 'Option 2', 'number': 2, 'votes': 1, 'deputies': 0},
            ]
        }

        expected_result = [
            { 'option': 'Option 2', 'number': 2, 'votes': 1, 'deputies': 20 },
            { 'option': 'Option 1', 'number': 1, 'votes': 0, 'deputies': 0 },
        ]

        response = self.client.post('/postproc/', data, format='json')
        self.assertEqual(response.status_code, 200)

        values = response.json()
        self.assertEqual(values, expected_result)

    def test2_webster(self):
        data = {
            'method': 'WEBSTER',
            'seats': 150,
            'options': [
                { 'option': 'Option 1', 'number': 1, 'votes': 2000, 'deputies': 0},
                { 'option': 'Option 2', 'number': 2, 'votes': 1200, 'deputies': 0},
                { 'option': 'Option 6', 'number': 6, 'votes': 700, 'deputies': 0},
                { 'option': 'Option 3', 'number': 3, 'votes': 450, 'deputies': 0},
                { 'option': 'Option 4', 'number': 4, 'votes': 350, 'deputies': 0},
                { 'option': 'Option 5', 'number': 5, 'votes': 300, 'deputies': 0},
            ]
        }

        expected_result = [
            { 'option': 'Option 1', 'number': 1, 'votes': 2000, 'deputies': 60},
            { 'option': 'Option 2', 'number': 2, 'votes': 1200, 'deputies': 36},
            { 'option': 'Option 6', 'number': 6, 'votes': 700, 'deputies': 21},
            { 'option': 'Option 3', 'number': 3, 'votes': 450, 'deputies': 13},
            { 'option': 'Option 4', 'number': 4, 'votes': 350, 'deputies': 11},
            { 'option': 'Option 5', 'number': 5, 'votes': 300, 'deputies': 9},
        ]

        response = self.client.post('/postproc/', data, format='json')
        self.assertEqual(response.status_code, 200)

        values = response.json()
        self.assertEqual(values, expected_result)