FROM python:3.13

RUN pip install gunicorn
RUN pip install git+https://github.com/Niklas-Deworetzki/cqp-tree.git@demo

ENTRYPOINT ["gunicorn", "cqp_tree.web.server:server", "--bind", "0.0.0.0:8000"]

EXPOSE 8000
