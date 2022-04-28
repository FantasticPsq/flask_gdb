import importlib
import json
import os.path

from flask import Flask, request

app = Flask(__name__)
gdb = importlib.import_module("gdb")
file_path = os.path.dirname(__file__)


@app.route('/upload/file', methods=["POST"])
def upload_file():  # put application's code here
    file = request.files.get("file")
    if file is None:
        return {"code": 1, "msg": "no file"}
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


if __name__ == '__main__':
    app.run(host="0.0.0.0")
