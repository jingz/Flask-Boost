from datetime import datetime


class ActiveRecordMixin(object):

    @classmethod
    def columns(cls):
        """
            all columns of this models
        """
        return { col.key: { 'python_type': col.type.python_type,
                            'type': str(col.type),
                            'primary_key': col.primary_key,
                            'default': col.default,
                            'nullable': col.nullable}
                for col in cls.__table__.columns } 


    @classmethod
    def all(cls):
        """ return all records """
        return cls.query.all()


    @classmethod
    def first(cls):
        """ return all records """
        return cls.query.first()


    @classmethod
    def last(cls):
        """ return all records """
        return cls.query.order_by(cls.id.desc()).first()


    @classmethod
    def find(cls, **kwargs):
        """ find a record that match given params in dict
            return an instant
            ex.
            User.find({ 'name': 'John' }) # <User #John>
        """
        return cls.query.filter_by(**kwargs).first()


    @classmethod
    def find_all(cls, **kwargs):
        """ find records that match given params in dict
            return array of instants
            ex.
            User.find_all({ 'name': 'John' }) # [<User #John Doe>, <User #John Die>
        """
        return cls.query.filter_by(**kwargs).all()


    @classmethod
    def create(cls, **kwargs):
        """ save attrs:dict to database
            ex.
            User.create(dict(firstname='example', lastname='example'))
            #=> return user's instance
        """
        item = cls(**kwargs)
        db.session.add(item)
        db.session.commit()
        return item


    @classmethod
    def new(cls, **kwargs):
        """ new model instance without making it persistence
            inst = User.new(name='John Read')
            inst.name = 'Read John' # update name later
        """
        return cls(**kwargs)


    @classmethod
    def get_or_create(cls, **kwargs):
        """ find record that match given params in dict
            if the record was found return it if not
            create new and return
            User.get_or_create({ 'name': 'John' }) # <User #John>
        """
        item = cls.query.filter_by(**kwargs).first()
        if not item:
            item = cls(**kwargs)
            db.session.add(item)
            db.session.commit()
        return item

    def save(self, **kwargs):
        """ save attrs:dict to database
            ex.
            inst.save(dict(firstname='example', lastname='example'))
            #=> return inst # it retrun itself
        """
        column_names = self.__class__.columns().keys()
        for attr, value in kwargs.iteritems():
            if attr in column_names:
                self.__setattr__(attr, value)
            else:
                raise KeyError("%s is not attributes of %s" %(attr, self.__class__))

        if getattr(self, 'updated_at'):
            self.updated_at = datetime.now()

        db.session.add(self)
        db.session.commit()
        return self


    def destroy(self):
        """ delete the record from database
            ex.
            inst.destroy()
            #=> return true if success
            #=> return false if fail
        """
        db.session.delete(self)
        db.session.commit()
        return True


    def attributes(self):
        """ return all colums with its values in dict format
            ex. 
            inst.attributes() #=> { firsname: 'John', lastname: 'Doe' }
        """
        return { k: getattr(self, k) for k in self.__class__.columns().keys() }


    def update_attributes(self, attrs):
        """ return all colums with its values in dict format
            ex. 
            inst.attributes() #=> { firsname: 'John', lastname: 'Doe' }
        """
        try:
            _dict = self.extract_request(attrs)
            for key in _dict:
                setattr(self, key, _dict[key])
            db.session.add(self)
            db.session.commit()
        except Exception as e:
            print(e)


    def extract_request(self, attrs):
        """ return all colums with its values in dict format
            ex. 
            inst.attributes() #=> { firsname: 'John', lastname: 'Doe' }
        """
        try:
            _base = self.attributes()
            _new_dict = {}
            for key in attrs:
                if key in _base:
                    _new_dict[key] = attrs[key]
            return _new_dict
        except Exception as e:
            print(e)
