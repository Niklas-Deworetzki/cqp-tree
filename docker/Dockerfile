FROM python:3.14

ARG VERSION="clarin-integration"

RUN git clone https://github.com/Niklas-Deworetzki/cqp-tree.git \
    cqp-tree \
    --branch=${VERSION}
WORKDIR cqp-tree

RUN pip install -e .

ENTRYPOINT ["cqp-tree-web", "--host", "0.0.0.0", "--port", "8000"]

EXPOSE 8000
