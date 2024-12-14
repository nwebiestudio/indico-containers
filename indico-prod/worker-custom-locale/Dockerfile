FROM python:3.12-bookworm AS builder

ENV INDICO_VIRTUALENV="/opt/indico/.venv"
ARG tx_locales="ru_RU" \
    tag="latest" \
    pip="${INDICO_VIRTUALENV}/bin/pip"

SHELL ["/bin/bash", "-exo", "pipefail", "-c"]
# Install build dependencies
RUN apt-get update && \
    apt-get -y install libxslt1-dev libxml2-dev libffi-dev libpcre3-dev \
    libyaml-dev build-essential redis-server postgresql libpq-dev libpango1.0-dev python3-pip \
    python3-dev nodejs npm python3-venv libjpeg62-turbo-dev git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install transifex CLI
WORKDIR /bin
RUN curl https://raw.githubusercontent.com/transifex/cli/master/install.sh | bash

# Clone indico repo
RUN git clone --depth 1 --branch ${tag} \
    https://github.com/indico/indico.git /opt/indico/src

WORKDIR /opt/indico/src
RUN python -m venv ${INDICO_VIRTUALENV} && \
    ${pip} install -U --no-cache-dir pip setuptools wheel && \
    ${pip} install --no-cache-dir -e '.[dev]'
ENV PATH="${INDICO_VIRTUALENV}/bin:$PATH"
RUN --mount=type=secret,id=tx_token,env=TX_TOKEN \
    npm ci && \
    ${INDICO_VIRTUALENV}/bin/indico i18n pull indico ${tx_locales} && \
    ${INDICO_VIRTUALENV}/bin/indico i18n check-format-strings && \
    ${INDICO_VIRTUALENV}/bin/indico i18n compile indico && \
    ./bin/maintenance/update_moment_locales.py && \
    ./bin/maintenance/build-wheel.py indico --ignore-unclean && \
    chmod 755 -R dist

FROM python:3.12-bookworm

ENV INDICO_VIRTUALENV="/opt/indico/.venv" \
    INDICO_CONFIG="/opt/indico/etc/indico.conf"

ARG pip="${INDICO_VIRTUALENV}/bin/pip" \
    tag="latest"

# create indico user, install apt dependencies as root and setup uwsgi etc.
USER root

SHELL ["/bin/bash", "-exo", "pipefail", "-c"]
RUN groupadd -r indico && \
    useradd -r -g indico -m -d /opt/indico indico

RUN apt-get update && \
    apt-get -y install --no-install-recommends texlive-xetex libpq-dev \
    postgresql-client vim less gcc gettext libldap2-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*


COPY uwsgi.ini /etc/uwsgi.ini
WORKDIR /opt/indico

RUN mkdir -p --mode=750 /opt/indico/etc && \
    mkdir -p --mode=777 /opt/indico/tmp && \
    mkdir -p --mode=750 /opt/indico/log && \
    mkdir -p --mode=750 /opt/indico/cache && \
    mkdir -p --mode=750 /opt/indico/archive && \
    chown -R indico:indico /opt/indico

# XXX do we still need this?
RUN chmod g=u /etc/passwd

# all the installations etc can be done using the unprivileged indico user
USER indico

RUN python -m venv ${INDICO_VIRTUALENV} && \
    ${pip} install --no-cache-dir --upgrade pip setuptools wheel && \
    ${pip} install --no-cache-dir uwsgi


RUN --mount=type=bind,from=builder,source=/opt/indico/src/dist,destination=/tmp/indico/dist \
    ${pip} install --no-cache-dir /tmp/indico/dist/indico-*.whl && \
    ${pip} install --no-cache-dir indico-plugins

RUN ${INDICO_VIRTUALENV}/bin/indico setup create-symlinks /opt/indico

COPY --chown=indico:indico run_indico.sh run_celery.sh docker_entrypoint.sh /opt/indico/
RUN chmod 755 /opt/indico/*.sh

ENTRYPOINT ["/opt/indico/docker_entrypoint.sh"]
EXPOSE 59999
