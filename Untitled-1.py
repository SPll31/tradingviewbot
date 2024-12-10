def fun(str1: str, str2: str):
    arr1 = [i for i in bytes(str1.lower(), "utf-8")]
    arr2 = [i for i in bytes(str2.lower(), "utf-8")]
    for i in range(1, len(arr1)):
        if arr1[i] < arr1[i-1]:
            saved = arr1[i]
            arr1[i] = arr1[i-1]
            arr1[i-1] = saved
    print(arr1)


print(fun('ряд', 'ярд'))
