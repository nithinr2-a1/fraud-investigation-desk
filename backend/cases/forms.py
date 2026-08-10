from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    SelectField,
    TextAreaField,
    SubmitField
)
from wtforms.validators import DataRequired


class CaseForm(FlaskForm):

    claim_id = SelectField(
        "Claim",
        validators=[DataRequired()],
        choices=[]
    )

    investigator = StringField(
        "Investigator",
        validators=[DataRequired()]
    )

    priority = SelectField(
        "Priority",
        choices=[
            ("Low", "Low"),
            ("Medium", "Medium"),
            ("High", "High")
        ]
    )

    status = SelectField(
        "Status",
        choices=[
            ("Open", "Open"),
            ("Under Review", "Under Review"),
            ("Closed", "Closed")
        ]
    )

    remarks = TextAreaField("Remarks")

    submit = SubmitField("Save Case")