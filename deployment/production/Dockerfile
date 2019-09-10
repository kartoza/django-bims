#--------- Generic stuff all our Dockerfiles should start with so we get caching ------------
FROM dimasciput/geonode-generic:2.10
MAINTAINER Dimas Ciputra<dimas@kartoza.com>

RUN apt-get update -y && apt-get -y --force-yes install yui-compressor rpl mdbtools python-matplotlib

# Install Node js
RUN curl -sL https://deb.nodesource.com/setup_6.x -o nodesource_setup.sh && \
    bash nodesource_setup.sh && \
    apt-get -y --force-yes install nodejs && \
    npm -g install yuglify && \
    rpl "env node" "env nodejs" /usr/lib/node_modules/yuglify/bin/yuglify

# install shallow clone of django bims geonode branch
ARG BIMS_TAG=develop
RUN git clone --depth=1 git://github.com/kartoza/django-bims.git --branch ${BIMS_TAG} /usr/src/bims
WORKDIR /usr/src/bims

RUN cd /usr/src/bims/deployment/docker && \
    pip install -r REQUIREMENTS.txt && \
    pip install uwsgi && \
    npm install -g grunt-cli && \
    cp package.json /package.json && \
    cp /usr/src/bims/deployment/production/Gruntfile.js /Gruntfile.js && \
    cd / && npm install && \
    mkdir -p /home/web/media && \
    cd /usr/src/bims/deployment/production && \
    chmod +x entry-point.sh && \
    cp uwsgi.conf /usr/src/bims/uwsgi.conf

# Open port 8080 as we will be running our uwsgi socket on that
EXPOSE 8080

ENTRYPOINT ["/usr/src/bims/entry-point.sh"]
CMD ["uwsgi", "--ini", "/usr/src/bims/uwsgi.conf"]
