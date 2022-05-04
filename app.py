import importlib
import os.path

from flask import Flask, request
from werkzeug.utils import secure_filename

from Variable import Variable

app = Flask(__name__)
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


@app.route('/breakpoint/add', methods=["POST"])
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


@app.route("/debug/run")
def run_debug():
    try:
        gdb.execute("r")
    except gdb.error as e:
        print(e)
        return {"code": 4, "msg": "运行失败"}

    return {"code": 200, "msg": "success"}


@app.route("/debug/continue")
def debug_continue():
    try:
        gdb.execute("c")
    except gdb.error as e:
        print(e)
        return {"code": 5, "msg": "continue失败"}
    return {"code": 200, "msg": "success"}


@app.route("/debug/next")
def debug_next():
    try:
        gdb.execute("n")
    except gdb.error as e:
        print(e)
        return {"code": 6, "msg": "next失败"}
    return {"code": 200, "msg": "success"}


@app.route("/debug/step")
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
    frame = gdb.selected_frame()
    variables = []
    try:
        block = frame.block()
    except RuntimeError:
        block = False
    while block:
        for symbol in block:
            if (symbol.is_argument or symbol.is_variable) and (symbol.name not in variables):
                try:
                    value = symbol.value(frame)
                except Exception as e:
                    print(e)
                try:
                    variable = get_variable_by_expression(symbol.name).serializable()
                    variables.append(variable)
                except Exception as e:
                    print(e)
    data['variables'] = variables
    return {"code": 200, "msg": "success", "data": data}


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


if __name__ == '__main__':
    app.run(host="0.0.0.0")
