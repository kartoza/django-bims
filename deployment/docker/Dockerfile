#--------- Generic stuff all our Dockerfiles should start with so we get caching ------------
FROM python:3.12.3-slim-bookworm as prod
MAINTAINER Dimas Ciputra <dimas@kartoza.com>

# Set up directories
RUN mkdir -p /usr/src/{app,geonode}
WORKDIR /usr/src/app

# Install system dependencies
ARG TIPPECANOE_VERSION=2.79.0
RUN echo "Updating apt-get" && \
    apt-get update && \
    echo "Installing build dependencies" && \
    apt-get install -y --no-install-recommends \
      nodejs npm \
      gcc g++ make \
      libc-dev musl-dev libpcre3 libpcre3-dev \
      libgdal-dev gdal-bin \
      libcurl4-gnutls-dev librtmp-dev curl git ca-certificates \
      # Tippecanoe deps
      libprotobuf-dev protobuf-compiler zlib1g-dev libsqlite3-dev \
      # psycopg2 deps (pg_config provider + runtime lib)
      libpq-dev libpq5 && \
    echo "Installing Tippecanoe ${TIPPECANOE_VERSION}" && \
    git clone --depth 1 --branch "${TIPPECANOE_VERSION}" https://github.com/felt/tippecanoe.git /tmp/tippecanoe && \
    make -C /tmp/tippecanoe -j"$(nproc)" && make -C /tmp/tippecanoe install && \
    tippecanoe --version && \
    cd /usr/src/app && \
    echo "Python server" && \
    pip install --no-cache-dir uwsgi

# Add application requirements (do this while libpq-dev is still installed)
COPY deployment/docker/REQUIREMENTS.txt /REQUIREMENTS.txt
# Ensure pg_config is available, then install requirements
RUN which pg_config && pg_config --version && \
    pip install --no-cache-dir -r /REQUIREMENTS.txt

# NOW it's safe to remove build-only deps (keep libpq5)
RUN echo "Removing build dependencies and cleaning up" && \
    apt-get -y --purge autoremove \
      make g++ libpcre3-dev libprotobuf-dev protobuf-compiler zlib1g-dev libsqlite3-dev libpq-dev && \
    rm -rf /var/lib/apt/lists/* /tmp/tippecanoe && \
    rm -rf ~/.cache/pip

# Add and install Node.js dependencies
RUN npm --quiet -g install yuglify && npm install -g grunt-cli
COPY deployment/docker/package.json /package.json
COPY deployment/docker/Gruntfile.js /Gruntfile.js
RUN npm install

# Add application source code
COPY . /home/web/django_project
WORKDIR /home/web/django_project

# Install front-end build tools and run webpack
RUN cd bims && npm install --quiet -g webpack@5.50.0 webpack-cli@4.8.0 && npm install --quiet && webpack --mode production

# Add uWSGI configuration
COPY deployment/docker/uwsgi.conf /uwsgi.conf

# Expose port 8080 for uWSGI
EXPOSE 8080

# Add and set entrypoint script
COPY deployment/docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ARG APP_USER=bims
ARG APP_UID=1001
ARG APP_GID=1001

RUN groupadd --gid ${APP_GID} ${APP_USER} \
 && useradd  --uid ${APP_UID} --gid ${APP_GID} \
             --create-home --shell /bin/bash ${APP_USER} \
 && mkdir -p /var/log \
 && chown -R ${APP_USER}:${APP_USER} /home/web /var/log /usr/src/app

USER ${APP_USER}

ENTRYPOINT ["/entrypoint.sh"]
CMD ["uwsgi", "--ini", "/uwsgi.conf"]

FROM prod as dev

USER root

RUN apt-get update && apt-get install -y openssh-server sudo
RUN mkdir /var/run/sshd
RUN echo 'root:docker' | chpasswd
RUN echo "PermitRootLogin yes" >> /etc/ssh/sshd_config
RUN sed 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' -i /etc/pam.d/sshd
ENV NOTVISIBLE "in users profile"
RUN echo "export VISIBLE=now" >> /etc/profile

ADD deployment/docker/REQUIREMENTS-dev.txt /REQUIREMENTS-dev.txt
RUN pip install -r /REQUIREMENTS-dev.txt
ADD bashrc /root/.bashrc

RUN apt-get install -y chromium
RUN mkdir -p /opt/karma
RUN npm install -g karma
RUN cd / && npm install

RUN apt-get install -y vim
ADD karma.conf.docker.js /karma.conf.js

EXPOSE 8080
EXPOSE 22

CMD ["/usr/sbin/sshd", "-D"]