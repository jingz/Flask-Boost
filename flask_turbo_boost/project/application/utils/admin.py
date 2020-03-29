import datetime, re
from flask import g, abort, request
from functools import wraps


def convert_params_for_search_format(model):
    params = request.args.to_dict()
    # remove page if have
    params.pop('page', None)

    search_params = params.copy()
    for k in params:
        if not params[k]: search_params.pop(k)

    for k, col_def in model.columns().items():
        value = search_params.get(k)
        if not value: continue

        ptype = col_def.get('python_type')

        if ptype is datetime.datetime or \
                ptype is datetime.date:

           dt_btw = value.split('to')
           if len(dt_btw) == 2:
               search_params.pop(k)
               search_params[k+'_gte'] = dt_btw[0].strip()
               search_params[k+'_lte'] = dt_btw[1].strip()

    return search_params, params


rexp_sort_by = re.compile("^sort_by")
def make_filter_params():
    params = request.args.to_dict()
    params.pop('page', None)
    filter_params = params.copy()
    # for k in params:
    #     # remove empty value
    #     if not params[k]: filter_params.pop(k)
    #     # remove sort_by keys
    #     if rexp_sort_by.match(k):
    #         sort_factors = filter_params.get(k).split('_')
    #         direction = sort_factors[0]
    #         if len(sort_factors) == 2:
    #             priority = sort_factors[1]
    #         else:
    #             priority = '1'

    #         if direction == 'asc':
    #             filter_params[k] = 'desc_' + priority
    #         else:
    #             filter_params[k] = 'asc_' + priority

    # current_app.logger.debug(filter_params)
    return filter_params


def admin_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if g.user and g.user.is_admin:
            return func(*args, **kwargs)
        else:
            return abort(403)
    return wrapper


def pagination(q, page, page_size=20):
    total = q.count()
    page = int(page)
    offset = page_size * (page - 1)

    q = q.offset(offset).limit(page_size)

    has_next = (page * page_size) < total
    has_prev = page > 1
    end = offset + page_size if has_next else total
    return q, dict( page=page,
                    start=offset + 1,
                    end=end,
                    has_next=has_next,
                    next_page=(page + 1 if has_next else None),
                    has_prev=has_prev,
                    prev_page=(page - 1 if has_prev else None),
                    per_page=page_size,
                    total=total )
