#--------- Generic stuff all our Dockerfiles should start with so we get caching ------------
FROM geosolutionsit/geonode-generic:1.0
MAINTAINER Dimas Ciputra<dimas@kartoza.com>

RUN apt-get update -y && apt-get -y --force-yes install yui-compressor rpl

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
RUN cd / && npm install

#USER www-data
WORKDIR /home/web/django_project

ADD uwsgi.conf /uwsgi.conf

# Open port 8080 as we will be running our uwsgi socket on that
EXPOSE 8080

CMD ["uwsgi", "--ini", "/uwsgi.conf"]
