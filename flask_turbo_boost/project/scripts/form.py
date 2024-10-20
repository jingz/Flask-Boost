import click
import jinja2
import os

import sqlalchemy as sa
from sqlalchemy.inspection import inspect # mapper object
from flask.cli import AppGroup, with_appcontext

import application.models as models
from application.models import db


form_cli = AppGroup('form', help='Form generation helper')


# utils
def _slug(s):
    return " ".join([x.title() for x in s.split("_")])


@form_cli.command('generate')
@click.option("--model_name", default='User')
@click.option("--is_admin", default=False)
def gen(model_name, is_admin):
    """ generate wtform for models """

    return generate_form(model_name, is_admin)


def generate_form(model_name, is_admin):

    model = getattr(models, model_name, None)

    if not model:
        print("%s is not a Modle." % model_name)
        return

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
        if not col.nullable:
            _validators.append("v.DataRequired()")

        if _validators:
            _meta['wtform_args'] = 'validators=[%s]' % ", ".join(_validators)

        meta.append(_meta)

    one_relationships = list()
    many_relationships = list()
    # find relationships
    for r in inspect(model).relationships:
        _r = dict(key=r.key, cls=r.mapper.class_.__name__)
        if 'TOONE' in r.direction.name:
            one_relationships.append(_r)
            continue
        many_relationships.append(_r) # relationship name

    if not is_admin:
        template_path = os.path.join(os.getcwd(), 'scripts', "form.template")
    else:
        template_path = os.path.join(os.getcwd(), 'scripts', "admin_form.template")

    # render and return content
    with open(template_path, 'r') as template:
        t = template.read()
        temp = jinja2.Template(t)
        content = temp.render(model_name=model.__name__,
                          columns=meta,
                          one_relationships=one_relationships,
                          many_relationships=many_relationships,
                          slug=_slug)
        return content


MAP_COLUMN_PROVIDER = dict(uri=['site'],
                           street_name=['street'],
                           sentence=['about'])

def _find_mapping_provider(column_name):
    for k, l in MAP_COLUMN_PROVIDER.items():
        if column_name in l:
            return k
    return None


@form_cli.command()
@click.option("--model_name", default='User')
def factory(model_name):
    """generate factory for given model"""

    import faker

    model = getattr(models, model_name, None)
    if not model:
        print("The model not found")
        exit()

    exclude_list = ['id', 'created_at', 'updated_at']
    exclude_columns = list()
    meta = list()
    cols = [c for c in model.__table__.columns]
    f = faker.Faker()
    for col in cols:
        if col.name in exclude_list:
            exclude_columns.append(col)
            continue
        if bool(col.foreign_keys):
            exclude_columns.append(col)
            continue

        p = _find_mapping_provider(col.name)
        if p:
            _meta = dict(col=col, provider=p)
        elif getattr(f, col.name, None):
            _meta = dict(col=col, provider=col.name)
        elif isinstance(col.type, sa.types.String):
            _meta = dict(col=col, provider="word")
        elif isinstance(col.type, sa.types.Integer):
            _meta = dict(col=col, provider="pyint")
        elif isinstance(col.type, sa.types.DateTime):
            _meta = dict(col=col, provider="date_this_year")
        elif isinstance(col.type, sa.types.DECIMAL):
            _meta = dict(col=col, provider="pydecimal")
        elif isinstance(col.type, sa.types.Text):
            _meta = dict(col=col, provider="text")
        elif isinstance(col.type, sa.types.Boolean):
            _meta = dict(col=col, provider="pybool")
        elif isinstance(col.type, sa.types.Date):
            _meta = dict(col=col, provider="date_this_month")
        elif isinstance(col.type, sa.types.Time):
            _meta = dict(col=col, provider="time_object")
        elif isinstance(col.type, sa.types.Float):
            _meta = dict(col=col, provider="pyfloat")
        elif isinstance(col.type, sa.types.JSON):
            _meta = dict(col=col, wtform_type="simple_profile")
        meta.append(_meta)

    one_relationships = list()
    many_relationships = list()
    # find relationships
    for r in inspect(model).relationships:
        _r = dict(key=r.key, cls=r.mapper.class_.__name__)
        if 'TOONE' in r.direction.name:
            one_relationships.append(_r)
            continue
        many_relationships.append(_r) # relationship name

    template_path = os.path.join(os.getcwd(), 'scripts', "factory.template")

    with open(template_path, 'r') as template:
        t = template.read()
        temp = jinja2.Template(t)
        print(temp.render(model_name=model.__name__,
                          many_relationships=many_relationships,
                          one_relationships=one_relationships,
                          exclude_columns=exclude_columns,
                          columns=meta))
