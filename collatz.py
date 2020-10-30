def collatz(start, num):
    sum = 0
    for i in range(num):
        print('Iter: ' + str(i) + ' Num: ' + str(start))
        if start % 2 == 0:
            start = start/2
        else:
            start = start * 3 +1
        sum += start
    return sum


print(collatz(1, 9))