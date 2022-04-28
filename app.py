import importlib
import json
import os.path

from flask import Flask, request
from werkzeug.utils import secure_filename

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


if __name__ == '__main__':
    app.run(host="0.0.0.0")
