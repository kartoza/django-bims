#--------- Generic stuff all our Dockerfiles should start with so we get caching ------------
FROM python:3.7-slim-stretch
MAINTAINER Dimas Ciputra<dimas@kartoza.com>

RUN mkdir -p /usr/src/{app,geonode}

WORKDIR /usr/src/app

# Install system dependencies
RUN echo "Updating apt-get" && \
    apt-get update && \
    echo "Installing build dependencies" && \
    apt-get install -y gcc make libc-dev musl-dev libpcre3 libpcre3-dev g++ && \
    echo "Installing Pillow dependencies" && \
    # RUN apt-get install -y NOTHING ?? It was probably added in other packages... ALPINE needed jpeg-dev zlib-dev && \
    echo "Installing GDAL dependencies" && \
    apt-get install -y libgeos-dev libgdal-dev && \
    echo "Installing Psycopg2 dependencies" && \
    # RUN apt-get install -y NOTHING ?? It was probably added in other packages... ALPINE needed postgresql-dev && \
    echo "Installing other dependencies" && \
    apt-get install -y libxml2-dev libxslt-dev && \
    echo "Installing GeoIP dependencies" && \
    apt-get install -y geoip-bin geoip-database && \
    echo "Installing healthceck dependencies" && \
    apt-get install -y curl && \
    echo "Python server" && \
    pip install uwsgi && \
    apt-get install -y git && \
    echo "Node js" && \
    curl -sL https://deb.nodesource.com/setup_12.x -o nodesource_setup.sh && \
    bash nodesource_setup.sh && \
    apt-get install -y nodejs && \
    echo "Removing build dependencies and cleaning up" && \
    # TODO : cleanup apt-get with something like apt-get -y --purge autoremove gcc make libc-dev musl-dev libpcre3 libpcre3-dev g++ && \
    rm -rf /var/lib/apt/lists/* && \
    rm -rf ~/.cache/pip

# install shallow clone of geonode master branch
RUN git clone -b '3.0' --depth=1 git://github.com/GeoNode/geonode.git --branch '3.0' /usr/src/geonode
RUN cd /usr/src/geonode/; pip install -r requirements.txt --no-cache-dir; pip install -e .

# Install python dependencies
RUN echo "Geonode python dependencies"
RUN pip install celery==4.4.2

# Install pygdal (after requirements https://github.com/GeoNode/geonode/pull/4599)
RUN pip install pygdal==$(gdal-config --version).*

COPY . /usr/src/app
#
#RUN chmod +x /usr/src/app/tasks.py \
#    && chmod +x /usr/src/app/entrypoint.sh

# app-specific requirements
#RUN pip install --no-cache-dir -r /usr/src/app/requirements.txt
#RUN pip install -e /usr/src/app

ADD REQUIREMENTS.txt /REQUIREMENTS.txt
RUN pip install -r /REQUIREMENTS.txt; pip install uwsgi
RUN npm -g install yuglify

RUN pip install MarkupSafe==1.1.1 && pip install pygbif==0.6.0

# Debian is messed up and aliases node as nodejs
# So when yuglify is installed it references the wrong node binary...
# lets fix that here...

# RUN rpl "env node" "env nodejs" /usr/lib/node_modules/yuglify/bin/yuglify

# Install grunt
RUN npm install -g grunt-cli
ADD package.json /package.json
ADD Gruntfile.js /Gruntfile.js
RUN cd / && npm install

# install shallow clone of django bims geonode branch
ARG BIMS_TAG=develop
RUN git clone --depth=1 git://github.com/kartoza/django-bims.git --branch ${BIMS_TAG} /usr/src/bims

#USER www-data
WORKDIR /usr/src/bims
RUN mkdir -p /home/web/media
ADD entry-point.sh /usr/src/bims/entry-point.sh
RUN chmod +x /usr/src/bims/entry-point.sh
ADD uwsgi.conf /usr/src/bims/uwsgi.conf

# Open port 8080 as we will be running our uwsgi socket on that
EXPOSE 8080

ENTRYPOINT ["/usr/src/bims/entry-point.sh"]
CMD ["uwsgi", "--ini", "/usr/src/bims/uwsgi.conf"]
