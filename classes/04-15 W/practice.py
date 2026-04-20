student = {
    "name": "Ana",
    "score": 92
}

class Student:
    def __init__(self, name, score):
        self.name = name
        self.score = score
    
    def describe(self):
        print(f'{self.name} has a grade of {self.score}')
    
