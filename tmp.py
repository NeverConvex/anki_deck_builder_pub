def shift_jis2unicode(charcode): # charcode is an integer
    if charcode <= 0xFF:
        shift_jis_string = chr(charcode)
    else:
        shift_jis_string = chr(charcode >> 8) + chr(charcode & 0xFF)
    unicode_string = shift_jis_string.encode('utf-8').decode('shift-jis')
    #assert len(unicode_string) == 1
    return ord(unicode_string)
