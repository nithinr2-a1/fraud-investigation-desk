from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField
from wtforms.validators import DataRequired


class PredictionForm(FlaskForm):

    claim_id = SelectField(
        "Claim",
        validators=[DataRequired()],
        choices=[]
    )

    submit = SubmitField("Predict Fraud Risk")