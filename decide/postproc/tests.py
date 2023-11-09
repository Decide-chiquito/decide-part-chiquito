from django.test import TestCase

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
            'type': 'IDENTITY',
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
            'type': 'DHONDT',
            'seats': 20,
            'options': [
                { 'option': 'Option 1', 'number': 1, 'votes': 0, 'dhondt': 0},
                { 'option': 'Option 2', 'number': 2, 'votes': 1, 'dhondt': 0},
            ]
        }

        expected_result = [
            { 'option': 'Option 2', 'number': 2, 'votes': 1, 'dhondt': 20 },
            { 'option': 'Option 1', 'number': 1, 'votes': 0, 'dhondt': 0 },
        ]

        response = self.client.post('/postproc/', data, format='json')
        self.assertEqual(response.status_code, 200)

        values = response.json()
        self.assertEqual(values, expected_result)

    def test2_dhondt(self):
        data = {
            'type': 'DHONDT',
            'seats': 150,
            'options': [
                { 'option': 'Option 1', 'number': 1, 'votes': 2000, 'dhondt': 0},
                { 'option': 'Option 2', 'number': 2, 'votes': 1200, 'dhondt': 0},
                { 'option': 'Option 6', 'number': 6, 'votes': 700, 'dhondt': 0},
                { 'option': 'Option 3', 'number': 3, 'votes': 450, 'dhondt': 0},
                { 'option': 'Option 4', 'number': 4, 'votes': 350, 'dhondt': 0},
                { 'option': 'Option 5', 'number': 5, 'votes': 300, 'dhondt': 0},
            ]
        }

        expected_result = [
            { 'option': 'Option 1', 'number': 1, 'votes': 2000, 'dhondt': 61},
            { 'option': 'Option 2', 'number': 2, 'votes': 1200, 'dhondt': 36},
            { 'option': 'Option 6', 'number': 6, 'votes': 700, 'dhondt': 21},
            { 'option': 'Option 3', 'number': 3, 'votes': 450, 'dhondt': 13},
            { 'option': 'Option 4', 'number': 4, 'votes': 350, 'dhondt': 10},
            { 'option': 'Option 5', 'number': 5, 'votes': 300, 'dhondt': 9},
        ]

        response = self.client.post('/postproc/', data, format='json')
        self.assertEqual(response.status_code, 200)

        values = response.json()
        self.assertEqual(values, expected_result)

    def test_webster(self):
        data = {
            'type': 'WEBSTER',
            'seats': 20,
            'options': [
                { 'option': 'Option 1', 'number': 1, 'votes': 0, 'webster': 0},
                { 'option': 'Option 2', 'number': 2, 'votes': 1, 'webster': 0},
            ]
        }

        expected_result = [
            { 'option': 'Option 2', 'number': 2, 'votes': 1, 'webster': 20 },
            { 'option': 'Option 1', 'number': 1, 'votes': 0, 'webster': 0 },
        ]

        response = self.client.post('/postproc/', data, format='json')
        self.assertEqual(response.status_code, 200)

        values = response.json()
        self.assertEqual(values, expected_result)

    def test2_webster(self):
        data = {
            'type': 'WEBSTER',
            'seats': 150,
            'options': [
                { 'option': 'Option 1', 'number': 1, 'votes': 2000, 'webster': 0},
                { 'option': 'Option 2', 'number': 2, 'votes': 1200, 'webster': 0},
                { 'option': 'Option 6', 'number': 6, 'votes': 700, 'webster': 0},
                { 'option': 'Option 3', 'number': 3, 'votes': 450, 'webster': 0},
                { 'option': 'Option 4', 'number': 4, 'votes': 350, 'webster': 0},
                { 'option': 'Option 5', 'number': 5, 'votes': 300, 'webster': 0},
            ]
        }

        expected_result = [
            { 'option': 'Option 1', 'number': 1, 'votes': 2000, 'webster': 60},
            { 'option': 'Option 2', 'number': 2, 'votes': 1200, 'webster': 36},
            { 'option': 'Option 6', 'number': 6, 'votes': 700, 'webster': 21},
            { 'option': 'Option 3', 'number': 3, 'votes': 450, 'webster': 13},
            { 'option': 'Option 4', 'number': 4, 'votes': 350, 'webster': 11},
            { 'option': 'Option 5', 'number': 5, 'votes': 300, 'webster': 9},
        ]

        response = self.client.post('/postproc/', data, format='json')
        self.assertEqual(response.status_code, 200)

        values = response.json()
        self.assertEqual(values, expected_result)