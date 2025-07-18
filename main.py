import os
import json

from functools import wraps

from flask import Flask, request, Response, render_template
from flask_cors import CORS

from filelock import FileLock

DB_FILE_PATH = "db.json"
INITIAL_MONEY = {"money": 0, "overall_money": 0} 
DEFAULT_JSON_INDENT = 4
DB_LOCK = FileLock("db.json.lock")

app = Flask(__name__)
CORS(app)

def _add_to_overall(amount: int):
    if amount > 0:
        app.config["db"]["overall_money"] += amount

def db_context(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        with DB_LOCK:
            with open(DB_FILE_PATH, "r") as db_file:
                app.config["db"] = json.load(db_file)
            result = func(*args, **kwargs)
            with open(DB_FILE_PATH, "w") as db_file:
                json.dump(app.config["db"], db_file, indent=4)
        return result
    return wrapper

@app.route("/api/delta", methods=["GET"])
@db_context
def add_money():
    amount = request.args.get("amount", type=int)
    app.config["db"]["money"] += amount
    _add_to_overall(amount)
    return Response(status=200)

@app.route("/", methods=["GET"])
@db_context
def money_counter():
    return render_template("index.html", money=app.config["db"]["money"])

def init_db():
    if not os.path.isfile(DB_FILE_PATH):
        with open(DB_FILE_PATH, "w") as db_file:
            json.dump(INITIAL_MONEY, db_file, indent=DEFAULT_JSON_INDENT)

def main():
    init_db()
    app.run(host="0.0.0.0", port=5004)


if __name__ == "__main__":
    main()
