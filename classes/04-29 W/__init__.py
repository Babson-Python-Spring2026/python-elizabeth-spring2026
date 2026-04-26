import json

class Student:
    def __init__(self, name, student_id=None):
        self.name = name
        self.student_id = student_id

class School:
    def __init__(self, name):
        self.name = name
        self.students = []
    
    def add_student(self, student):
        max_id = 0
        for s in self.students:
            if s.student_id is not None:
                if s.student_id > max_id:
                    max_id = s.student_id

        if student.student_id is None:
            student.student_id = max_id + 1

        self.students.append(student)

class Schools:
    def __init__(self):
        self.schools = []
    
    def add_school(self, school):
        self.schools.append(school)

my_schools = Schools()
babson = School('Babson')
mit = School('MIT')

my_schools.add_school(babson)
my_schools.add_school(mit)

eve = Student('Eve', 1)
babson.add_student(eve)

for student in babson.students:
    print(student.name, student.student_id)

for student in mit.students:
    print(student.name, student.student_id)