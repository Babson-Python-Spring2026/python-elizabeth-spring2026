class Rectangle:
    def __init__(self, width, height):
        self.width = width
        self.height = height

    def area(self):
        return self.width * self.height

    def perimeter(self):
        return 2 * (self.width + self.height)
        
rec1 = Rectangle(5,10)
rec2 = Rectangle(3,3)

print(rec1.area())
print(rec1.perimeter())
print(rec2.is_square())