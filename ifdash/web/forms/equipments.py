from flask_wtf import FlaskForm
from wtforms import fields, widgets, validators
from .fields import CoordinatesField


class EquipmentForm(FlaskForm):
    coordinates = CoordinatesField("Coordinates")
