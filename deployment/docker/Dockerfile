#--------- Generic stuff all our Dockerfiles should start with so we get caching ------------
# Note this base image is based on debian
FROM python:3.6
MAINTAINER Dimas Ciputra<dimas@kartoza.com>

RUN export DEBIAN_FRONTEND=noninteractive
ENV DEBIAN_FRONTEND noninteractive
RUN dpkg-divert --local --rename --add /sbin/initctl

RUN apt-get update -y

RUN apt-get install -y python3-pip \
    python-gdal \
    python-geoip \
    python3-setuptools \
    rpl

RUN apt-get -y --force-yes install yui-compressor

ADD REQUIREMENTS.txt /REQUIREMENTS.txt
RUN pip install -r /REQUIREMENTS.txt
RUN pip install uwsgi

# Install Node js
RUN curl -sL https://deb.nodesource.com/setup_6.x -o nodesource_setup.sh
RUN bash nodesource_setup.sh
RUN apt-get -y --force-yes install nodejs
RUN npm -g install yuglify

# Debian is messed up and aliases node as nodejs
# So when yuglify is installed it references the wrong node binary...
# lets fix that here...

RUN rpl "env node" "env nodejs" /usr/lib/node_modules/yuglify/bin/yuglify

# Install grunt
RUN npm install -g grunt-cli
ADD package.json /package.json
ADD Gruntfile.js /Gruntfile.js
RUN cd / && npm install grunt grunt-contrib-concat grunt-contrib-uglify
RUN cd / && npm install grunt-contrib-requirejs

#USER www-data
WORKDIR /home/web/django_project

ADD uwsgi.conf /uwsgi.conf

# Open port 8080 as we will be running our uwsgi socket on that
EXPOSE 8080

CMD ["uwsgi", "--ini", "/uwsgi.conf"]
