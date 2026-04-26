class Rectangle:
    def __init__(self, width, height):
        if width < 0 or height < 0: 
            width = 0
            height = 0

        self.width = width
        self.height = height

    def area (self):
        return self.width * self.height

    @property 
    def width(self):
        return self._width
    
    @width.setter
    def width(self, value):
        self._width = value

    
    

r1 = Rectangle(7,8)

r1.width = 14

print(r1._width)

   
   