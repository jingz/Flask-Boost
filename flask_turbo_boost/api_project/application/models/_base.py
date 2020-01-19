from flask_sqlalchemy import SQLAlchemy
from flask_sqlalchemy.model import Model
from application.extensions.searchable_mixin import SearchableMixin
from application.extensions.active_record_mixin import ActiveRecordMixin


class BaseModelMixin(Model, ActiveRecordMixin, SearchableMixin):
    pass


db = SQLAlchemy(model_class=BaseModelMixin)
