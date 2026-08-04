from flask_login import login_required, current_user
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS

from config import Config
from extensions import login_manager

# Use the correct import depending on your auth structure
from auth import auth_bp

from db import claims, users, cases, evidence

app = Flask(__name__)
app.config.from_object(Config)

CORS(app)

login_manager.init_app(app)

app.register_blueprint(auth_bp)

print("\n========= URL MAP =========")
print(app.url_map)
print("===========================\n")

print("Login Manager:", login_manager)
print("User Loader :", login_manager._user_callback)


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

    if data:
        claims.insert_many(data)

    return jsonify({"message": "Uploaded Successfully"})

@app.route("/dashboard")
@login_required
def dashboard():
    return render_template(
        "dashboard.html",
        user=current_user
    )
if __name__ == "__main__":
    app.run(debug=True)