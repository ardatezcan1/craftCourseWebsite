--Table Creates
CREATE TABLE Users (
    ID SERIAL PRIMARY KEY,
    Username VARCHAR(255) UNIQUE NOT NULL,
    Password VARCHAR(255) NOT NULL,
    Address TEXT,
    Phone VARCHAR(50),
    HomePhone VARCHAR(50),
    Email VARCHAR(100) UNIQUE NOT NULL,
    Role CHAR(1) CHECK (Role IN ('T', 'S', 'P', 'A'))
);

CREATE TABLE Teacher (
    UserID INT PRIMARY KEY,
    FOREIGN KEY (UserID) REFERENCES Users(ID)
);

CREATE TABLE TeacherCourses (
    CourseID SERIAL PRIMARY KEY,
    TeacherID INT NOT NULL,
    CourseName VARCHAR(255),
    CourseDetails TEXT,
    Price DECIMAL(10, 2) CHECK (Price >= 1 AND Price <= 5000),
    FOREIGN KEY (TeacherID) REFERENCES Teacher(UserID)
);

ALTER TABLE TeacherCourses
ADD CourseDate DATE;


CREATE TABLE Students (
    UserID INT PRIMARY KEY,
    FOREIGN KEY (UserID) REFERENCES Users(ID)
);

CREATE TABLE Courses (
    CourseID SERIAL PRIMARY KEY,
    TeacherCourseID INT,
    Date DATE,
    CoursePrice DECIMAL(10, 2),
    IsActive BOOLEAN,
    Quota INT,
    FOREIGN KEY (TeacherCourseID) REFERENCES TeacherCourses(CourseID)
);

ALTER TABLE Courses
ADD COLUMN Reservations INT DEFAULT 0;


CREATE TABLE StudentCourses (
    StudentCourseID SERIAL PRIMARY KEY,
    StudentID INT,
    CourseID INT,
    AttendanceDate DATE,
    PurchaseDate DATE,
    Price DECIMAL(10, 2),
    PaymentMethod VARCHAR(50) CHECK (PaymentMethod IN ('cash', 'card')),
    FOREIGN KEY (StudentID) REFERENCES Students(UserID),
    FOREIGN KEY (CourseID) REFERENCES Courses(CourseID)
);

-- Kurs ücretini course table'na atarken update
CREATE OR REPLACE FUNCTION update_course_price()
RETURNS TRIGGER AS $$
BEGIN
    -- Update the CoursePrice when the Price in the Teacher table changes
    IF TG_OP = 'UPDATE' OR TG_OP = 'INSERT' THEN
        UPDATE Courses
        SET CoursePrice = NEW.Price * 1.5
        WHERE TeacherID = NEW.UserID;
    ELSIF TG_OP = 'DELETE' THEN
        -- Optionally set a default price or make the course inactive when a teacher is deleted
        UPDATE Courses
        SET CoursePrice = 100  -- Default price
        WHERE TeacherID = OLD.UserID;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to call the function after updating the teacher price
CREATE TRIGGER trigger_update_course_price
AFTER INSERT OR UPDATE OR DELETE ON Teacher
FOR EACH ROW
EXECUTE PROCEDURE update_course_price();


--Update Courses table when Teacher has changes or insert

CREATE OR REPLACE FUNCTION update_course_price()
RETURNS TRIGGER AS $$
BEGIN
    -- Update the CoursePrice in Courses table when the Price in TeacherCourses changes
    IF TG_OP = 'UPDATE' THEN
        UPDATE Courses
        SET CoursePrice = NEW.Price * 1.5
        WHERE TeacherCourseID = NEW.CourseID;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_course_price
AFTER UPDATE ON TeacherCourses
FOR EACH ROW
EXECUTE PROCEDURE update_course_price();


-- When course created in teacher, it should be visable also in courses, but the price 1.5

CREATE OR REPLACE FUNCTION auto_add_course()
RETURNS TRIGGER AS $$
BEGIN
    -- Insert into Courses with CoursePrice set to 1.5 times the price from TeacherCourses
    INSERT INTO Courses (TeacherCourseID, Date, CoursePrice, IsActive, Quota)
    VALUES (NEW.CourseID, NEW.CourseDate, NEW.Price * 1.5, FALSE, 0);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


CREATE TRIGGER trigger_auto_add_course
AFTER INSERT ON TeacherCourses
FOR EACH ROW
EXECUTE PROCEDURE auto_add_course();


--Kursun kontenjanını kontrol eden bir trigger

CREATE OR REPLACE FUNCTION update_reservations()
RETURNS TRIGGER AS $$
BEGIN
    -- Check if adding another reservation would exceed the quota
    IF (SELECT Reservations FROM Courses WHERE CourseID = NEW.CourseID) >= 
       (SELECT Quota FROM Courses WHERE CourseID = NEW.CourseID) THEN
        RAISE EXCEPTION 'This course is already full.';
    ELSE
        -- Increment the reservations count
        UPDATE Courses SET Reservations = Reservations + 1 WHERE CourseID = NEW.CourseID;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER check_course_capacity
BEFORE INSERT ON StudentCourses
FOR EACH ROW
EXECUTE PROCEDURE update_reservations();


-- Insert Data
INSERT INTO Users (Username, Password, Address, Phone, HomePhone, Email, Role)
VALUES 
    ('teacher1', 'teacherpass1', '123 Main St, City, Country', '123456789', '987654321', 'teacher1@example.com', 'T'),
    ('teacher2', 'teacherpass2', '456 Elm St, City, Country', '987654321', NULL, 'teacher2@example.com', 'T'),
    ('teacher3', 'teacherpass3', '789 Oak St, City, Country', '5551234567', NULL, 'teacher3@example.com', 'T'),
    ('personnel1', 'personnelpass1', '789 Pine St, City, Country', '5559876543', NULL, 'personnel1@example.com', 'P'),
    ('personnel2', 'personnelpass2', '321 Cedar St, City, Country', '999888777', NULL, 'personnel2@example.com', 'P'),
    ('student1', 'studentpass1', '456 Oak St, City, Country', '1112223333', NULL, 'student1@example.com', 'S'),
    ('student2', 'studentpass2', '654 Maple St, City, Country', '4445556666', NULL, 'student2@example.com', 'S'),
    ('student3', 'studentpass3', '987 Walnut St, City, Country', '7778889999', NULL, 'student3@example.com', 'S'),
    ('student4', 'studentpass4', '741 Birch St, City, Country', '8889990000', NULL, 'student4@example.com', 'S'),
    ('student5', 'studentpass5', '852 Elm St, City, Country', '3334445555', NULL, 'student5@example.com', 'S');

-- Insert Teacher Records
INSERT INTO Teacher (UserID) VALUES (1), (2), (3);

-- Insert Student Records
INSERT INTO Students (UserID) VALUES (6), (7), (8), (9), (10);

-- Insert Teacher Courses
INSERT INTO TeacherCourses (TeacherID, CourseName, CourseDetails, Price, CourseDate)
VALUES 
    (1, 'Advanced Painting', 'Explore advanced painting techniques.', 180.00, '2024-06-01'),
    (1, 'Watercolor Workshop', 'Learn watercolor painting from basics to advanced.', 150.00, '2024-06-08'),
    (2, 'Sculpture 101', 'Introduction to sculpture for beginners.', 200.00, '2024-06-15'),
    (2, 'Metalwork Techniques', 'Advanced metalwork techniques.', 220.00, '2024-07-15'),
    (3, 'Digital Photography', 'Basics of digital photography.', 160.00, '2024-08-01'),
    (3, 'Film Photography', 'Exploring the art of film photography.', 170.00, '2024-07-08');

--Course Quota Update
UPDATE Courses
SET IsActive = TRUE, Quota = 10
WHERE CourseID BETWEEN 1 AND 10;

-- Insert Student-Course Enrollment
INSERT INTO StudentCourses (StudentID, CourseID, AttendanceDate, PurchaseDate, Price, PaymentMethod)
VALUES 
    (6, 1, '2024-06-01', '2024-05-01', 270.00, 'cash'),
    (6, 2, '2024-06-08', '2024-05-03', 250.00, 'card'),
    (6, 3, '2024-06-15', '2024-05-03', 310.00, 'card'),
    (7, 2, '2024-06-08', '2024-05-05', 225.00, 'card'),
    (7, 3, '2024-06-15', '2024-05-02', 300.00, 'card'),
    (8, 3, '2024-06-15', '2024-05-10', 300.00, 'card'),
    (9, 4, '2024-07-15', '2024-05-15', 330.00, 'cash'),
    (10, 5, '2024-08-01', '2024-05-20', 240.00, 'card'),
    (10, 6, '2024-07-08', '2024-05-20', 200.00, 'card');