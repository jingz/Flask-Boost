import click
import os
import jinja2
import sqlalchemy as sa

from flask import current_app
from flask.cli import AppGroup, with_appcontext
from flask_security import SQLAlchemyUserDatastore
from sqlalchemy.inspection import inspect # mapper object

import application.models as models
from application.models import db
from .form import generate_form


scaffold_admin_cli = AppGroup('scaffold_admin', help='Admin scaffold')


@scaffold_admin_cli.command('generate')
@click.option("--model_name", default='User')
@click.option("--force", default=False)
def generate(model_name, force):
    """generate scaffold for administration page."""

    model = getattr(models, model_name, None)

    # prepare paths
    # TODO configurable paths
    form_file_path = os.path.join(os.getcwd(), "application", "forms", "admin", model_name.lower() + ".py")
    controller_file_path = os.path.join(os.getcwd(), "application", "admin_controllers", model_name.lower() + ".py")
    view_dir_path = os.path.join(os.getcwd(), "application", "pages", "admin", model_name.lower())

    # check all three files exists
    if not force:
        verify = True
        if os.path.exists(form_file_path):
            print("%s has already exists." %form_file_path)
            verify = False
        if os.path.exists(controller_file_path):
            print("%s has already exists." %controller_file_path)
            verify = False
        if os.path.exists(view_dir_path):
            print("%s has already exists." %view_dir_path)
            return False

        if not verify: return False

    # write admin model form file
    admin_form_content = generate_form(model_name, True)
    print(admin_form_content)

    f = open(form_file_path, 'w')
    f.write(admin_form_content)
    f.close()
    print("Admin Form")
    print("%s generated." %form_file_path)

    # write admin model controller file
    _admin_template_path = os.path.join(os.getcwd(), 'scripts', 'admin_controller.template')
    template = open(_admin_template_path, 'r')
    t = template.read()
    temp = jinja2.Template(t)
    content = temp.render(model_name=model.__name__)
    f = open(controller_file_path, 'w')
    f.write(content)
    f.close()
    print("Admin Controller")
    print("%s generated." %controller_file_path)

    # write admin model views and create view dir
    _admin_views_path = os.path.join(os.getcwd(), 'scripts', 'admin_view_templates')
    # useing env to replace delimiters
    admin_view_env = jinja2.Environment(
        block_start_string='[%',
        block_end_string='%]',
        variable_start_string='[[',
        variable_end_string=']]',
        comment_start_string='<#',
        comment_end_string='#>',
        loader=jinja2.FileSystemLoader(_admin_views_path)
    )

    meta = _get_meta(model_name)

    if not os.path.exists(view_dir_path):
        os.makedirs(view_dir_path)

    print("Admin Views")
    for view in ["index.html","show.html", "edit.html", "new.html"]:
        content = admin_view_env.get_template(view) \
                    .render(model_name=model.__name__, meta=meta)

        view_file_path = os.path.join(view_dir_path, view)
        f = open(view_file_path, 'w')
        f.write(content)
        f.close()
        print("%s generated." %view_file_path)


def _get_meta(model_name):
    model = getattr(models, model_name, None)
    if not model: raise("%s not found." %model_name)

    columns_meta = _get_meta_columns(model_name)
    # find all relationships
    one_relationships = list()
    many_relationships = list()
    for r in inspect(model).relationships:
        _r = dict(key=r.key, cls=r.mapper.class_.__name__)
        _columns_meta = _get_meta_columns(_r['cls'])
        _r.update(meta=_columns_meta)
        if 'TOONE' in r.direction.name:
            one_relationships.append(_r)
            continue
        many_relationships.append(_r) # relationship name

    return dict(columns=columns_meta, one_relationships=one_relationships,
            many_relationships=many_relationships)


def _get_meta_columns(model_name):
    model = getattr(models, model_name, None)
    meta = list()
    cols = [c for c in model.__table__.columns]
    for col in cols:
        # if col.name == 'id': continue

        if isinstance(col.type, sa.types.String):
            _meta = dict(col=col,
                        sort=True,
                        render_macro_fn=None,
                        filters=dict(key="%s_like" % col.name, macro_fn='filter_text' ))
        if isinstance(col.type, sa.types.Unicode):
            _meta = dict(col=col,
                        sort=True,
                        render_macro_fn=None,
                        filters=dict(key="%s_like" % col.name, macro_fn='filter_text' ))
        elif isinstance(col.type, sa.types.Integer):
            # TODO
            _meta = dict(col=col,
                        sort=True,
                        render_macro_fn=None,
                        filters=dict(key="%s_eq" % col.name, macro_fn='filter_id' ))
        elif isinstance(col.type, sa.types.DateTime):
            _meta = dict(col=col,
                        sort=True,
                        render_macro_fn=None,
                        filters=dict(key=col.name, macro_fn='filter_date' ))
        elif isinstance(col.type, sa.types.DECIMAL):
            # TODO
            _meta = dict(col=col,
                        sort=True,
                        render_macro_fn=None,
                        filters=dict(key="%s_eq" % col.name, macro_fn='filter_id' ))
        elif isinstance(col.type, sa.types.Text):
            _meta = dict(col=col,
                        sort=False,
                        render_macro_fn=None,
                        filters=dict(key="%s_like" % col.name, macro_fn='filter_text' ))
        elif isinstance(col.type, sa.types.Boolean):
            _meta = dict(col=col,
                        sort=False,
                        render_macro_fn='render_boolean_value',
                        filters=dict(key=col.name, macro_fn='filter_boolean' ))
        elif isinstance(col.type, sa.types.Date):
            _meta = dict(col=col,
                        sort=True,
                        render_macro_fn=None,
                        filters=dict(key=col.name, macro_fn='filter_date' ))
        elif isinstance(col.type, sa.types.Time):
            # TODO
            _meta = dict(col=col,
                        sort=True,
                        render_macro_fn=None,
                        filters=dict(key=col.name, macro_fn='filter_date' ))
        elif isinstance(col.type, sa.types.Float):
            # TODO
            _meta = dict(col=col,
                        sort=True,
                        render_macro_fn=None,
                        filters=dict(key="%s_eq" % col.name, macro_fn='filter_id' ))
        elif isinstance(col.type, sa.types.JSON):
            # TODO
            _meta = dict(col=col,
                        sort=False,
                        render_macro_fn=None,
                        filters=dict(key="%s_like" % col.name, macro_fn='filter_text' ))

        meta.append(_meta)

    return meta
