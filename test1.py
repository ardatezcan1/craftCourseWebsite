import unittest
from app import app, conn

class FlaskTestCase(unittest.TestCase):
    def setUp(self):
        # Set the app to testing mode
        app.config['TESTING'] = True
        self.client = app.test_client()

    def tearDown(self):
        # Roll back database transactions or close connections if opened
        pass

    def login(self, username, password):
        # Helper method to perform login during tests.
        return self.client.post('/login', data=dict(username=username, password=password), follow_redirects=True)

    def test_add_user_as_personnel(self):
    # Tests that personnel can add a new user, or handle the case where the username already exists.
        self.login('personnel1', 'personnelpass1')
        response = self.client.post('/add_user', data=dict(
            username='student6', 
            password='studentpass6', 
            address='853 Elm St, City, Country', 
            phone='3334445556', 
            homePhone='887654321', 
            email='student6@example.com', 
            role='S'), 
            follow_redirects=True)

        # Check if the response data contains either the success message or the username exists message.
        response_data = response.get_data(as_text=True)
        success_message = 'New user added successfully.'
        exists_message = 'Username already exists. Please use a different username.'
        self.assertTrue(success_message in response_data or exists_message in response_data, "Either the user should be added successfully, or the username exists message should be displayed.")

    def test_filter_courses_by_price_as_personnel(self):
    # Log in as personnel
        self.login('personnel1', 'personnelpass1')

        # Setup the maximum price to filter courses
        max_price = 220.00

        # Make a POST request with the max price
        response = self.client.post('/filter_courses', data={'max_price': max_price}, follow_redirects=True)
        response_data = response.get_data(as_text=True)

        # Verify no courses listed above the max price (simplified, pseudo-code-ish check)
        self.assertNotIn('$225.00', response_data, "No courses should be listed above the specified maximum price.")
        self.assertNotIn('$300.00', response_data, "No courses should be listed above the specified maximum price.")
        self.assertIn('$150.00', response_data, "Courses should be listed below the specified maximum price.")
        self.assertIn('$205.00', response_data, "Courses should be listed below the specified maximum price.")

    def test_add_course_as_teacher(self):
        # Verifies that a teacher can successfully add a course.
        self.login('teacher3', 'teacherpass3')
        response = self.client.post('/add_course', data=dict(course_name='Test_Course', course_details='Details', price=100, course_date='2024-07-08'), follow_redirects=True)
        #If everything fine, the course should be visiable after it added
        self.assertIn('Test_Course', response.get_data(as_text=True))

if __name__ == '__main__':
    unittest.main()