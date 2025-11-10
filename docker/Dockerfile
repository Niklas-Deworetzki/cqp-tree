FROM python:3.13

RUN pip install gunicorn cqp-tree==0.1a1

ENTRYPOINT ["gunicorn", "cqp_tree.web.server:server", "--bind", "0.0.0.0:8000"]

EXPOSE 8000
