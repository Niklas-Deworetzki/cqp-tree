import os
from flask import Flask, request, render_template, flash, url_for
from cqp_tree import cqp_from_query
from cqp_tree.grew import query_from_grew
from cqp_tree.deptreepy import query_from_deptreepy
from cqp_tree.translation.errors import *

app = Flask(__name__)
app.secret_key = os.urandom(12).hex() # apparently necessary to flash messages

url_for('static', filename='style.css')

@app.route("/", methods=["GET"])
def main():
    return render_template("index.html", cqp="")

@app.route('/', methods=["POST"])
def translate():
    form_content = request.form
    query_str = form_content["query_str"]
    query = None
    try:
        if form_content["language"] == "deptreepy":
            query = query_from_deptreepy(query_str) 
        elif form_content["language"] == "grew":
            query = query_from_grew(query_str)
        else:
            pass # guess?
    except ParsingFailed as parse_failure:
        flash("\n".join(
            ["Query cannot be parsed:"] 
          + [str(err) for err in parse_failure.errors]))
    except NotSupported as not_supported:
        if not str(not_supported):
            flash('Query cannot be translated.')
        else:
            flash('Query cannot be translated: ' + str(not_supported))
    cqp = cqp_from_query(query) if query else ""
    return render_template("index.html", cqp=str(cqp))
