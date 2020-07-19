# File with various functions that are not associated with pod or pandas

# combine bytes to either a list of bytes are a integer from byte
def combineByte(byteList):
    if type(byteList) is int:
        return byteList
    fullInt = 0
    for thisInt in byteList:
        fullInt = 256*fullInt + thisInt
    return fullInt


# recursive version to handle single items (not lists) up
# through multi-layered lists (lol = list of lists)
def flatten(lol):
    if type(lol) is list:
        if len(lol) == 1:
            return flatten(lol[0])
        else:
            return flatten(lol[0]) + flatten(lol[1:])
    else:
        return [lol]


def printDict(thisDict):
    for keys, values in thisDict.items():
        print('  {} =   {}'.format(keys, values))
    print('\n')


def printList(thisList):
    for item in thisList:
        print(item)
    print('\n')


def listFromDict(thisDict):
    list_of_keys = []
    for keys, values in thisDict.items():
        list_of_keys.append(keys)
    return list_of_keys


def versionString(thisNumList):
    """
      Convert a list of numbers to a string separated by '.'
    """
    verStr = ""
    for val in thisNumList:
        verStr = verStr + "." + str(val)
    # remove leading "."
    verStr = verStr[1:]
    return verStr
