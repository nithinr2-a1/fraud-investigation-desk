from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from db import claims
from bson import ObjectId

app = Flask(__name__)
CORS(app)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/claims", methods=["GET"])
def get_claims():

    data = []

    for claim in claims.find():
        claim["_id"] = str(claim["_id"])
        data.append(claim)

    return jsonify(data)


@app.route("/claims", methods=["POST"])
def add_claim():

    claim = request.json

    result = claims.insert_one(claim)

    claim["_id"] = str(result.inserted_id)

    return jsonify(claim), 201


@app.route("/claims/bulk", methods=["POST"])
def bulk_insert():

    data = request.json

    claims.delete_many({})

    if len(data):
        claims.insert_many(data)

    return jsonify({"message":"Uploaded Successfully"})


if __name__ == "__main__":
    app.run(debug=True)