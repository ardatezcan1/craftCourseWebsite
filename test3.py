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

    def test_view_user_details_as_personnel(self):
        # Tests that personnel can view details of specific users.
        self.login('personnel1', 'personnelpass1')

        # Make a GET request to view the initial form/page
        response = self.client.get('/view_user_details', follow_redirects=True)
        self.assertIn('View User Details', response.get_data(as_text=True), "Personnel should be able to access the view user details page")

        response = self.client.post('/view_user_details', data={'user_id': 1}, follow_redirects=True)
        self.assertIn('User Details', response.get_data(as_text=True), "Personnel should be able to view specific user details")
        # Check for specifics in the user information or courses, depending on what is expected to be rendered
        self.assertIn('teacher1', response.get_data(as_text=True), "Details about the user's courses should be visible if applicable")

    def test_student_view_own_profile(self):
        self.login('student3', 'studentpass3')
        
        # Simulate accessing the my_profile page
        response = self.client.get('/my_profile', follow_redirects=True)
        
        # Check for successful page access and the presence of expected user information
        self.assertIn('My Profile', response.get_data(as_text=True), "The My Profile page should load successfully.")
        
        # Assuming the test database has specific known values for this student
        self.assertIn('student3@example.com', response.get_data(as_text=True), "The student's email should be displayed on the profile page.")
        self.assertIn('987 Walnut St', response.get_data(as_text=True), "The student's address should be displayed on the profile page.")

if __name__ == '__main__':
    unittest.main()