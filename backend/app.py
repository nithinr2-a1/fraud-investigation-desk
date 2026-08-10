from flask_login import login_required, current_user
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from prediction import prediction_bp

from config import Config
from extensions import login_manager
from evidence import evidence_bp

# Use the correct import depending on your auth structure
from auth import auth_bp
from dashboard import dashboard_bp

from db import claims, users, cases, evidence
from claims import claims_bp
from cases import cases_bp

app = Flask(__name__)
app.config.from_object(Config)

CORS(app)

login_manager.init_app(app)

app.register_blueprint(auth_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(claims_bp)
app.register_blueprint(cases_bp)
app.register_blueprint(evidence_bp)
app.register_blueprint(prediction_bp)

print("\n========= URL MAP =========")
print(app.url_map)
print("===========================\n")

print("Login Manager:", login_manager)
print("User Loader :", login_manager._user_callback)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/claims", methods=["GET"])
def get_claims():
    data = []

    for claim in claims.find():
        claim["_id"] = str(claim["_id"])
        data.append(claim)

    return jsonify(data)


@app.route("/api/claims", methods=["POST"])
def add_claim():
    claim = request.json

    result = claims.insert_one(claim)

    claim["_id"] = str(result.inserted_id)

    return jsonify(claim), 201


@app.route("/api/claims/bulk", methods=["POST"])
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