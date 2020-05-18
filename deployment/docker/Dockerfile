#--------- Generic stuff all our Dockerfiles should start with so we get caching ------------
FROM python:2.7.16-slim-stretch
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

# Install python dependencies
RUN echo "Geonode python dependencies"
RUN pip install celery==4.1.0 # see https://github.com/GeoNode/geonode/pull/3714

# install shallow clone of geonode master branch
RUN git clone -b '2.10.3' --depth=1 git://github.com/GeoNode/geonode.git --branch '2.10.3' /usr/src/geonode
RUN cd /usr/src/geonode/; pip install -r requirements.txt --no-cache-dir; pip install -e .

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

# Debian is messed up and aliases node as nodejs
# So when yuglify is installed it references the wrong node binary...
# lets fix that here...

# RUN rpl "env node" "env nodejs" /usr/lib/node_modules/yuglify/bin/yuglify

# Install grunt
RUN npm install -g grunt-cli
ADD package.json /package.json
ADD Gruntfile.js /Gruntfile.js
RUN cd / && npm install

#USER www-data
WORKDIR /home/web/django_project

ADD uwsgi.conf /uwsgi.conf

EXPOSE 8000
# Open port 8080 as we will be running our uwsgi socket on that
EXPOSE 8080

# ENTRYPOINT ["/usr/src/app/entrypoint.sh"]

CMD ["uwsgi", "--ini", "/uwsgi.conf"]
