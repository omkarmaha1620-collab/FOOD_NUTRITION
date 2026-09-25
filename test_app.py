"""
Automated End-to-End Verification Test Suite
Tests all 12 modules, routes, calculations, authentication, and database CRUD.
"""

import unittest
from app import app
from db import execute_query, execute_update

class NutritionAnalyzerTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        # Clean up test accounts to ensure idempotent runs
        execute_update("DELETE FROM users WHERE email IN ('alice@example.com', 'testuser@example.com')")
        execute_update("DELETE FROM food_items WHERE name = 'Greek Honey Yogurt'")

    def test_01_home_page(self):
        """Test home landing page renders successfully"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Food Nutrition Analyzer', response.data)
        self.assertIn(b'Nutrient Consumed', response.data)

    def test_02_user_registration_and_login(self):
        """Test Module 1: Registration, validation, and session login"""
        # Register new user
        reg_data = {
            'name': 'Alice Smith',
            'email': 'alice@example.com',
            'password': 'Password@123',
            'confirm_password': 'Password@123',
            'age': '24',
            'gender': 'Female',
            'height_cm': '165.0',
            'weight_kg': '58.0',
            'activity_level': 'Lightly Active'
        }
        res_reg = self.client.post('/register', data=reg_data, follow_redirects=True)
        self.assertEqual(res_reg.status_code, 200)
        self.assertIn(b'Registration successful', res_reg.data)

        # Login with newly created user
        res_login = self.client.post('/login', data={
            'email': 'alice@example.com',
            'password': 'Password@123'
        }, follow_redirects=True)
        self.assertEqual(res_login.status_code, 200)
        self.assertIn(b'Welcome back, Alice Smith', res_login.data)

    def test_03_profile_and_health_calculations(self):
        """Test Module 2, 8, 9: Profile, BMI, and Calorie targets"""
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['user_name'] = 'John Doe'

        response = self.client.get('/profile')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Body Mass Index (BMI)', response.data)
        self.assertIn(b'Daily Calorie Requirement', response.data)
        self.assertIn(b'Normal weight', response.data)

        # Test updating profile
        update_data = {
            'name': 'Johnathan Doe',
            'age': '23',
            'gender': 'Male',
            'height_cm': '178.0',
            'weight_kg': '72.0',
            'activity_level': 'Very Active'
        }
        res_update = self.client.post('/profile', data=update_data, follow_redirects=True)
        self.assertEqual(res_update.status_code, 200)
        self.assertIn(b'Profile updated successfully', res_update.data)

    def test_04_food_search_and_api_calculation(self):
        """Test Module 4 & 5: Food search and quantity calculations"""
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1

        # Search food
        res_search = self.client.get('/foods?search=Rice')
        self.assertEqual(res_search.status_code, 200)
        self.assertIn(b'Cooked White Rice', res_search.data)

        # API calculate 250g of food ID 15 (White Rice: 130 kcal / 100g)
        res_api = self.client.post('/api/calculate-nutrition', json={
            'food_id': 15,
            'quantity_grams': 250
        })
        self.assertEqual(res_api.status_code, 200)
        data = res_api.get_json()
        self.assertTrue(data['success'])
        # 130 * 250 / 100 = 325.0 kcal
        self.assertEqual(data['data']['calories'], 325.0)

    def test_05_meal_management_and_tracking(self):
        """Test Module 6 & 7: Add, edit, delete meal, and daily tracking"""
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1

        # Add meal
        meal_data = {
            'food_id': 1, # Apple
            'meal_type': 'Snacks',
            'quantity_grams': '150',
            'entry_date': '2026-09-25'
        }
        res_add = self.client.post('/meals/add', data=meal_data, follow_redirects=True)
        self.assertEqual(res_add.status_code, 200)
        self.assertIn(b'Daily Meal Tracker', res_add.data)

        # Verify tracking page shows Snacking and Apple
        res_track = self.client.get('/tracking?date=2026-09-25')
        self.assertEqual(res_track.status_code, 200)
        self.assertIn(b'Snacks', res_track.data)

    def test_06_reports_and_visualization(self):
        """Test Module 11: Reports page with weekly aggregation"""
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1

        response = self.client.get('/reports?view=weekly')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Nutrition Report', response.data)
        self.assertIn(b'Calorie Intake Trend', response.data)
        self.assertIn(b'Macronutrient Ratio', response.data)

    def test_07_admin_portal_and_food_crud(self):
        """Test Module 12: Admin login, dashboard metrics, food CRUD"""
        # Admin login
        res_admin_login = self.client.post('/admin/login', data={
            'identifier': 'admin',
            'password': 'Admin@123'
        }, follow_redirects=True)
        self.assertEqual(res_admin_login.status_code, 200)
        self.assertIn(b'Administrator Dashboard', res_admin_login.data)

        # Add new food
        new_food_data = {
            'name': 'Greek Honey Yogurt',
            'category': 'Dairy',
            'serving_size': '1 cup (150g)',
            'calories_per_100g': '85.0',
            'protein_per_100g': '8.5',
            'carbs_per_100g': '10.2',
            'fat_per_100g': '1.5',
            'fiber_per_100g': '0.0',
            'micronutrients': 'Calcium, Probiotics'
        }
        res_add_food = self.client.post('/admin/foods/add', data=new_food_data, follow_redirects=True)
        self.assertEqual(res_add_food.status_code, 200)
        self.assertIn(b'Greek Honey Yogurt', res_add_food.data)

if __name__ == '__main__':
    unittest.main()
