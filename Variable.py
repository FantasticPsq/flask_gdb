import importlib

gdb = importlib.import_module("gdb")


class Variable(gdb.Variable):

    def __int__(self, frame, symbol=False, value=False, expression=False):
        self.frame = frame
        self.symbol = symbol
        self.value = value
        self.expression = expression
        if self.expression:
            self.name = self.expression.split(".")[-1].split("->")[-1]
        else:
            self.name = self.symbol.name

    def serializable(self):

        frame = self.frame
        symbol = self.symbol
        if symbol:
            value = symbol.value(frame)
        else:
            value = self.value

        try:
            block = frame.block()
        except RuntimeError as e:
            print(e)
            return False
        serializable = {}
        serializable["is_global"] = block.is_global
        serializable["name"] = self.name
        serializable["expression"] = self.expression
        serializable["is_pointer"] = value.type.code == gdb.TYPE_CODE_PTR
        serializable["is_optimized_out"] = value.is_optimized_out
        try:
            serializable["address"] = str(value.address) if value.address else "0x0"
        except:
            serializable["address"] = "0x0"

        try:
            if not value.is_optimized_out:
                serializable["value"] = value.lazy_string(length=10000).value().string()
                serializable["is_nts"] = True
            else:
                serializable["value"] = '<optimized out>'
                serializable["is_nts"] = False
        except gdb.error as e:
            try:
                serializable["is_nts"] = False
                serializable["value"] = str(value)
            except gdb.MemoryError as e:
                print(e)
                return None
            except gdb.error as e:
                print(e)
        except UnicodeDecodeError as e:
            serializable["is_nts"] = False
            serializable["value"] = str(value)
        except Exception as e:
            print(e)

            return None
        return serializable