FROM frolvlad/alpine-python3

RUN mkdir -p /usr/src/app

WORKDIR /usr/src/app
COPY requirements.txt .
# RUN pip install --upgrade pip
# RUN pip install -r requirements.txt
RUN apk update && \
    apk add postgresql-libs python3-dev && \
    apk add --virtual .build-deps gcc musl-dev postgresql-dev && \
    pip install -r requirements.txt --no-cache-dir && \
    apk --purge del .build-deps


EXPOSE 5008

CMD ["python3", "manage.py", "run"]
