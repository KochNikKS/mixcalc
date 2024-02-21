from decimal import Decimal, ROUND_HALF_UP
from typing import Callable
from random import randint
import re
import sys
import os
from typing import Any

VALID_NAME_LETTERS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz_0123456789'


class REGroups(object):
    """
    >>> line = 'This string is a test string'
    >>> a, b, c = REGroups(re.search(r'(is).*(is).*(ing)', line))[1, 2, 3]
    >>> print(a, b, c)
    is is ing
    """
    def __init__(self, result, subs=None):
        self.result = result
        self.substitute = subs

    def __getitem__(self, keys):
        keys = [keys] if type(keys) is int else keys

        if self.result is None:
            unpacked_result = [self.substitute] * len(keys)
        else:
            unpacked_result = []
            for key in keys:
                try:
                    unpacked_result.append(self.result.group(key))
                except IndexError:
                    unpacked_result.append(self.substitute)
        return unpacked_result if len(unpacked_result) > 1 else unpacked_result[-1]


def count_diff(a: list | tuple | dict | set, b: list | tuple | dict | set):
    if type(a) is dict and type(b) is dict:
        auniqs = {key: a[key] for key in a if key not in b or b[key] != a[key]}
        buniqs = {key: b[key] for key in b if key not in a or b[key] != a[key]}
        return auniqs, buniqs
    else:
        auniqs = [value for value in a if value not in b]
        buniqs = [value for value in b if value not in a]
    return auniqs, buniqs


#  TODO rewrite!!!!
def _randomname(constpart: str = '', rp_length: int = 6, delim: str = '', dirpath: str = '.', ext='tmp'):
    newname = ''
    while newname in os.listdir(dirpath) or not newname:
        newname = f'{constpart}{delim}{"".join(chr(randint(999, 10**rp_length)))}.{ext}'
        print(newname, newname in os.listdir(dirpath))
    return newname


def safesplit(line='', key=' ', minparts=1, maxsplit=0):
    """
    returns line split by key, with length of returned list not less than minparts value
    
    >>> a, b, c = safesplit('ab c', ' ', minparts=3)
    >>> print(f'a={a};b={b};c={c};')
    a=ab;b=c;c=;

    """
    normal_split_num = len(line.split(key))
    if normal_split_num < minparts:
        return line.split(key) + [''] * (minparts - normal_split_num)
    else:
        
        return line.split(key) if maxsplit == 0 else line.split(key, maxsplit=maxsplit)


def merge_symbols(line: str = '', keys=()):
    """
    removes symbol repeats, saving only first one in sequence
    """
    str_buffer = []
    for letter in line:
        last = str_buffer[-1] if len(str_buffer) > 0 else ''
        if letter == last and letter in keys:
            ...
        else:
            str_buffer.append(letter)
    line = line if not str_buffer else ''.join(str_buffer)
    return line


def conv_resub(exps: dict,  target: str):
    """
    Conveyour re.sub()

    :param exps: dict  # dictionary where keys are pattern expressions and corresponding values are substitutions
    :param target: str
    :return: str

    >>> print(conv_resub({'a': '1', 'b': '2', 'c': '3'}, target='abcdefgh'))
    123defgh
    """
    for exp in exps:
        target = re.sub(exp, exps[exp], target, re.MULTILINE)
    return target


def rec_resub(exps: tuple, subs: tuple, target: str):
    """
    Recursive realization of conveyour re.sub()
    :param exps:  tuple  # contains pattern strings in some order
    :param subs:  tuple  # contains cubstitution strings in corresponding order
    :param target:  str
    :return: str

    >>> print(rec_resub(('a', 'b', 'c'), ('1', '2', '3'), 'abcdefgh'))
    123defgh
    """
    if len(exps) > 1:
        index = len(exps) - 1
        return re.sub(exps[index], subs[index], rec_resub(exps=exps[:index], subs=subs[:index], target=target))
    else:
        return re.sub(exps[0], subs[0], target, re.MULTILINE)


def mcount(line: str, templates: str | tuple | list, sep=None, summary=True):
    """
    multi-key counter, if "symbols" is a string and "sep" == '' - each single symbol will 
    be counted elif "sep" is not empty string -> "symbols" will be splited by "sep" and 
    each part will be counted". If summary=False - returns dictionary like: 
    {template_1: count, template_2: count, ..., template_n: count}

    >>> print(mcount('ACTGCCCGTAGCTA', 'AC'))
    1
    >>> print(mcount('ACTGCCCGTAGCTA', 'AC', sep=''))
    8
    >>> print(mcount('ACTGCCCGTAGCTA', ['A', 'C']))
    8
    >>> print(mcount('ACTGCCCGTAGCTA', 'AC', sep='', summary=False))
    {'A': 3, 'C': 5}

    """
    
    templates = templates if type(templates) in (list, tuple) else tuple(templates) if\
        type(templates) is str and sep == '' else templates.split(sep)
    return sum([line.count(t) for t in templates]) if summary else {t: line.count(t) for t in templates}


def mget(d: dict, keylist=(), default: Any = None, aliases=False):

    """
    Replacement for the "alt_get" and multiget function.

    Searches for provided keys in dictionary and returns one value if at least one key found 
    when aliases==True or tuple of values, corresponding all found keys, when 
    aliases==False. If aliases are set to False and the number of defaults provided is less than 
    the number of keys, the last default provided will be used for the "extra" keys. A list of defaults 
    longer than the number of keys will be truncated to the size of the keylist

    >>> a = {1: 2, 2: 3, 3: 4, 4: 5}
    >>> print(mget(a, (1,2,11), 'Non-existent key', aliases=False))
    (2, 3, 'Non-existent key')
    >>> print(mget(a, (1,2,11), default=('Non-existent key', 'Error'), aliases=False))
    (2, 3, 'Error')
    >>> print(mget(a, ("hello", "is there", "anybody?"), default=('Non-existent key', 'Error'), aliases=False))
    ('Non-existent key', 'Error', 'Error')
    >>> b = {1: 2, 2: 2, 3: 2, 4: 15, 5: 12}
    >>> print(mget(b, (1, 2), aliases=True))
    2
    >>> print(mget(b, keylist='Hello', default=(1, 7, 17), aliases=True))
    1
    >>> print(mget(b, keylist=(3, 'Hello'), default=(1, 7, 17), aliases=True))
    2
    >>> print(mget(b, keylist=(1e+12, 'Hello'), default=1, aliases=True))
    1
    """
    if type(keylist) not in (list, tuple, dict):
        keylist = (keylist, )
    if type(default) not in (list, tuple):
        default = [default, ]

    if aliases:
        found_values = tuple(set(d[key] for key in keylist if key in d))
        if len(found_values) == 0:
            return default[0]
        elif len(found_values) == 1:
            return found_values[0]
        else:
            raise ValueError('Some of keys provided address non equal values')
    else:
        return tuple(d.get(key, default[i] if i < len(default) else default[-1]) for i, key in enumerate(keylist))


def dkey_search(dictionary, key):
    keys_table = dict(zip(map(str.lower, dictionary.keys()), dictionary.keys()))
    return keys_table.get(key.lower(), None)


def iter_func(converter: Callable, engine: Callable, effector: Callable, iter_object):
    """
    :param engine: # any of higher order functions able to iterate throughout iter_object
    :param effector: # function, which will be applied to all items in iter_object container
    :param iter_object: # some iterable container
    :param converter: # a post-processing function(e.g. list, tuple, dict etc)
    :return: # type of container, which will be returned depends on converter function

    >>> a = {i: str(i+2000) for i in range(1, 10)}
    >>> print(a)
    {1: '2001', 2: '2002', 3: '2003', 4: '2004', 5: '2005', 6: '2006', 7: '2007', 8: '2008', 9: '2009'}
    >>> print(iter_func(dict,filter,lambda x: int(x[1]) % x[0] == 0, a.items()))
    {1: '2001', 2: '2002', 4: '2004', 5: '2005', 8: '2008'}
    """

    try:
        return converter(engine(effector, iter_object))
    except TypeError:
        print('Inappropriate argument')
        raise TypeError


def tryfunc(func, argument=None, substitution=None):
    if substitution is None:
        substitution = argument
    try:
        return func(argument)
    except:
        return substitution


def dzip(values1, values2):
    return dict(zip(values1, values2))


def t_filter(f, s):
    return tuple(filter(f, s))


def is_iterable(something):
    try:
        something.iter()
        return True
    except TypeError:
        return False


def is_indexed(something):
    return hasattr(something, '__getitem__')


def is_container(something):
    return is_indexed(something) and not (type(something) is str)


def not_number(s: str):
    try:
        float(s)        
    except ValueError:
        return True
    return False
    

def is_number(s: str):
    try:
        float(s)
        return True
    except ValueError:
        return False


def mwsum(*addends):
    # print(list(addends))
    # print(list(zip(*addends)
    # print('addends', tuple(zip(*addends)))
    s = tuple(sum(addend) for addend in tuple(zip(*addends)))
    return s


# returns tuple with length equal to first iterable provided as argument (factor1)
# and with product of corresponding elements of first and second iterable as elements
def mwprod(factor1, factor2):
    first = is_container(factor1)
    second = is_container(factor2)

    if first and second:
        return tuple(i * u for i, u in zip(factor1, factor2))
    elif first and not second:
        return tuple(factor2 * u for u in factor1)
    elif not first and second:
        return tuple(factor1 * u for u in factor2)
    else:
        raise ValueError(f'No iterable arguments: {factor1} & {factor2}')


def anyone(i) -> bool:
    tpl = tuple(i)
    return any(tpl) and (len(tuple(filter(bool, tpl))) == 1)


def legal_varname(name: str):
    if len(name) > 100:
        return False
    try:
        exec('name=0')
    except SyntaxError:
        return False
    return True


def dict_min(some_dict: dict):  # returns keys, korresponding to the minimal value/es
    minimal = min(some_dict.values())
    return (key for key in some_dict if some_dict[key] == minimal)


def strfilter(line: str, filter_symbols='', sets=(), negative=False):
    """
    This function filter line using filter_symbols and sets to get set of acceptable symbols.
    sets variable must be iterable containing some of such strings as: LATIN, DIGITS, LINES, PUNCT, MATH, SPEC,
    SPACE.
    If negative is True function will remove defined symbols

    >>> print(strfilter(line='ATGCATGCATGC', filter_symbols='GCS'))
    GCGCGC
    >>> print(strfilter(line='HELLo Dolly, this is YOur fr1end - VAsya, my email is: #Vasya@gmail.com',
    ... sets=("LATIN", "SPEC")))
    HELLoDollythisisYOurfrendVAsyamyemailis#Vasya@gmailcom
    """

    LATIN = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
    DIGITS = '0123456789'
    LINES = '_-|'
    PUNCT_MARKS = '!,.?:;"\''
    MATH = '+=-*/\\[]{}%^'
    SPECIAL = '@#$'
    SPACE = ' '
    ALPHABET = {'LATIN': LATIN, 'DIGITS': DIGITS, 'LINES': LINES,
                'PUNCT': PUNCT_MARKS, 'MATH': MATH, 'SPEC': SPECIAL, 'SPACE': SPACE}
    if type(sets) is str:
        sets = [sets]

    if type(filter_symbols) is not str:
        filter_symbols = ''

    try:
        symbols_set = filter_symbols + ''.join(ALPHABET[sset] for sset in sets)
        return ''.join(filter(lambda x: x in symbols_set, line)) if not negative else \
               ''.join(filter(lambda x: x not in symbols_set, line))
    except KeyError:
        raise KeyError(f'Undefined symbol set found: {sets}. Only LATIN, DIGITS, LINES, PUNCT, MATH, SPEC and SPACE'
                       f' sets are acceptable.')
    except TypeError:
        raise TypeError(line, )


def ar_round(value: float, template=0.1):
    """
    >>> print(ar_round(123.12334, 0.1))
    123.1
    >>> print(ar_round(123.562334, 1))
    124.0
    """
    return float(Decimal(str(value)).quantize(exp=Decimal(str(template)), rounding=ROUND_HALF_UP))


def any_in(container1, container2):
    """
    Check, wheather any of container1 items exists in container2
    """
    return any(i in container2 for i in container1)


def all_in(container1, container2):
    """
    Check, whether all members of first container exists in container2, returns bool
    """
    return all(i in container2 for i in container1)


def each_in(keys: list | tuple, container):
    """
    Check, whether all keys exists in container and returns  tuple like 
    (True, True, False) (where True or False correspond to the presence of the 
    each single key in the container)
    
    """ 
    return tuple(key in container for key in keys)


def filter_dict(fnc, dictionary):  # filter dictionary
    return {key: dictionary[key] for key in filter(fnc, dictionary)}


def distance(x1, x0, y1=0, y0=0, z1=0, z0=0):
    return ((x1 - x0) ** 2 + (y1 - y0) ** 2 + ((z1 - z0) ** 2)) ** 0.5


def sub_strings(subs: str | list | tuple = (), text='', where=1):
    """
    subs: str | list | tuple # string or container with string values which will be searched
    text: str  # string where parts will be searched for
    where: int  # shall be 0 - start, -1 - end, 1 - to search in a whole string

    >>> print(sub_strings(('abc', ), 'abcdefgh', where=0))
    (True, ['abc'])
    >>> print(sub_strings('adc', 'abcdefgh', where=1))
    (False, [])
    >>> print(sub_strings(['abc', 'fg'], 'abcdefgh', where=0))
    (True, ['abc'])
    >>> print(sub_strings(['abc', 'cds'], 'abcdefgh', where=1))  # where==0 by default
    (True, [('abc', 0)])
    >>> print(sub_strings(['abc', 'fgh'], 'abcdefgh', where=-1))
    (True, ['fgh'])
    >>> print(sub_strings(['fgh'],'abcdefgh', where=1))
    (True, [('fgh', 5)])
    >>> print(sub_strings(['fgh', 'acc'], 'abcdefgh', where=0))
    (False, [])
    """

    subs = subs if is_container(subs) else [subs]
    if where == 1:
        return any(sub in text for sub in subs), [(sub, text.index(sub)) for sub in subs if sub in text]
    elif where == 0:
        return any(text.startswith(sub) for sub in subs), [sub for sub in subs if text.startswith(sub)]
    elif where == -1:
        return any(text.endswith(sub) for sub in subs), [sub for sub in subs if text.endswith(sub)]
    else:
        raise ValueError(f'Invalid "where" argument value {where}')


def substr_in(s: str, container: list | tuple, first=True) -> (bool, list):
    """
    :param s: substring to search for
    :param container: list, tuple etc., elements of which will be checked
    :param first: True - return only first found element (default), False - return all found elements
    :return: result (True/False), list of tuples: (index of elements, value of element)

    >>> a = ['Aquila non captat muscas', 'Cogito, ergo sum', 'Carthago delenda est', 'Alea iacta est']
    >>> print(*substr_in('est', a))
    True [(2, 'Carthago delenda est')]
    >>> print(*substr_in('est', a, False))
    True [(2, 'Carthago delenda est'), (3, 'Alea iacta est')]
    >>> print(*substr_in('Amicus Plato', a, False))
    False []
    """

    values_indexes = [(index, value) for index, value in enumerate(container) if s in value]
    return len(values_indexes) > 0, values_indexes[:1] if first else values_indexes


def cond_in(key_function: Callable, container: list | tuple, first=True) -> (bool, list):
    """
    :param key_function: function to providing condition for search (must return boolean)
    :param container: list, tuple etc., elements of which will be checked
    :param first: bool  # True - return only first found element (default), False - return all found elements
    :return: result (True/False), list of tuples: (index of elements, value of element)

    >>> a = [12, 123, 34, 45, 56, 7, 32, 22, 13]
    >>> print(*cond_in(lambda x: x < 32, a, first=False))
    True [(0, 12), (5, 7), (7, 22), (8, 13)]
    >>> print(*cond_in(lambda x: x < 32, a))
    True [(0, 12)]
    >>> print(*cond_in(str, a, first=False))
    False []

    """

    values_indexes = [(index, value) for index, value in enumerate(container) if key_function(value) is True]
    return len(values_indexes) > 0, values_indexes[:1] if first else values_indexes


def multisplit(line: str = '', *separators):
    first = separators[0]
    for s in separators:
        line = line.replace(s, first)
    return line.split(first)


def newer_than(actual_version: str, version_to_compare: str, delimiter='.'):
    """compares the actual version (as a string) with the given version (as a string) to answer whether the
    actual version is newer than the given version (the version in X.Y.Z format could be parsed) """

    av = actual_version.split(delimiter)
    vtc = version_to_compare.split(delimiter)
    l_av, l_vtc = len(av), len(vtc)
    max_length = max([l_av, l_vtc])
    for i in range (max_length):
        if i >= l_av:
            return False
        elif i >= l_vtc:
            return True
        elif int(av[i]) > int(vtc[i]):
            return True
    return False





class DotDict(dict):   
  # TODO написать более или менее подробное описание класса DotDict и возможностей его методов!!!
    """
    Words _DotDict__aliases and __aliases should not be used as keys as reserved for internal purposes

    >>> d = DotDict({'a': '2', 'b': 4, 'c': 6})
    >>> print(d)
    DotDict('a': '2', 'b': 4, 'c': 6)
    >>> d['d'] = 12
    >>> print(d)
    DotDict('a': '2', 'b': 4, 'c': 6, 'd': 12)
    >>> d.m = 100
    >>> print(d)
    DotDict('a': '2', 'b': 4, 'c': 6, 'd': 12, 'm': 100)
    >>> print(d.a)
    2
    >>> testdict = {'level1_1': [1, 2, {'x': 3, 'y': 4}], 'level1_2': {'a': 1, 'b': 2}}
    >>> dd = DotDict().convert(testdict)
    >>> print(dd)
    DotDict('level1_1': [1, 2, {'x': 3, 'y': 4}], 'level1_2': DotDict('a': 1, 'b': 2))
    >>> print(dd.level1_1)
    [1, 2, {'x': 3, 'y': 4}]
    >>> print(dd['level1_1', 'level1_2'])
    ([1, 2, {'x': 3, 'y': 4}], DotDict('a': 1, 'b': 2))
    """

    def __init__(self, *args, **kw):
        """
        Define 'default' only with variable name: default=value
        """
        super(DotDict, self).__init__(*args, **kw)
        # self.__defaults = defaults
        self.__aliases = {}


    def __iter__(self):
        return iter(i for i in super(DotDict, self).__iter__() if i != '_DotDict__aliases')
        # and i != '_DotDict__defaults')

    def contains(self, items):
        """
        >>> a = DotDict({1: 2, 3: 4, 5: 6})
        >>> print(a.contains(100))
        False
        >>> print(a.contains((1, 3, 7)))
        (True, True, False)
        """
        return items in self if not is_container(items) else tuple(item in self for item in items)

    def _getvalue(self, key):
        """
        Basic 'getter' function. 
        Could emulate dict.get() if pair (key, defauld_value) provided as a key
        (as soon as this function is not used directly, but called by other functions, which can 
        process multiple keys in one call, singular key in form "(key, default_value)" must be followed by 
        the comma:
        DotDict_name[(key, default_value),] (or [(key1, default1),(key2, default2),(keyn, defaultn)] for 
        multiple keys)).
        Could return self.default (if it is defined in the __init__ function) in case of non-existing key.


        >>> s = DotDict({1: 2, 3: 4, 5: 6, 'a': 777})
        >>> print(s.a)
        777
        >>> print(s[1])
        2
        >>> s.setalias('d', 'h')
        >>> s.d = 12
        >>> print(s.h, s.d)
        12 12
        >>> print(s[b, 3])
        3

        """
        if type(key) in (list, tuple) and len(key) == 2:
            return super(DotDict, self).get(key[0], key[1])
        elif super(DotDict, self).__contains__(key):
            return super(DotDict, self).__getitem__(key)
        elif not super(DotDict, self).__contains__(key) and key in self.__aliases:
            return super(DotDict, self).__getitem__(self.__aliases[key])
        else:
            raise KeyError(f"The key '{key}' does not exist")

    def __getattr__(self, key):
        return self._getvalue(key)

    def __getitem__(self, key):
        """
        >>> a = DotDict({'a': 1, 'b': 2, 'c': 3, 'd': 4})
        >>> print(a[('e', 112), ('d', -1), ('url', 'http://127.0.0.3:5000')])
        (112, 4, 'http://127.0.0.3:5000')
        """
        if type(key) in (list, tuple):
            result = [self._getvalue(single_key) for single_key in key]
            return tuple(result) if len(result) > 1 else result[-1]
        else:
            return self._getvalue(key)

    def __setattr__(self, key, value):
        super(DotDict, self).__setitem__(key, value)

    def asdict(self, keys, convertor=None):
        """
        Returns dictionary, with keys listed in "keys" argument and corresponding values from DotDict exemplar
        (if 'keys' is of type dict -> keys of this dictionary will be used as keys for returning dictionary and
        values from 'keys' dictionary will be used as default values (like default values in dict.get() method).
        If 'keys' is of type (tuple, list, set) -> in each subkey with type tuple or list subkey[-1] will be used as
        default value and subkey[0] - as key.

        :param keys:
        :return:

        >>> a = DotDict({'1': 2, '2': 3, '3': 4})
        >>> print(a.asdict(['1', '2', '3']))
        {'1': 2, '2': 3, '3': 4}
        >>> print(a.asdict({'6': 0, '3': 'Will not be returned'}))
        {'6': 0, '3': 4}
        >>> print(a.asdict([('111', 'will be returned'), ]))
        {'111': 'will be returned'}
        """

        if type(keys) not in (tuple, list, set, dict):
            keys = [keys]
        if type(keys) is dict:
            return {key: convertor(self._getvalue((key, value),)) if convertor else self._getvalue((key, value),) for key, value in keys.items()}
        else:
            return {key[0] if (type(key) in (tuple, list) and len(key) > 1) else key:
                    convertor(self._getvalue(key)) if convertor else self._getvalue(key) for key in keys}

    def get(self, key=(), default=()):
        """
        If some single key provided - calls 'get' method of the 'dict' class
        If multiple keys provided - returns a tuple of values corresponding to the specified keys if such keys exist or
        the corresponding default value for each missing key, if defaults defined in function call

        >>> a = DotDict({1: 2, 2: 3, 3: 4})
        >>> print(a.get(1, 1))
        2
        >>> print(a.get(0, 1))
        1
        >>> print(a.get((1, 2, 3), (0, 0, 0)))
        (2, 3, 4)
        >>> print(*a.get((10, 20, 30), ('These are', 'the default', 'values')))
        These are the default values
        >>> print(a.get((1, 2, 15), None))
        (2, 3, None)
        >>> print(a.get((14, 51, 3), None))
        (None, None, 4)
        """

        if is_container(key) and is_container(default) and len(key) <= len(default):
            return tuple(super(DotDict, self).get(key, default) for key, default in zip(key, default))
        elif is_container(key) and is_container(default) and len(key) > len(default):
            raise ValueError(f'The number of keys ({key}) does not match the number of default values ({default})')
        elif is_container(key) and not is_container(default):
            return tuple(super(DotDict, self).get(subkey, default) for subkey in key)
        else:
            return super(DotDict, self).get(key, default)

    def update_values(self, source: dict, keys: list | tuple, sub=None) -> None:
        """
        Current value will be replaced for each given key existing both in the class exemplar and in the 'source'
        variable. New key added with value from 'source' if source has this key else with None value.

        :param source: dict | DotDict  # dictionary or DotDict examplar to copy values from
        :param keys: list | tuple  # list or tuple etc. with keys used for coping values
        :return: None

        >>> testdict = {'level1_1': [1, 2, {'x': 3, 'y': 4}], 'level1_2': {'a': 1, 'b': 2}}
        >>> dd = DotDict().convert(testdict)
        >>> source_dict = {'aa': 11, 'bb': 12, 'cc': 13}
        >>> dd.update_values(source_dict, keys=('aa', 'cc'))
        >>> print(dd.aa, dd.cc)
        11 13
        >>> dd.update_values(source=testdict, keys=['hello'])
        >>> print(dd.hello)
        None
        >>> testdd = DotDict({'aaa': 111, 'bbb': 222, 'ccc': 333})
        >>> dd.level1_2.update_values(testdd, ('aaa', 'bbb'))
        >>> print(dd.level1_2.bbb)
        222
        """
        for key in (keys if keys else source.keys()):
            self.__setattr__(key, source[key] if key in source else sub)

    @classmethod
    def convert(cls, source):
        """
        Convert multilevel dictionaries into DotDict. Dictionaries in each level should not be interupted by other types
        of containers for dot notation be possible ( {{}, (), {{}, {{}, {}, {}}}, []} - acceptable, result will be:
        DotDict(DotDict, (), DotDict(DotDict, DotDict(DotDict, DotDict, DotDict)), []);
        {[{}]} - only first level will be converted)
        :param source: dict  # some multilevel dictionary to convert into DotDict
        :return:
        """
        if type(source) is dict and not any(type(source[key]) is dict for key in source):
            return DotDict(source)
        elif type(source) is dict and any(type(source[key]) is dict for key in source):
            for key in source:
                if type(source[key]) is dict:
                    source[key] = cls.convert(source[key])
            return DotDict(source)
        else:
            return source

    def __str__(self):

        p, s = "'", ''
        return 'DotDict(' + ', '.join([f'{p if type(key) is str else s}{key}{p if type(key) is str else s}: '
                                       f'{p if type(self[key]) is str else s}{self[key]}'
                                       f'{p if type(self[key]) is str else s}'
                                       for key in self.keys() if key not in ('_DotDict__aliases', )]) + ')'

    def __repr__(self):
        return self.__str__()

    def __len__(self):
        return super(DotDict, self).__len__() - 2

    def setalias(self, *a, **b):
        key, alias = None, None
        if 'key' in b:
            key = b['key']
        elif ('key' not in b) and len(a) > 0:
            key = a[0]

        if 'alias' in b:
            alias = [b['alias']] if type(b['alias']) not in (tuple, list, set) else list(b['alias'])
        elif ('alias' not in b) and len(a) > 1:
            alias = a[1:]

        if not key:
            raise TypeError('Missing required keyword argument "key" and no positional arguments provided')
        elif not alias:
            raise TypeError('Missing required keyword argument "alias" and no corresponding '
                            'positional arguments provided')
        elif alias in self:
            raise KeyError(f'The key "{alias}" already exists.')

        else:
            for a in alias:
                self.__aliases[a] = key

    def del_aliases(self, *alias):
        if alias:
            for al in alias:
                self.__aliases.pop(al)


    def _correct_keys(self):
        keys = (key for key in self if key != '_DotDict__aliases')
        return keys

    def keys(self):
        return tuple(self._correct_keys())


    def values(self):
        return tuple(self._getvalue(key) for key in self._correct_keys())




def sysargv(arguments=None, commands: list | tuple = (), aliases: list | tuple = (),
        def_vars: list | tuple | dict = ()):

    """
    n.b. flags are stored without '-' characters

    :param arguments: if None sys.argv will be used
    :param commands: enlists arguments wich must be in "commands" list
    :param aliases: enlists arguments wich are aliases, e.g. [('--help', '-h'), ('--noprint', '--np', '-n')];
                    those arguments having aliases will be replaced by the first of them
    :param def_vars: default values for enlisted variables, e.g. (('output', 'stdout'), ('Mg', 2.5))
    :return:

    >>> ar = ['aa', '-b', 'cc=123', 'hello_kitty!']
    >>> args = sysargv(arguments=ar, aliases=(('aaa', 'aa', 'a'), ('--bbb', '--bb', '-b'), ('ccc', 'cc', 'c')))
    >>> print(args.vars, args.flags)
    DotDict('ccc': '123') ['--bbb']
    """

    if arguments is None:
        arguments = sys.argv[1:]

    aliases = {al: group[0] for group in aliases for al in group[1:]}

    # default values for variables
    dv = dict(def_vars)
    # aliases in defaults
    cleared_def_vars = dict()
    for v in dv:
        cleared_def_vars[(v if v not in aliases else aliases[v])] = dv[v]

    # stored order
    indexed = {i: arg for i, arg in enumerate(arguments)}

    # variables
    # noinspection PyTypeChecker
    variables = dict([arg.split('=') for arg in arguments if '=' in arg and arg.count('=') == 1 and
                      legal_varname(arg.split('=')[0])])

    # flags
    longflags = [key for key in arguments if key.startswith('--')]
    shortflags = ['-' + subkey for key in arguments for subkey in
                  key[1:] if key.startswith('-') and not key.startswith('--')]
    flags = [aliases.get(f, f) for f in (longflags + shortflags)]

    # commands
    arg_commands = (arg for arg in arguments if aliases.get(arg, arg) in commands and not arg.startswith('-'))
    arg_commands = [aliases.get(c, c) for c in arg_commands]

    # variables without cli initiation
    unnamed = [arg for arg in arguments if not arg.startswith('-') and ('=' not in arg or arg.count('=') > 1)
               and aliases.get(arg, arg) not in commands]

    output = {'indexing': indexed, 'vars': variables, 'flags': flags, 'unnamed': unnamed, 'commands': arg_commands}

    # aliases
    for group_name in output:
        group = {aliases.get(v, v): output[group_name][v] for v in output[group_name]
                 } if type(output[group_name]) is dict else [aliases.get(v, v) for v in output[group_name]]
        output[group_name] = group

    # update dict of variables by cleared_def_vars (only non-existing variables)
    output['vars'].update({var: cleared_def_vars[var] for var in cleared_def_vars if var not in output['vars']})

    #print(output)
    return DotDict().convert(output)

