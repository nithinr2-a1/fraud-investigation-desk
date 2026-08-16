from flask import (
    render_template,
    request,
    redirect,
    url_for,
    flash,
    abort
)

from flask_login import login_required, current_user

from bson import ObjectId
from werkzeug.security import generate_password_hash

from . import users_bp
from db import users


# ============================================================
# Users List
# ============================================================

@users_bp.route("/users")
@login_required
def users_list():

    all_users = list(
        users.find().sort("username", 1)
    )

    total_users = users.count_documents({})

    admin_count = users.count_documents({
        "role": "Admin"
    })

    investigator_count = users.count_documents({
        "role": "Investigator"
    })

    active_users = users.count_documents({
        "$or": [
            {"status": "Active"},
            {"status": {"$exists": False}}
        ]
    })

    return render_template(
        "users.html",
        users=all_users,
        total_users=total_users,
        active_users=active_users,
        admin_count=admin_count,
        investigator_count=investigator_count
    )


# ============================================================
# Add User
# ============================================================

@users_bp.route("/users/add", methods=["GET", "POST"])
@login_required
def add_user():

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        name = request.form.get(
            "name",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip()

        role = request.form.get(
            "role",
            "Investigator"
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        # --------------------------------------------
        # Validation
        # --------------------------------------------

        if not username:
            flash(
                "Username is required.",
                "danger"
            )
            return render_template(
                "add_user.html"
            )

        if not password:
            flash(
                "Password is required.",
                "danger"
            )
            return render_template(
                "add_user.html"
            )

        if len(password) < 6:
            flash(
                "Password must contain at least 6 characters.",
                "danger"
            )
            return render_template(
                "add_user.html"
            )

        # --------------------------------------------
        # Duplicate username
        # --------------------------------------------

        existing_user = users.find_one({
            "username": username
        })

        if existing_user:

            flash(
                "Username already exists.",
                "danger"
            )

            return render_template(
                "add_user.html"
            )

        # --------------------------------------------
        # Create user
        # --------------------------------------------

        user_document = {

            "username": username,

            "name": name,

            "email": email,

            "role": role,

            "password": generate_password_hash(
                password
            ),

            "status": "Active"
        }

        users.insert_one(
            user_document
        )

        flash(
            "User created successfully.",
            "success"
        )

        return redirect(
            url_for("users.users_list")
        )

    return render_template(
        "add_user.html"
    )


# ============================================================
# Edit User
# ============================================================

@users_bp.route(
    "/users/edit/<user_id>",
    methods=["GET", "POST"]
)
@login_required
def edit_user(user_id):

    try:

        user = users.find_one({
            "_id": ObjectId(user_id)
        })

    except Exception:

        abort(404)

    if not user:
        abort(404)

    # --------------------------------------------
    # POST
    # --------------------------------------------

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        name = request.form.get(
            "name",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip()

        role = request.form.get(
            "role",
            "Investigator"
        ).strip()

        status = request.form.get(
            "status",
            "Active"
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        # --------------------------------------------
        # Validation
        # --------------------------------------------

        if not username:

            flash(
                "Username is required.",
                "danger"
            )

            return render_template(
                "edit_user.html",
                user=user
            )

        # --------------------------------------------
        # Check duplicate username
        # --------------------------------------------

        duplicate = users.find_one({
            "username": username,
            "_id": {
                "$ne": ObjectId(user_id)
            }
        })

        if duplicate:

            flash(
                "Username already exists.",
                "danger"
            )

            return render_template(
                "edit_user.html",
                user=user
            )

        # --------------------------------------------
        # Update fields
        # --------------------------------------------

        update_data = {

            "username": username,

            "name": name,

            "email": email,

            "role": role,

            "status": status
        }

        # --------------------------------------------
        # Update password only if entered
        # --------------------------------------------

        if password:

            if len(password) < 6:

                flash(
                    "Password must contain at least 6 characters.",
                    "danger"
                )

                return render_template(
                    "edit_user.html",
                    user=user
                )

            update_data["password"] = (
                generate_password_hash(password)
            )

        users.update_one(
            {
                "_id": ObjectId(user_id)
            },
            {
                "$set": update_data
            }
        )

        flash(
            "User updated successfully.",
            "success"
        )

        return redirect(
            url_for(
                "users.users_list"
            )
        )

    return render_template(
        "edit_user.html",
        user=user
    )


# ============================================================
# Delete User
# ============================================================

@users_bp.route(
    "/users/delete/<user_id>",
    methods=["POST"]
)
@login_required
def delete_user(user_id):

    try:

        object_id = ObjectId(user_id)

    except Exception:

        abort(404)

    # --------------------------------------------
    # Prevent deleting logged-in user
    # --------------------------------------------

    if str(current_user.id) == str(user_id):

        flash(
            "You cannot delete the currently logged-in user.",
            "danger"
        )

        return redirect(
            url_for("users.users_list")
        )

    user = users.find_one({
        "_id": object_id
    })

    if not user:

        flash(
            "User not found.",
            "danger"
        )

        return redirect(
            url_for("users.users_list")
        )

    users.delete_one({
        "_id": object_id
    })

    flash(
        "User deleted successfully.",
        "success"
    )

    return redirect(
        url_for("users.users_list")
    )