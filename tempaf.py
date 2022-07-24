mylist = [1,2,3,4,5,6,7,8,9,10]

for number in mylist[:]:
    print("number : ", number)
    print("mylist : ", mylist)
    mylist.remove(number)
    print("mylist : ", mylist)
    if number == 4:
        break

print("mylist : ", mylist)




