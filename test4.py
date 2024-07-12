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

    def test_register_for_course_as_student(self):
        # Tests that a student can register for a course.
        self.login('student3', 'studentpass3')
        response = self.client.post('/student_dashboard', data=dict(course_id=2, payment_method='cash'), follow_redirects=True)
        self.assertIn('You have successfully registered for the course.', response.get_data(as_text=True))
    
    def test_teacher_cannot_register_for_course(self):
    # Tests that a teacher cannot register for a course.
        self.login('teacher1', 'teacherpass1')  # Log in as a teacher
    # Attempt to register for a course, which should not be permitted for teachers
        response = self.client.post('/student_dashboard', data=dict(course_id=1, payment_method='cash'), follow_redirects=True)
        self.assertNotIn('You have successfully registered for the course.', response.get_data(as_text=True))
        self.assertIn('login', response.get_data(as_text=True), "Teacher should not be able to register for courses")

if __name__ == '__main__':
    unittest.main()