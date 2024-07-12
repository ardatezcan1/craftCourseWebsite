from flask import Flask, render_template, request, redirect, url_for, session
import psycopg2
import psycopg2.extras
from psycopg2 import IntegrityError

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Database connection parameters
DB_HOST = "localhost"
DB_NAME = "yazilim_proje_main"
#DB_NAME = "test_software_proje"   ---Test DB Name
DB_USER = "postgres"
DB_PASS = "admin"

# Setup database connection
conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST)

@app.route('/')
def home():
    if 'username' not in session:
        return redirect(url_for('login'))  # Redirect to login if not logged in
    else:
        # Display a welcome message or dashboard depending on the role
        return 'Logged in as ' + session['username'] + ' with role ' + session['role']

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Fetch all relevant user data including the user ID
        cur.execute("SELECT id, username, password, role FROM users WHERE username=%s", (username,))
        user = cur.fetchone()
        cur.close()
        
        if user and user['password'] == password:
            session['user_id'] = user['id']  # Store the user ID in the session
            session['username'] = user['username']
            session['role'] = user['role']
            
            # Redirect to the specific dashboard based on the user's role
            if user['role'] == 'T':
                return redirect(url_for('teacher_dashboard'))
            elif user['role'] == 'S':
                return redirect(url_for('student_dashboard'))
            elif user['role'] == 'P':
                return redirect(url_for('personal_dashboard'))
            elif user['role'] == 'A':
                return redirect(url_for('admin_dashboard'))
            else:
                error = 'Role not recognized'
        else:
            error = 'Invalid username or password'
    
    return render_template('login.html', error=error)


@app.route('/teacher_dashboard')
def teacher_dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))  # Ensure the user is logged in
    if session['role'] != 'T':
        return 'Unauthorized access'  # Ensure the user is a teacher

    user_id = session['user_id']  # Use the user_id stored in session
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # Fetch courses that this teacher is responsible for
    cur.execute("SELECT * FROM TeacherCourses WHERE TeacherID = %s", (user_id,))
    courses = cur.fetchall()
    cur.close()
    
    return render_template('teacher_dashboard.html', courses=courses)

@app.route('/add_course', methods=['GET', 'POST'])
def add_course():
    if 'username' not in session or session['role'] != 'T':
        return redirect(url_for('login'))  # Redirect to login if not logged in or not a teacher

    if request.method == 'POST':
        # Retrieve form data
        course_name = request.form['course_name']
        course_details = request.form['course_details']
        price = request.form['price']
        course_date = request.form['course_date']

        # Insert course into the database
        cur = conn.cursor()
        cur.execute("INSERT INTO TeacherCourses (TeacherID, CourseName, CourseDetails, Price, CourseDate) VALUES (%s, %s, %s, %s, %s)",
                    (session['user_id'], course_name, course_details, price, course_date))
        conn.commit()
        cur.close()

        return redirect(url_for('teacher_dashboard'))  # Redirect back to the dashboard after adding

    # GET request: display the course addition form
    return render_template('add_course.html')

@app.route('/teacher_profile')
def teacher_profile():
    if 'username' not in session or session['role'] != 'T':
        return redirect(url_for('login'))  # Redirect if not logged in or not a teacher

    conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST)
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # Fetch the teacher's information
    cur.execute("""
        SELECT Username, Address, Phone, HomePhone, Email
        FROM Users
        WHERE ID = %s;
    """, (session['user_id'],))
    user_info = cur.fetchone()

    cur.close()
    conn.close()

    return render_template('teacher_profile.html', user_info=user_info)

@app.route('/student_dashboard', methods=['GET', 'POST'])
def student_dashboard():
    # Check if the user is logged in and is a student
    if 'username' not in session or session['role'] != 'S':
        return redirect(url_for('login'))  # Redirect if not logged in or not a student

    # Database connection setup
    conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST)
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # Fetch all available courses to display on the dashboard
    cur.execute("""
        SELECT Courses.CourseID, TeacherCourses.CourseName, TeacherCourses.CourseDetails, 
               Courses.CoursePrice, Courses.Date, Courses.Quota, Courses.Reservations, Users.Username AS TeacherName
        FROM Courses
        JOIN TeacherCourses ON Courses.TeacherCourseID = TeacherCourses.CourseID
        JOIN Teacher ON TeacherCourses.TeacherID = Teacher.UserID
        JOIN Users ON Teacher.UserID = Users.ID
        WHERE Courses.IsActive = True;
    """)
    courses = cur.fetchall()

    # Handle POST request for course registration
    if request.method == 'POST':
        course_id = request.form['course_id']
        payment_method = request.form['payment_method']

        # Attempt to register for a course
        try:
            cur.execute("""
                INSERT INTO StudentCourses (StudentID, CourseID, AttendanceDate, PurchaseDate, Price, PaymentMethod)
                SELECT %s, %s, Courses.Date, NOW(), CoursePrice, %s FROM Courses WHERE CourseID = %s AND NOT EXISTS (
                    SELECT 1 FROM StudentCourses WHERE StudentID = %s AND CourseID = %s
                );
            """, (session['user_id'], course_id, payment_method, course_id, session['user_id'], course_id))
            if cur.rowcount == 0:
                message = "You have already registered for this course or it does not exist."
            else:
                conn.commit()
                message = "You have successfully registered for the course."
        except psycopg2.Error as e:
            conn.rollback()
            if 'unique_student_course' in str(e):
                message = "You have already registered for this course."
            else:
                message = "Failed to register for the course. Please try again later."
        finally:
            cur.close()
            conn.close()
            return render_template('student_dashboard.html', courses=courses, message=message)

    # Render the dashboard for GET request or initial page load
    cur.close()
    conn.close()
    return render_template('student_dashboard.html', courses=courses)



@app.route('/my_courses')
def my_courses():
    if 'username' not in session or session['role'] != 'S':
        return redirect(url_for('login'))  # Redirect if not logged in or not a student

    conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST)
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cur.execute("""
        SELECT tc.CourseName, tc.CourseDetails, c.CoursePrice, c.Date, sc.PurchaseDate, sc.PaymentMethod
        FROM StudentCourses sc
        JOIN Courses c ON sc.CourseID = c.CourseID
        JOIN TeacherCourses tc ON c.TeacherCourseID = tc.CourseID
        WHERE sc.StudentID = %s;
    """, (session['user_id'],))
    registered_courses = cur.fetchall()
    cur.close()
    conn.close()

    return render_template('my_courses.html', registered_courses=registered_courses)

@app.route('/my_profile')
def my_profile():
    if 'username' not in session or session['role'] != 'S':
        return redirect(url_for('login'))  # Redirect if not logged in or not a student

    conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST)
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # Fetch the student's information
    cur.execute("""
        SELECT Username, Address, Phone, HomePhone, Email
        FROM Users
        WHERE ID = %s;
    """, (session['user_id'],))
    user_info = cur.fetchone()

    cur.close()
    conn.close()

    return render_template('my_profile.html', user_info=user_info)

@app.route('/personal_dashboard', methods=['GET', 'POST'])
def personal_dashboard():
    if 'username' not in session or session['role'] != 'P':
        return redirect(url_for('login'))

    conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST)
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    if request.method == 'POST':
        if 'update_course' in request.form:
            course_id = request.form['course_id']
            new_price = request.form['price']
            new_quota = request.form['quota']
            is_active = request.form['is_active'] == 'True'
            cur.execute("""
                UPDATE Courses
                SET CoursePrice = %s, Quota = %s, IsActive = %s
                WHERE CourseID = %s;
            """, (new_price, new_quota, is_active, course_id))
            conn.commit()

    # Fetching all courses for display and editing
    cur.execute("""
        SELECT c.CourseID, tc.CourseName, c.CoursePrice, c.Date, c.Quota, c.IsActive, u.Username AS TeacherName
        FROM Courses c
        JOIN TeacherCourses tc ON c.TeacherCourseID = tc.CourseID
        JOIN Teacher t ON tc.TeacherID = t.UserID
        JOIN Users u ON t.UserID = u.ID;
    """)
    courses = cur.fetchall()

    cur.close()
    conn.close()

    return render_template('personal_dashboard.html', courses=courses)

@app.route('/personnel_profile')
def personnel_profile():
    if 'username' not in session or session['role'] != 'P':
        return redirect(url_for('login'))  # Redirect if not logged in or not a personnel

    conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST)
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # Fetch the personnel's information
    cur.execute("""
        SELECT Username, Address, Phone, HomePhone, Email
        FROM Users
        WHERE ID = %s;
    """, (session['user_id'],))
    user_info = cur.fetchone()

    cur.close()
    conn.close()

    return render_template('personnel_profile.html', user_info=user_info)

@app.route('/view_user_details', methods=['GET', 'POST'])
def view_user_details():
    if 'username' not in session or session['role'] != 'P':
        return redirect(url_for('login'))  # Redirect if not logged in or not personnel

    conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST)
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cur.execute("SELECT ID, Username, Role FROM Users WHERE Role IN ('T', 'S');")
    users = cur.fetchall()

    user_info = None
    courses = None
    if request.method == 'POST':
        user_id = request.form['user_id']
        cur.execute("SELECT * FROM Users WHERE ID = %s;", (user_id,))
        user_info = cur.fetchone()

        if user_info:
            if user_info['role'] == 'S':
                cur.execute("""
                    SELECT tc.CourseName, sc.AttendanceDate, sc.PurchaseDate, sc.Price, sc.PaymentMethod
                    FROM StudentCourses sc, TeacherCourses tc
                    WHERE sc.StudentID = %s AND tc.courseid=sc.courseid;
                """, (user_id,))
                courses = cur.fetchall()
            elif user_info['role'] == 'T':
                cur.execute("""
                    SELECT tc.CourseName, tc.CourseDetails, tc.Price, tc.CourseDate
                    FROM TeacherCourses tc
                    WHERE tc.TeacherID = %s;
                """, (user_id,))
                courses = cur.fetchall()

    cur.close()
    conn.close()

    return render_template('view_user_details.html', users=users, user_info=user_info, courses=courses)


@app.route('/filter_courses', methods=['GET', 'POST'])
def filter_courses():
    if 'username' not in session or session['role'] != 'P':
        return redirect(url_for('login'))  # Redirect if not logged in or not personnel

    conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST)
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # Fetch students for the dropdown
    cur.execute("SELECT ID, Username FROM Users WHERE Role = 'S';")
    students = cur.fetchall()

    courses = []  # Initialize courses as an empty list
    message = None
    if request.method == 'POST':
        max_price = request.form.get('max_price')
        if max_price:
            cur.execute("""
                SELECT c.CourseID, tc.CourseName, c.CoursePrice, c.Date AS CourseDate
                FROM Courses c
                JOIN TeacherCourses tc ON c.TeacherCourseID = tc.CourseID
                WHERE c.CoursePrice <= %s;
            """, (max_price,))
            courses = cur.fetchall() or []  # Ensure courses is a list even if query returns None

        student_id = request.form.get('student_id')
        course_id = request.form.get('course_id')
        payment_method = request.form.get('payment_method')

        if student_id and course_id:
            # Attempt to register the student
            try:
                cur.execute("""
                    INSERT INTO StudentCourses (StudentID, CourseID, AttendanceDate, PurchaseDate, Price, PaymentMethod)
                    VALUES (%s, %s, (SELECT Date FROM Courses WHERE CourseID = %s), NOW(), (SELECT CoursePrice FROM Courses WHERE CourseID = %s), %s);
                """, (student_id, course_id, course_id, course_id, payment_method))
                conn.commit()
                message = "Registration successful."
            except Exception as e:
                conn.rollback()
                message = f"Failed to register: {str(e)}"

    cur.close()
    conn.close()

    return render_template('filter_courses.html', students=students, courses=courses, message=message)

@app.route('/add_user', methods=['GET', 'POST'])
def add_user():
    if 'username' not in session or session['role'] != 'P':
        return redirect(url_for('login'))  # Redirect if not logged in or not personnel

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        address = request.form['address']
        phone = request.form['phone']
        homePhone = request.form['homePhone']
        email = request.form['email']
        role = request.form['role']

        conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST)
        cur = conn.cursor()

        try:
            cur.execute("""
                INSERT INTO Users (Username, Password, Address, Phone, HomePhone, Email, Role)
                VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING ID;
            """, (username, password, address, phone, homePhone, email, role))
            user_id = cur.fetchone()[0]  # Fetch the ID of the newly created user

            if role == 'T':
                cur.execute("INSERT INTO Teacher (UserID) VALUES (%s);", (user_id,))
            elif role == 'S':
                cur.execute("INSERT INTO Students (UserID) VALUES (%s);", (user_id,))

            conn.commit()
            message = "New user added successfully."
        except IntegrityError:
            conn.rollback()
            message = "Username already exists. Please use a different username."
        except Exception as e:
            conn.rollback()
            message = f"Failed to add user: {str(e)}"
        finally:
            cur.close()
            conn.close()

        return render_template('add_user.html', message=message)

    return render_template('add_user.html')


if __name__ == '__main__':
    app.run(debug=True,port=5001)
