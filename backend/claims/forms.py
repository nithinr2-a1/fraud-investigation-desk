from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    FloatField,
    IntegerField,
    SubmitField
)

from wtforms.validators import DataRequired


class ClaimForm(FlaskForm):

    claim_id = StringField(
        "Claim ID",
        validators=[DataRequired()]
    )

    claim_type = StringField(
        "Claim Type",
        validators=[DataRequired()]
    )

    claim_amount = FloatField(
        "Claim Amount",
        validators=[DataRequired()]
    )

    policy_limit = FloatField(
        "Policy Limit",
        validators=[DataRequired()]
    )

    premium = FloatField(
        "Premium",
        validators=[DataRequired()]
    )

    policy_age_days = IntegerField(
        "Policy Age",
        validators=[DataRequired()]
    )

    prior_claims = IntegerField(
        "Prior Claims",
        validators=[DataRequired()]
    )

    report_delay_days = IntegerField(
        "Report Delay",
        validators=[DataRequired()]
    )

    customer_age = IntegerField(
        "Customer Age",
        validators=[DataRequired()]
    )

    submit = SubmitField("Save Claim")