import os
import re
import yaml
from copy import deepcopy
from sqlalchemy import Table, Column, Integer, String, Float, ForeignKey, MetaData, DateTime, Boolean, Date
from sqlalchemy import Unicode
from flask_script import Command, Manager, Option
from flask import current_app
from application.models import db

#Example of table_info
"""
{
    description: "TEST TEST",
    name: table_a,
    fields: [
        {
            name: id,
            type: Integer,
            primary: True,
        },
        {
            name: name,
            type: String,
            size: 10,
            index: True,
            unique: True,
            order: {
                seq: 1,
                desc: False,
            }
        },
        {
            name: age,
            type: Integer,
            default: 1,
        },
        {
            name: salary,
            type: Float,
            default: 0,
        },
        {
            name: title_id,
            type: ForeignKey,
            table: title,
            field: id,
            null: False,
        },
        {
            name: created_at,
            type: DateTime,
            size: 3,
            onupdate: datetime.datetime.now,
        }
    ]
}
"""

#---------------------------------------------
#Example of yaml file

yml_example = """
models:
    -   name: Person
        fields:
            -   name: id
                type: Integer
                primary: true

            -   name: name
                type: String
                size: 64
                index: true
                repr: true
                criteria: True  # True, =, >, <, >=, <=, in, exclude, between

            -   name: email
                type: String
                size: 64
                unique: true

            -   name: active
                type: Boolean
                default: true
                null: false

            -   name: created_at
                type: DateTime
                default: datetime.datetime.now
                format: '%Y-%m-%d %M:%H:%S.%f'
                repr: true
                order:
                    desc: True
                    seq: 0

            -   name: updated_at
                type: DateTime
                default: datetime.datetime.now
                onupdate: datetime.datetime.now
                format: '%Y-%m-%d %M:%H:%S.%f'
                repr: true

    -   name: Address
        fields:
            -   name:   id
                type: Integer
                primary: true

            -   name: addr1
                type: String
                size: 64

            -   name: addr2
                type: String
                size: 64

            -   name: city
                type: String
                size: 64

            -   name: zip
                type: String
                size: 16

            -   name: person
                type: ForeignKey
                table: Person
                field: id
"""

ModelTemplate = [
    "# encoding: utf-8",
    "",
    "from {db_module} import db",
    "",
    "",
    "class {model_name}(db.Model):",
    "{indent}# Fields",
    "",
    "{indent}def __repr__(self):",
    "{indent}{indent}return '<{model_name} {repr_display}>' %{repr_params}",
]

ControllerTemplate = [
    "# encoding: utf-8",
    "",
    "from copy import deepcopy",
    "import datetime",
    "from flask import request, Blueprint, jsonify, g",
    "from flask import current_app as app",
    "from {model_module}.{model_file} import {model}",
    "from {model_module} import db",
    "",
    "",
    "bp = Blueprint('{blueprint}', __name__ , {url_prefix})",
    "",
    "",
    "@bp.route('/', methods=['GET'])",
    "def list():",
    "{indent}_limit  = request.args.get('_limit', 10)",
    "{indent}_offset = request.args.get('_offset', 0)",
    "",
    "{indent}l = {model}.query",
    "{grasp_filters}",
    "{indent}c = l.count()",
    "{indent}l = l.{order}limit(_limit).offset(_offset).all()",
    "{indent}ll = []",
    "{indent}for o in l:",
    "{indent}{indent}d = dict( (c.name, str(getattr(o, c.name))) for c in o.__table__.columns )",
    "{indent}{indent}ll.append(d)",
    "{indent}return jsonify(dict(data=ll,count=c))",
    "",
    "",
    "@bp.route('/<{table}_id>', methods=['GET'])",
    "def show({table}_id):",
    "{indent}o = {model}.query.filter_by(id={table}_id).first()",
    "{indent}d = dict()",
    "{indent}if o:",
    "{indent}{indent}d = dict( (c.name, str(getattr(o, c.name))) for c in o.__table__.columns )",
    "{indent}return jsonify(dict(data=d))",
    "",
    "",
    "@bp.route('/', methods=['POST'])",
    "def create():",
    "{indent}try:",
    "{indent}{indent}d = request.json.get('data')",
    "{indent}{indent}o = {model}(**d)",
    "{indent}{indent}db.session.add(o)",
    "{indent}{indent}db.session.commit()",
    "{indent}{indent}d = dict( (c.name, str(getattr(o, c.name))) for c in o.__table__.columns )",
    "{indent}{indent}return jsonify(dict(data=d, success=True)), 201",
    "{indent}except Exception as e:",
    "{indent}{indent}db.session.rollback()",
    "{indent}{indent}return jsonify(dict(message=e.message, success=False))",
    "",
    "",
    "@bp.route('/<{table}_id>', methods=['PUT'])",
    "def update({table}_id):",
    "{indent}try:",
    "{indent}{indent}d = request.json.get('data')",
    "{indent}{indent}o = {model}.query.filter_by(id={table}_id).first()",
    "{indent}{indent}od = dict( (c.name, str(getattr(o, c.name))) for c in o.__table__.columns )",
    "{indent}{indent}for k in d:",
    "{indent}{indent}{indent}if k in od:",
    "{indent}{indent}{indent}{indent}setattr(o, k, d[k])",
    "{indent}{indent}db.session.commit()",
    "{indent}{indent}d = dict( (c.name, str(getattr(o, c.name))) for c in o.__table__.columns )",
    "{indent}{indent}return jsonify(dict(data=d, success=True))",
    "{indent}except Exception as e:",
    "{indent}{indent}db.session.rollback()",
    "{indent}{indent}return jsonify(dict(message=e.message, success=False))",
    "",
    "",
    "@bp.route('/<{table}_id>', methods=['DELETE'])",
    "def delete({table}_id):",
    "{indent}try:",
    "{indent}{indent}o = {model}.query.filter_by(id={table}_id).first()",
    "{indent}{indent}db.session.delete(o)",
    "{indent}{indent}db.session.commit()",
    "{indent}{indent}return jsonify(dict(success=True))",
    "{indent}except Exception as e:",
    "{indent}{indent}db.session.rollback()",
    "{indent}{indent}return jsonify(dict(message=e.message, success=False))",
]

CriteriaOperator = {
    '=': '=',
    '>': '>',
    '>=': '>=',
    '<': '<',
    '<=': '<=',
    'in': 'in',
    'between': 'between',
}

TypeMapping = {
    'integer': Integer,
    'string': String,
    'unicode': Unicode,
    'float': Float,
    'foreignkey': ForeignKey,
    'date': DateTime,
    'datetime': DateTime,
    'boolean': Boolean,
}

ReverseTypeMapping = {
    Integer: 'Integer',
    String: 'String',
    Unicode: 'Unicode',
    Float: 'Float',
    ForeignKey: 'ForeignKey',
    DateTime: 'DateTime',
    Date: 'Date',
    Boolean: 'Boolean',
}

PythonTypeMapping = {
    'integer': 'int',
    'string': 'str',
    'unicode': 'unicode',
    'float': 'float',
    'foreignkey': 'int',
    'date': 'date',
    'datetime': 'datetime',
    'boolean': 'bool',
}

class DBUtilsException(Exception):
    pass


_underscorer1 = re.compile(r'(.)([A-Z][a-z]+)')
_underscorer2 = re.compile('([a-z0-9])([A-Z])')

def camel_to_snake(s):
    """ 
    Is it ironic that this function is written in camel case, yet it
    converts to snake case? hmm..
    """
    subbed = _underscorer1.sub(r'\1_\2', s)
    return _underscorer2.sub(r'\1_\2', subbed).lower()

def build_table(table_info, engine=None):
    columns = []
    for c in table_info.get('fields'):
        t = TypeMapping[c['type'].lower()]
        pk = c.get('primary', False)
        index = c.get('index', False)
        unique = c.get('unique', False)
        default = c.get('default', None)
        null = c.get('null', True)

        attrs = {}
        if pk: attrs['primary_key'] = pk
        if index: attrs['index'] = index
        if unique: attrs['unique'] = unique
        if default: attrs['default'] = default
        if not null: attrs['nullable'] = False

        if t == ForeignKey:
            ref = "{table}.{field}".format(**c)
            columns.append(Column(c['name'], Integer, ForeignKey(ref), **attrs))
        else:
            size = c.get('size')
            if size:
                if t not in [String, Unicode, DateTime]:
                    raise DBUtilsException("Field %s cannot have size subscription" %c['type'])
                size = int(size)
                columns.append(Column(c['name'], t(size), **attrs))
            else:
                columns.append(Column(c['name'], t, **attrs))

    metadata = MetaData()
    table = Table(table_info['name'], metadata, *columns)
    if engine:
        table.create(engine)
    return table

def scaffold_field(model, field_info, indent=" "*4):
    imports = []

    n = field_info.get('name')
    if not n: return None
    properties = []

    t = field_info.get('type', 'Integer')
    if not t: return None

    link = None
    if t.lower() == 'foreignkey':
        m = field_info.get('table')
        f = field_info.get('field')
        if not m or not f: return None
        properties.append("db.Integer")
        foreign_name = camel_to_snake(m)
        link_name = camel_to_snake(model)
        properties.append("db.ForeignKey('{table}.{field}')".format(table=foreign_name,field=f))

        # n has been overrided here
        old_name = n
        n = '_'.join([old_name, f])
        backref = old_name + '_' + link_name

        link = "{indent}{link} = db.relationship('{model}', backref = '{backref}s')".format(indent=indent,backref=backref,model=m,link=old_name)
    else:
        s = field_info.get('size')
        if s: s = "({0})".format(s)
        else: s = ""
        properties.append("db.{type}{size}".format(type=t,size=s))

        p = field_info.get('primary')
        if p: properties.append("primary_key = True")

        if not p:
            i = field_info.get('index')
            if i: properties.append("index = True")

            u = field_info.get('unique')
            if u: properties.append("unique = True")

            null = field_info.get('null')
            if null == False:
                properties.append("nullable = False")

        d = field_info.get('default')
        if d and t.lower() in ['string', 'unicode']:
            d = "'{0}'".format(d)
        if d is not None:
            properties.append("default = {default}".format(default=d))
            if t.lower() in ['datetime', 'date']:
                l = d.split('.')
                if len(l) > 1:
                    imports.append(l[0])

        o = field_info.get('onupdate')
        if o:
            properties.append("onupdate = {onupdate}".format(onupdate=o))
            l = o.split('.')
            if len(l) > 1:
                imports.append(l[0])
        

    pps = ', '.join(properties)
    s = "{indent}{name} =  db.Column({properties})".format(indent=indent, name=n, properties=pps)
    if link is not None:
        s = "\n"+s+"\n"+link+"\n"
    return s, imports
        
    
def scaffold_model(table_info, db_from='._base', indent=" "*4):
    db_module = db_from
    model_name = table_info.get('name', 'unknown').strip()
    repr_display = []
    repr_params = []

    repr_fields = [f['name'] for f in table_info['fields'] if 'repr' in f and f['repr']]
    if repr_fields:
        for f in repr_fields:
            repr_display.append("{0} = %s".format(f))
            repr_params.append("self.{0}".format(f))
        repr_display = ", ".join(repr_display)
        repr_params = "(" + ", ".join(repr_params) + ")"
    else:
        repr_display = "%s"
        repr_params = "self.id"
        
    imports = []
    fields = []
    for f in table_info['fields']:
        s, imp = scaffold_field(model_name, f, indent)
        imports.extend(imp)
        if s: fields.append(s)

    model_template = deepcopy(ModelTemplate)
    model_template[7:7] = fields

    desc = table_info.get('description', 'Describe model here!!!')
    model_template[5:5] = ["'''", desc, "'''"]

    imports = ["import {0}".format(i) for i in set(imports)]
    model_template[2:2] = imports

    model_str = "\n".join(model_template).format(
        db_module = db_module,
        model_name = model_name,
        indent = " "*4,
        model_info = "",
        repr_display = repr_display,
        repr_params = repr_params,
    )

    return model_str

def gen_model_file(table_info, prefix_path='application', model_folder='models', db_from='._base', indent=" "*4):
    try:
        os.makedirs(os.path.join(prefix_path, model_folder))
    except OSError:
        # leaf folder already existed
        pass
    except:
        # Unexpected error
        raise DBUtilsException("Cannot make path for model")

    s = scaffold_model(table_info, db_from=db_from, indent=indent)
    fname = os.path.join(prefix_path, model_folder, "%s.py" %camel_to_snake(table_info.get('name')))
    f = open(fname, 'w')
    f.write(s)
    f.close()

def resolve_rvar(varname, vartype, varformat=None, criteria=None):

    element_template = "{element}.strip()"
    if vartype == 'datetime':
        if varformat == None: varformat = '%Y-%M-%d %H:%M:%S.%f'
        element_template = "datetime.strptime({element}, '%s')" %varformat
    if vartype == 'date':
        if varformat == None: varformat = '%Y-%M-%d'
        element_template = "datetime.strptime({element}, '%s')" %varformat
    if vartype == 'bool':
        element_template = "bool({element}.lower().capitalize())"
    if vartype in ['int', 'float']:
        element_template = "%s({element})" %vartype

    if criteria in ['in', 'between', 'exclude']:
        template = "[%s for {element} in {varname}.split(',')]" %element_template
        result = template.format(element='e',varname=varname)
    else:
        result = element_template.format(element=varname)
    return result

def compose_varname(varname, criteria):
    if criteria == 'in':
        return varname+"_contains"
    if criteria == 'between':
        return varname+"_betweens"
    if criteria == 'exclude':
        return varname+"_excludes"
    return varname

def compose_grasp_filter(table_info, indent):
    l = []
    model = table_info.get('name')
    
    for field in table_info['fields']:
        n = field['name']
        criteria = field.get('criteria', False)
        if not criteria: continue

        if criteria == True: criteria = '='

        var = compose_varname(n, criteria)

        l.append("{indent}{var} = request.args.get('{var}')".format(
            indent = indent,
            var = var))
        l.append("{indent}if {var} is not None:".format(indent=indent, var=var))

        t = PythonTypeMapping[field.get('type','string').lower()]
        rvar = resolve_rvar(var, t, field.get('format'), criteria)
        l.append("{indent}{indent}{var} = {rvar}".format(
            indent = indent,
            var = var,
            rvar = rvar))
        if criteria == 'in':
            l.append("{indent}{indent}l = l.filter({model}.{field}.in_({var}))".format(
                indent = indent,
                field = n,
                model = model,
                var = var))
        elif criteria == 'between':
            l.append("{indent}{indent}l = l.filter({model}.{field}>={var}[0],{model}.{field}<={var}[-1])".format(
                indent = indent,
                model = model,
                field = n,
                var = var))
        elif criteria == 'exclude':
            l.append("{indent}{indent}l = l.filter(~{model}.{field}.in_({var}))".format(
                indent = indent,
                field = n,
                model = model,
                var = var))
        else:
            if criteria is True:
                criteria = '='
            l.append("{indent}{indent}l = l.filter_by({field}{criteria}{var})".format(
                indent = indent,
                field = n,
                criteria = criteria,
                var = var))
        l.append("")

    return '\n'.join(l)
        
def compose_order_by(table_info):
    orders = []
    for f in table_info['fields']:
        if not 'order' in f or not f['order']:
            continue
        if f['order'] == True:
            orders.append( (999999, f['name'], False) )
        else:
            orders.append( (f['order'].get('seq', 999999), f['name'], f['order'].get('desc', False)) )
    #orders.sort(cmp=lambda a, b: cmp(a[0], b[0]))
    orders.sort(key=lambda x: x[0])
    l = []
    for order in orders:
        s = "{model}.{field}".format(model=table_info['name'],field=order[1])
        if order[-1]: s += ".desc()"
        l.append(s)
    if len(l) == 0:
        l.append("{model}.id".format(model=table_info['name']))
    return "order_by({0}).".format(', '.join(l))

def gen_crud_controller(table_info, prefix_path='application', controller_folder='controllers', indent=" "*4, model_module='application.models'):
    try:
        os.makedirs(os.path.join(prefix_path, controller_folder))
    except OSError:
        # leaf folder already existed
        pass
    except:
        # Unexpected error
        raise DBUtilsException("Cannot make path for controller")

    model_file  = camel_to_snake(table_info['name'])
    blueprint   = model_file + "_controller_blueprint"
    url_prefix  = "url_prefix = '/" + model_file + "'"

    grasp_filters = compose_grasp_filter(table_info, indent)
    order = compose_order_by(table_info)

    s = '\n'.join(ControllerTemplate).format(
        indent = indent,
        model_module = model_module,
        model_file = model_file,
        model = table_info['name'],
        blueprint = blueprint,
        url_prefix = url_prefix,
        table = model_file,
        grasp_filters = grasp_filters,
        order = order)

    fname = os.path.join(prefix_path, controller_folder, "%s_controller.py" %camel_to_snake(table_info.get('name')))
    f = open(fname, 'w')
    f.write(s)
    f.close()

def scaffold(table_info, application_path='application', controller_folder='controllers', model_folder='models', indent=" "*4):
    gen_model_file(table_info, application_path, model_folder, db_from='._base', indent=indent)
    gen_crud_controller(table_info, application_path, controller_folder, indent, model_module='application.models')

def scaffold_from_yaml(yml, app_path, controller_folder, model_folder):
    f = open(yml, 'r')
    meta = yaml.load(f)
    f.close()
    if 'models' in meta:
        for sect in meta['models']:
            print("\tScaffold model/controller for %s" %sect['name'])
            scaffold(sect, app_path, controller_folder, model_folder)

def reverse_model(model):
    fields = []
    for c in model.__table__.c:
        t = ReverseTypeMapping[type(c.type)]
        d = dict(
            name = c.name,
            type = t,
        )
        if t.lower() in ['string', 'unicode']:
            d['size'] = c.type.length

        if c.primary_key: d['primary'] = True
        if c.index: d['index'] = True
        if c.unique: d['unique'] = True
        if not c.nullable: d['null'] = False
        if c.default:
            if hasattr(c.default.arg, '__call__'):
                if c.default.arg.__qualname__ == 'datetime.now':
                    d['default'] = 'datetime.datetime.now'
                else:
                    d['default'] = c.default.arg.__qualname__
            else:
                d['default'] = c.default.arg
        if c.onupdate:
            if hasattr(c.onupdate.arg, '__call__'):
                if c.onupdate.arg.__qualname__ == 'datetime.now':
                    d['onupdate'] = 'datetime.datetime.now'
                else:
                    d['onupdate'] = c.onupdate.arg.__qualname__
            else:
                d['onupdate'] = c.onupdate.arg
        fields.append(d)

    return dict(
        name = model.__name__,
        fields = fields,
    )

def scaffold_from_model(model, application_path='application', controller_folder='controllers', indent=" "*4):
    table_info = reverse_model(model)
    gen_crud_controller(table_info, application_path, controller_folder, indent, model_module='application.models')

#-------------------------
#  Flask Script Section
#-------------------------
scaffold_manager = Manager(current_app, help="Scaffold model and controller from yaml format definition.")

@scaffold_manager.option("--file", "-f", dest="yml", default=None)
@scaffold_manager.option("--controller-folder", "-c", dest="controller_folder", default="controllers/api-v1")
@scaffold_manager.option("--model-folder", "-m", dest="model_folder", default="models")
def from_yml(yml, controller_folder, model_folder):
    if not yml or\
       not os.path.isfile(yml):
        print("Please specify valid yaml file.")
        return
    project_path = current_app.config.get('PROJECT_PATH', os.path.join(os.getcwd(), '..'))
    app_path     = os.path.join(project_path, 'application')
    scaffold_from_yaml(yml, app_path, controller_folder, model_folder)
    print("Complete generating scaffold from %s." %yml)


@scaffold_manager.option("--file", "-f", dest="yml", default=None)
@scaffold_manager.option("--controller-folder", "-c", dest="controller_folder", default="controllers/api-v1")
def crud_from_yml(yml, controller_folder):
    if not yml or\
       not os.path.isfile(yml):
        print("Please specify valid yaml file.")
        return
    project_path = current_app.config.get('PROJECT_PATH', os.path.join(os.getcwd(), '..'))
    app_path     = os.path.join(project_path, 'application')

    f = open(yml, 'r')
    meta = yaml.load(f)
    f.close()
    if 'models' in meta:
        for sect in meta['models']:
            print("\tScaffold controller for %s" %sect['name'])
            gen_crud_controller(sect, prefix_path=app_path, controller_folder=controller_folder, indent=" "*4, model_module='application.models')
    print("Complete generating scaffold controller from %s." %yml)


@scaffold_manager.option("--model", "-m", dest="model", default=None)
@scaffold_manager.option("--controller-folder", "-c", dest="controller_folder", default="controllers/api-v1")
def crud_from_model(model, controller_folder):
    if not model:
        print("Please specify valid model name.")
        return

    project_path = current_app.config.get('PROJECT_PATH', os.path.join(os.getcwd(), '..'))
    app_path     = os.path.join(project_path, 'application')

    module = camel_to_snake(model)
    exec("from application.models.{module} import {model}".format(module=module, model=model))
    m = eval(model)
    scaffold_from_model(m, application_path=app_path, controller_folder=controller_folder, indent=" "*4)
    print("complete generating scaffold crud from model %s." %model)


@scaffold_manager.option("--model", "-m", dest="model", default=None)
def to_yml(model):
    if not model:
        print("Please specify valid model name.")
        return

    module = camel_to_snake(model)
    exec("from application.models.{module} import {model}".format(module=module, model=model))
    m = eval(model)
    d = dict(models=[reverse_model(m)])
    print(yaml.dump(d, default_flow_style=False, indent=3))

@scaffold_manager.command
def example():
    print(yml_example)

if __name__ == '__main__':
    table_info = {
        'name': 'Test',
        'fields': [
            {
                'name': 'id',
                'type': 'Integer',
                'primary': True,
                'order': {
                    'desc': True,
                    'seq': 2,
                },
            },
            {
                'name': 'name',
                'type': 'String',
                'size': 128,
                'index': True,
                'unique': True,
                'null': False,
                'criteria': 'in',
                'order': {
                    'desc': False,
                    'seq': 0,
                },
                'repr': True,
            },
            {
                'name': 'age',
                'type': 'Integer',
                'default': 1,
                'criteria': '>=',
            },
            {
                'name': 'salary',
                'type': 'Float',
                'default': 0,
                'criteria': 'between',
            },
            {
                'name': 'title_id',
                'type': 'ForeignKey',
                'table': 'Title',
                'field': 'id',
                'criteria': 'exclude',
                'order': True
            },
            {
                'name': 'updated_at',
                'type': 'DateTime',
                'onupdate': 'datetime.datetime.now',
                'default': 'datetime.datetime.now',
                'format': '%Y-%m-%dT%H:%M:%S.%f+0700',
                'criteria': 'between',
                'order': {},
                'repr': True,
            },
            {
                'name': 'created_at',
                'type': 'DateTime',
                'default': 'datetime.datetime.now',
                'format': '%Y-%m-%dT%H:%M:%S.%f+0700',
                'criteria': 'between',
                'order': {},
                'repr': True,
            },
        ]
    }

    '''
    from sqlalchemy import create_engine
    engine = create_engine('sqlite://')
    table = build_table(table_info, engine)
    results = engine.connect().execute("select count(*) from test")
    for r in results:
        print r
    '''

    #scaffold(table_info, application_path='application', controller_folder='controllers', model_folder='models', indent=" "*4)
    #scaffold_from_yaml('workflow.yml')
