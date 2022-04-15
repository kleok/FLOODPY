#  Python Module for import                           Date : 2018-04-07
#  vim: set fileencoding=utf-8 ff=unix tw=78 ai syn=python : Python PEP 0263
'''
_______________|  test_4pytest : Test pytest within integration like Travis.

    $ py.test --doctest-modules

REFERENCE:
    pytest:    https://pytest.org/latest/getting-started.html
                  or PDF at http://pytest.org/latest/pytest.pdf

CHANGE LOG
2018-04-07  Add fadd and its doctest. Conform to flake8.
2018-04-06  First version to dummy testing.
'''

from __future__ import absolute_import, print_function


def test_assert_try_repo():
    '''Dummy test.'''
    assert "Hello" == "Hello"


def fadd(x, y):
    '''Simple fuction.'''
    return x+y


def test_fadd_try_repo():
    '''Test fadd as doctest.
    >>> fadd(2, 3)
    5
    '''
    pass


if __name__ == "__main__":
    pass
