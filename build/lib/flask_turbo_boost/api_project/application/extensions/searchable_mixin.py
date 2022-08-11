from sqlalchemy import sql
import re

try:
      basestring
except NameError:
      basestring = str

# Enhance Front-End-Like search API for SQLAlchemy Model
class SearchableMixin(object):

    @classmethod
    def search(cls, di, sel=[]):
        """
            SPECS
            SQL         Predication
            =====       ===========
            =           eq
            !=          not_eq 
            LIKE        like
            NOT LIKE    not_like
            <           lt
            >           gt
            <=          lte
            >=          gte
            in          in
            not_in      not_in

        example given "di" is dict argument : { 'name_like': 'jing' }
            generate where clause : name like '%jing%'

            User.search({'name_like': 'sarunyoo'}) will return User's db session

        return raw session scoped by the class
        """
        filter_clause, filter_params = cls._build_search_clause(di)
        sort_ = sql.text(cls._build_sort_clause(di))
        filter_clause = sql.text(filter_clause)
        if len(sel) == 0:
            return cls.query.filter(filter_clause).\
                       params(**filter_params).order_by(sort_)
        else:
            return cls.query.session.query(*sel).filter(filter_clause).\
                       params(**filter_params).order_by(sort_)


    SEARCH_OPT_REGEXP = r'(((?<!not)_eq)|(_not_eq)|((?<!not)_like)|(_not_like)|((?<!not)_contains)|(_not_contains)|(_lt)|(_gt)|(_lte)|(_gte)|((?<!not)_in)|(_not_in))$'
    SEARCH_OPT_MAPPER = {
        'eq': '=',
        'not_eq': '<>',
        'like': 'like',
        'contains': 'like',
        'not_like': 'not like',
        'not_contains': 'not like',
        'lt': '<',
        'gt': '>',
        'gte': '>=',
        'lte': '<=',
        'in': 'in',
        'not_in': 'not in',
    }

    SEARCH_OPT_TEXT_MAPPER = {
        'eq': 'equal to',
        'not_eq': 'not equal to',
        'like': 'contains',
        'contains': 'contains',
        'not_like': 'not contains',
        'not_contains': 'not contains',
        'lt': 'less than',
        'gt': 'greater than',
        'gte': 'greater than and equal to',
        'lte': 'less than and equal to',
        'in': 'in any',
        'not_in': 'not in any',
    }


    @classmethod
    def explain_search_clause(cls, di, transform_key=True):
        text = []
        for k, v in di.items():
            col, opt = cls._grep_search_opt(k)
            if col and opt:
                read_pattern = u"{col} {text_opt} {v}" 
                to = cls.SEARCH_OPT_TEXT_MAPPER.get(opt)
                _col = col
                if transform_key:
                    _col = _col.title().replace('_', ' ')
                text.append(read_pattern.format(col=_col, text_opt=to, v=v))
        return u" and ".join(text)


    @classmethod
    def _build_search_clause(cls, di):
        filter_clause = []
        filter_params = {}
        for k, v in di.items():
            col, opt = cls._grep_search_opt(k)
            if col and opt:
                __where = "%s.{col} {opt} :{column_param}" % cls.__tablename__
                sql_opt = cls.SEARCH_OPT_MAPPER.get(opt)

                if opt in ('like', 'not_like', 'contains', 'not_contains'):
                    # wrap value with '%' 
                    if isinstance(v, basestring):
                        if re.match('^%.*', v) or re.match('.*%$', v):
                            pass
                        else:
                            v = u"%{0}%".format(v)

                if opt == 'in' or opt == 'not_in':
                    # in is a special case to
                    # serialize value and key into where statement
                    in_params_series = [] # :column_name_key_1 ...
                    n = len(v)
                    i = 1
                    while n != 0:
                        _k = ":%s_%d" % (k, i)
                        in_params_series.append(_k)
                        # set binding params
                        filter_params.setdefault(_k[1:], v[i-1])
                        i += 1
                        n -= 1
                        
                    __where = u"{col} {opt} (%s)" % ", ".join(in_params_series)
                    filter_text = __where.format(col=col, opt=sql_opt)
                    filter_clause.append(filter_text)
                    continue

                if sql_opt is not None:
                    filter_text = __where.format(col=col, opt=sql_opt, column_param=k)
                    filter_clause.append(filter_text)
                    filter_params.setdefault(k, v)
                else:
                    continue
            else:
                continue

        filter_clause = " and ".join(filter_clause)
        return (filter_clause, filter_params)


    @classmethod
    def _grep_search_opt(cls, text):
        match = re.search(cls.SEARCH_OPT_REGEXP, text);
        if match is not None:
            col, _ = text.split(match.group(0)) # client_code, ''
            opt = match.group(0)[1:] # remove a leading _ 
            # match but the matched column is not in mapper
            if col not in [__col.name for __col in cls.__mapper__.c]:
                col = opt = None
        # could be just column name
        elif text in [__col.name for __col in cls.__mapper__.c]:
            col = text
            opt = 'eq'
        else:
            col = opt = None
        return (col, opt)


    @classmethod
    def _build_sort_clause(cls, di):
        orders = []
        for k, v in di.items():
            col, direction, priority = cls._grep_sort_opt(k, v)
            if col is not None:
                orders.append({ 'column': col, 'direction': direction,
                    'priority': priority})

        # sort order by priority
        if len(orders) > 0:
            proc = lambda k: k['priority']
            order_pattern = u"%s.{column} {direction}" % cls.__tablename__
            return ", ".join([order_pattern.format(**d) for d in sorted(orders, key=proc)]) 
        else:
            return ""


    SORT_KEY_REGEXP = r'^sort_by_(.*)'
    SORT_VALUE_REGEXP = r'(asc|desc)_?((?<=)\d+)?' # asc_1

    @classmethod
    def _grep_sort_opt(cls, key_text, value_text):
        match_key = re.search(cls.SORT_KEY_REGEXP, key_text)
        match_val = re.search(cls.SORT_VALUE_REGEXP, value_text, re.IGNORECASE)
        if match_key is not None and match_val is not None:
            col = match_key.group(1) # client_code
            collate = False
            if col.startswith('$'):
                collate = True
                col = col[1:]

            direction, priority = match_val.group(1), match_val.group(2)
            if direction is None: 
                direction = "ASC"
            
            if collate:
                direction = ("COLLATE NOCASE %s" % direction)

            if priority is None:
                priority = 99
            else:
                priority = int(priority)

            # match but the matched column is not in mapper
            if col not in [__col.name for __col in cls.__mapper__.c]:
                col = direction = priority = None
        else:
            col = direction = priority = None

        return (col, direction, priority)
