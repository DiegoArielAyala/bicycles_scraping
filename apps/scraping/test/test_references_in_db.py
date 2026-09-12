from bs4 import BeautifulSoup
from rest_framework.test import APITestCase

from apps.scraping.models import Bicycle
from apps.scraping.services.bicycles_services import create_bicycles

class TestReferencesInDB(APITestCase):
    def setUp(self):
        html = '''
        <li>
            <img data-src="https://cdn.test/11111_foto.jpg" />
            <span class="price">1000</span>
        </li>    
        '''
        self.web = "biking_point"
        self.bicycle_references_in_db = {"11111", "22222"}
        self.product_elements_html = BeautifulSoup(html, "html.parser").find_all("li")

        bicycles_in_db = []
        bicycles_in_db.append(Bicycle(reference="11111", current_price=1000, web=self.web))
        bicycles_in_db.append(Bicycle(reference="22222", current_price=2000, web=self.web))
        Bicycle.objects.bulk_create(bicycles_in_db)
    
    def test_retuns_only_bicycle_references_not_found_in_scraping(self):
        bicycle_references_in_db = create_bicycles(self.product_elements_html, self.web, self.bicycle_references_in_db)
        self.assertEqual(len(bicycle_references_in_db), 1)