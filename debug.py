import importlib

gdb = importlib.import_module("gdb")


class Breakpoint(gdb.Breakpoint):
    def __init__(
            self,
            source=None,
            line=None,
            address=None
    ):
        if (source is not None) and (line is not None):
            gdb.Breakpoint.__init__(
                self,
                source=source,
                line=line
            )

            return

        gdb.Breakpoint.__init__(
            self,
            "*" + str(address)
        )

    def stop(self):
        return True
