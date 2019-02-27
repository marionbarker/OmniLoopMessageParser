# file: byteUtils.py
# collect useful stuff that various modules will need

def combineByte(byteList):
    if type(byteList) is int :
        return byteList
    fullInt = 0;
    for thisInt in byteList:
        fullInt = 256*fullInt + thisInt
    return fullInt
