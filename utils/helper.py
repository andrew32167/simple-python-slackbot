import sys
import logger


def utf_to_str(utf):
    '''
    Function to convert utf-8 string to python string

    :param utf: utf-8 string
    :return:
    '''
    try:
        string = unicode(utf, 'utf8')
    except TypeError:
        string = utf
    string_for_output = string.encode('utf8', 'replace')
    return str(string_for_output)


def wrapped_function(function):
    '''
    Function to catch functions exceptions returns None when exception caught

    Usage:

        res = wrapped_function(lambda: my_function(args))

    :param function: function name
    :return: None when exception catched or actual function return when everything is OK
    '''
    try:
        res = function()
    except:
        logger.log('Exception caught')
        logger.log(sys.exc_info())
        return None
    return res
