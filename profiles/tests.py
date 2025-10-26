from django.test import TestCase
from django.urls import reverse

class DiscoverPageTest(TestCase):
    def test_discover_page_status_code(self):
        response = self.client.get(reverse('profiles:discover'))
        self.assertEqual(response.status_code, 200)