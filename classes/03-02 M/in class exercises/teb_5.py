# Goal: Accept numbers 1–5 only
# Keep asking until user enters a number between 1 and 5.

while True:
    try:
        x = int(input('enter 1-5'))
        if x == 1 and x <=5:
            print('correct')
            break
        else:
            print('incorrect')
    except ValueError:
        txt = 'value error, try again'
