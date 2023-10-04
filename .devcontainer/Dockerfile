FROM python:3.11-bookworm

ARG USERNAME="nonroot"
ARG USER_UID=1000
ARG USER_GID=1000

WORKDIR /code
COPY . .

ENV PYTHONPATH=$PYTHONPATH:/code/src

RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME

RUN pip install -r requirements.txt

USER $USERNAME
