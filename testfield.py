def print_paper_airplane():
    width = 20
    length = 50

    # Print top part of the airplane
    for i in range(3):
        print(' ' * (width - 2 - i) + '/' + ' ' * (2 * i) + '\\')

    # Print body of the airplane
    for i in range(length):
        if i < 5 or i > length - 6:
            print(' ' * width)
        elif i % 2 == 0:
            print(' ' * (width // 2 - 1) + '\\' + ' ' * (length - 2) + '/')
        else:
            print(' ' * (width // 2) + ' ' * (length - 2) + ' ')

    # Print bottom part of the airplane
    for i in range(3):
        print(' ' * (width - 2 + i) + '\\' + ' ' * (2 * (2 - i)) + '/')

print_paper_airplane()
a = 3