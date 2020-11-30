import os, sys


def show_func_name(func_depth):
    """
        Show current function name, helpful for debug
    """
    return sys._getframe(func_depth).f_code.co_name


def show_line_num(func_depth):
    """
        Show current code line number, helpful for debug
    """
    return sys._getframe(func_depth).f_lineno


def inline_debug(func_depth=2):
    print("[Function Name: {0}; At Line: {1}]".format(show_func_name(func_depth), show_line_num(func_depth)))

