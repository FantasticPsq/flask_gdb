import importlib
import os.path
import re

from flask import Flask, request
from werkzeug.utils import secure_filename
from flask_cors import CORS

app = Flask(__name__)
CORS(app=app)
gdb = importlib.import_module("gdb")
bash_path = os.path.dirname(__file__)


@app.route('/upload/file', methods=["POST"])
def upload_file():  # put application's code here
    file = request.files.get("file")
    if file is None:
        return {"code": 1, "msg": "no file"}
    file_path = os.path.join(bash_path, secure_filename(file.filename))
    file.save(file_path)
    os.system("gcc -g %s -o a.out" % file.filename)
    return {"code": 200, "msg": "success"}


@app.route('/breakpoint', methods=["POST"])
def add_breakpoint():
    line = int(request.args.get("line"))
    try:
        gdb.execute("file a.out")
        gdb.execute("break %d" % line)
    except Exception as e:
        print(e)
        return {"code": 2, "msg": "打断点失败"}
    return {"code": 200, "msg": "success"}


@app.route("/breakpoint", methods=["DELETE"])
def delete_breakpoint():
    # 根据断点编号删除断点
    number = request.args.get("number")

    try:
        gdb.execute("d %s" % number)
    except Exception as e:
        return {"code": 3, "msg": e.__str__()}
    return {"code": 200, "msg": "success"}


@app.route("/breakpoints/info")
def get_breakpoint_info():
    target_breakpoints = request.args.get("target")
    if target_breakpoints is not None:
        cmd = "i breakpoints %s" % target_breakpoints
    else:
        cmd = "i breakpoints"
    breakpoints = gdb.execute(cmd)
    return {"code": 200, "msg": "success", "data": {"breakpoints": breakpoints}}


@app.route('/breakpoints')
def get_breakpoints():
    bps = []
    for _breakpoint in gdb.breakpoints():
        _breakpoint_json = {}
        _breakpoint_json["number"] = _breakpoint.number
        _breakpoint_json["enabled"] = _breakpoint.enabled
        _breakpoint_json["location"] = _breakpoint.location
        _breakpoint_json["expression"] = _breakpoint.expression
        _breakpoint_json["condition"] = _breakpoint.condition
        _breakpoint_json["thread"] = _breakpoint.thread

        if isinstance(_breakpoint.location, str) and (_breakpoint.location.__len__() > 1) and (
                _breakpoint.location[0] == "*"):
            try:
                _breakpoint_json["assembly"] = gdb.execute("x/i " + str(_breakpoint.location[1:]), to_string=True)
            except:
                pass
        bps.append(_breakpoint_json)
    return {"code": 200, "msg": "success", "data": {"breakpoints": bps}}


@app.route("/debug/run", methods=["POST"])
def run_debug():
    try:
        gdb.execute("r")
    except gdb.error as e:
        print(e)
        return {"code": 4, "msg": "运行失败"}

    return {"code": 200, "msg": "success"}


@app.route("/debug/continue", methods=["POST"])
def debug_continue():
    try:
        gdb.execute("c")
    except gdb.error as e:
        # 如果当前断点之后没有断点了，程序运行结束
        return {"code":200,"msg":"程序运行结束"}
    return {"code": 200, "msg": "success"}


@app.route("/debug/next", methods=["POST"])
def debug_next():
    try:
        gdb.execute("n")
    except gdb.error as e:
        print(e)
        return {"code": 6, "msg": "next失败"}
    return {"code": 200, "msg": "success"}


@app.route("/debug/step", methods=["POST"])
def debug_step():
    try:
        gdb.execute("s")
    except gdb.error as e:
        print(e)
        return {"code": 7, "msg": "step失败"}
    return {"code": 200, "msg": "success"}


@app.route("/debug/variables")
def get_variables():
    data = {}
    # 获取当前栈帧
    frame = gdb.selected_frame()
    variables = []
    try:
        # 获取当前域
        block = frame.block()
    except RuntimeError:
        block = False

    if not block:
        return {"msg": "error"}
    # 遍历当前域中的表达式
    for symbol in block:
        # 寻找所有变量和参数
        if (symbol.is_argument or symbol.is_variable) and (symbol.name not in variables):
            try:
                value = symbol.value(frame)
            except Exception as e:
                print(e)
            try:
                # 将变量解析为gdb.Value,Value中包含了对象的值
                value = gdb.parse_and_eval(symbol.name)
                variable = Variable(
                    frame=gdb.selected_frame(),
                    symbol=False,
                    value=value,
                    expression=symbol.name
                )
                # 将variable序列化成JSON格式
                variables.append(variable.serializable())
            except Exception as e:
                print(e)
    data['variables'] = variables
    return {"code": 200, "msg": "success", "data": data}


@app.route("/debug/vars")
def get_vars():
    vars = []
    varArr = gdb.execute("i locals", to_string=True).splitlines()
    print(varArr)
    for var in varArr:
        data = {"name": var.split(" = ")[0], "value": var.split(" = ")[1]}
        vars.append(data)
    return {"code": 200, "msg": "success", "data": vars}


@app.route("/debug/stack/trace")
def get_stack_trace():
    trace = []
    recursion_num = 0
    # 当前栈帧
    frame = gdb.selected_frame()

    def _back(frame):
        nonlocal recursion_num
        if recursion_num > 100:
            return
        recursion_num += 1
        parent = frame.older()
        # 递归寻找parent frame
        if parent is not None:
            trace.append(parent)
            _back(parent)

    trace.append(frame)
    _back(frame)
    # frame是不能直接序列化的
    backtrace_json = []
    for _stack_frame in trace:
        _name = _stack_frame.name()
        _function = _stack_frame.function()
        _stack_frame_json = {}
        _stack_frame_json["pc"] = frame.pc()
        _stack_frame_json["function"] = _name
        _stack_frame_json["file"] = {}
        if _function is not None:
            _stack_frame_json["line"] = _stack_frame.find_sal().line
            _stack_frame_json["file"]["name"] = _function.symtab.filename
            _stack_frame_json["file"]["path"] = _function.symtab.fullname()
        else:
            _stack_frame_json["file"] = False
        backtrace_json.append(_stack_frame_json)
    return {"code": 200, "msg": "success", "data": {"trace": backtrace_json}}


@app.route("/debug/watches")
def get_watches():
    expression = request.args.get("expression")
    if not expression:
        return {"code": 1001, "msg": "参数错误"}
    value = gdb.parse_and_eval(expression)
    return {"code": 200, "msg": "success", "data": {"value": value}}


@app.route("/debug/registers")
def get_registers():
    data = {}
    try:
        lines = gdb.execute("i registers", to_string=True).splitlines()
    except gdb.error:
        return {"code": 200, "msg": "success", "data": {}}
    for line in lines:
        print(line)
        vals = re.findall("(.+?)\\s+(.+?)\\s+(.+)", line, flags=re.IGNORECASE)

        if len(vals) < 1: continue
        if len(vals[0]) < 3: continue
        vals = vals[0]
        data[vals[0]] = (
            vals[1],
            vals[2]
        )
    return {"code": 200, "msg": "success", "data": data}


def get_variable_by_expression(expression):
    try:
        value = gdb.parse_and_eval(expression)
        print(value)
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


class Variable:

    def __init__(self, frame, symbol=False, value=False, expression=False):
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


if __name__ == '__main__':
    app.run(host="0.0.0.0")
