FROM python:3.12

RUN pip install cqp-tree gunicorn

ENTRYPOINT ["gunicorn", "cqp_tree.web.app:app", "--bind", "0.0.0.0:8000"]

EXPOSE 8000
