# Ask the user for an integer.

# If they enter something invalid, print:
# "That was not a valid integer."
try:
    x = int(input('enter integer'))
except ValueError:
    print('that was not a valid integer')

