from flask import Flask, request, render_template
from cqp_tree import cqp_from_query
from cqp_tree.grew import query_from_grew
from cqp_tree.deptreepy import query_from_deptreepy

app = Flask(__name__)

@app.route("/", methods=["GET"])
def main():
    return render_template("index.html")

@app.route('/translate', methods=["POST"])
def translate():
    form_content = request.form
    query_str = form_content["query_str"]
    print(form_content)
    if form_content["language"] == "deptreepy":
        query = query_from_deptreepy(query_str) 
    elif form_content["language"] == "grew":
        query = query_from_grew(query_str)
    else:
        pass # guess?
    return str(cqp_from_query(query))