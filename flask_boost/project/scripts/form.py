import os
from flask import current_app
from flask_script import Command, Manager, Option
import sqlalchemy as sa
from application.models import db
import application.models as models
import jinja2

form_manager = Manager(current_app, help='Form generation helper')


def _slug(s):
    return " ".join([x.title() for x in s.split("_")])


@form_manager.option("--model_name", "-m", dest="model_name", default='User')
def gen(model_name):
    """ generate wtform for models """
    model = getattr(models, model_name, None)
    if model:
        meta = list()
        cols = [c for c in model.__table__.columns]
        for col in cols:
            if col.name == 'id': continue

            if isinstance(col.type, sa.types.String):
                _meta = dict(col=col, wtform_type="StringField")
            if isinstance(col.type, sa.types.Unicode):
                _meta = dict(col=col, wtform_type="StringField")
            elif isinstance(col.type, sa.types.Integer):
                _meta = dict(col=col, wtform_type="IntegerField")
            elif isinstance(col.type, sa.types.DateTime):
                _meta = dict(col=col, wtform_type="DateTimeField")
            elif isinstance(col.type, sa.types.DECIMAL):
                _meta = dict(col=col, wtform_type="DecimalField")
            elif isinstance(col.type, sa.types.Text):
                _meta = dict(col=col, wtform_type="TextAreaField")
                # meta.append(dict(col=col, wtform_type="TextField"))
            elif isinstance(col.type, sa.types.Boolean):
                _meta = dict(col=col, wtform_type="BooleanField")
            elif isinstance(col.type, sa.types.Date):
                _meta = dict(col=col, wtform_type="DateField")
            elif isinstance(col.type, sa.types.Time):
                _meta = dict(col=col, wtform_type="TimeField")
            elif isinstance(col.type, sa.types.Float):
                _meta = dict(col=col, wtform_type="FloatField")
            elif isinstance(col.type, sa.types.JSON):
                _meta = dict(col=col, wtform_type="TextField")

            # check default validators
            _validators = []
            if col.nullable is False:
                _validators.append("v.DataRequired()")

            if _validators:
                _meta['wtform_args'] = 'validators=[%s]' % ", ".join(validators) 

            meta.append(_meta)

        template_path = os.path.join(os.getcwd(), 'scripts', "form.template")
        with open(template_path, 'r') as template:
            t = template.read()
            temp = jinja2.Template(t)
            print temp.render(model_name=model.__name__, columns=meta, slug=_slug)
    else:
        print "%s Model not found" % model_name

