from flask_wtf import FlaskForm

from wtforms import (
    StringField,
    FloatField,
    IntegerField,
    BooleanField,
    SubmitField
)

from wtforms.validators import (
    DataRequired,
    InputRequired,
    NumberRange
)


class ClaimForm(FlaskForm):

    # =========================================================
    # CLAIM INFORMATION
    # =========================================================

    claim_id = StringField(
        "Claim ID",
        validators=[
            DataRequired()
        ]
    )

    claim_type = StringField(
        "Claim Type",
        validators=[
            DataRequired()
        ]
    )

    # =========================================================
    # FINANCIAL INFORMATION
    # =========================================================

    claim_amount = FloatField(
        "Claim Amount",
        validators=[
            InputRequired(),
            NumberRange(
                min=0,
                message="Claim amount cannot be negative."
            )
        ]
    )

    policy_limit = FloatField(
        "Policy Limit",
        validators=[
            InputRequired(),
            NumberRange(
                min=0,
                message="Policy limit cannot be negative."
            )
        ]
    )

    premium = FloatField(
        "Premium",
        validators=[
            InputRequired(),
            NumberRange(
                min=0,
                message="Premium cannot be negative."
            )
        ]
    )

    # =========================================================
    # POLICY INFORMATION
    # =========================================================

    policy_age_days = IntegerField(
        "Policy Age",
        validators=[
            InputRequired(),
            NumberRange(
                min=0,
                message="Policy age cannot be negative."
            )
        ]
    )

    # =========================================================
    # CLAIM HISTORY
    # =========================================================

    prior_claims = IntegerField(
        "Prior Claims",
        validators=[
            InputRequired(),
            NumberRange(
                min=0,
                message="Prior claims cannot be negative."
            )
        ]
    )

    # =========================================================
    # REPORTING INFORMATION
    # =========================================================

    report_delay_days = IntegerField(
        "Report Delay",
        validators=[
            InputRequired(),
            NumberRange(
                min=0,
                message="Report delay cannot be negative."
            )
        ]
    )

    # =========================================================
    # CUSTOMER INFORMATION
    # =========================================================

    customer_age = IntegerField(
        "Customer Age",
        validators=[
            InputRequired(),
            NumberRange(
                min=18,
                max=120,
                message="Customer age must be between 18 and 120."
            )
        ]
    )

    # =========================================================
    # POLICE REPORT
    # =========================================================

    police_report = BooleanField(
        "Police Report Available"
    )

    # =========================================================
    # SUBMIT
    # =========================================================

    submit = SubmitField(
        "Save Claim"
    )