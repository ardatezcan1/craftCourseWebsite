import unittest
from app import app, conn

class FlaskTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()

    def tearDown(self):
        pass

    def login(self, username, password):
        return self.client.post('/login', data=dict(username=username, password=password), follow_redirects=True)

    def test_no_access_without_login(self):
        # Test that all relevant pages redirect to login if not logged in
        protected_urls = ['/teacher_dashboard', '/personal_dashboard', '/student_dashboard','/add_course', '/teacher_profile',
                            '/my_courses', '/my_profile', '/personal_dashboard', '/personnel_profile', '/view_user_details', '/filter_courses']
        for url in protected_urls:
            response = self.client.get(url, follow_redirects=True)
            self.assertIn('Login', response.get_data(as_text=True), f"Accessing {url} without login should redirect to login page")

    def test_role_based_access_control(self):
        # First, log in with a specific role
        self.login('student1', 'studentpass1')
        # Attempt to access a page not allowed for this role
        response = self.client.get('/teacher_dashboard', follow_redirects=True)
        self.assertNotIn('Your Courses', response.get_data(as_text=True))
        self.assertIn('Unauthorized', response.get_data(as_text=True))


if __name__ == '__main__':
    unittest.main()
