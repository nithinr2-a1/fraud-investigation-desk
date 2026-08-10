from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, FileField, SubmitField
from wtforms.validators import DataRequired


class EvidenceForm(FlaskForm):

    case_id = SelectField(
        "Case",
        validators=[DataRequired()],
        choices=[]
    )

    evidence_type = SelectField(
        "Evidence Type",
        choices=[
            ("Invoice", "Invoice"),
            ("Bank Statement", "Bank Statement"),
            ("Driver License", "Driver License"),
            ("CCTV", "CCTV"),
            ("Email", "Email"),
            ("Other", "Other")
        ]
    )

    description = StringField("Description")

    evidence_file = FileField(
        "Evidence File",
        validators=[DataRequired()]
    )

    submit = SubmitField("Upload Evidence")