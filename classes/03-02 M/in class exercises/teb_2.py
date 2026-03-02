#Goal: Catch ZeroDivisionError
# Ask for two numbers.
# Divide the first by the second.
# Catch division by zero."

try:
    numerator = float(input('enter float'))
    denominator = float (input('enter float'))

    quotient = numerator / denominator

except ZeroDivisionError:
    print('you can not divide by 0')

except ValueError: 
    print('do not enter text, enter float')

else:
    print(quotient)
finally:
    print('maybe it worked maybe it did not')