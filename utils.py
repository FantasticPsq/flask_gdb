import importlib

from gdbfrontend.api.debug import Variable

gdb = importlib.import_module("gdb")


def get_variable_by_expression(expression):
    try:
        value = gdb.parse_and_eval(expression)
        variable = Variable(
            frame=gdb.selected_frame(),
            symbol=False,
            value=value,
            expression=expression
        )
    except gdb.error as e:
        print(e)
        return None
    except Exception as e:
        print(e)
        return None
    return variable
