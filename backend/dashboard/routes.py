from flask import render_template
from flask_login import login_required, current_user

from . import dashboard_bp

from db import claims
from db import cases
from db import users
from db import predictions


@dashboard_bp.route("/dashboard")
@login_required
def dashboard():

    total_claims = claims.count_documents({})

    open_cases = cases.count_documents({
        "status": "Open"
    })

    high_risk = predictions.count_documents({
        "risk_level": "High"
    })

    total_users = users.count_documents({
        "status": "Active"
    })

    return render_template(
        "dashboard.html",

        user=current_user,

        total_claims=total_claims,

        open_cases=open_cases,

        high_risk=high_risk,

        total_users=total_users
    )