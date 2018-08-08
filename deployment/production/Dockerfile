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

RUN rpl "env node" "env nodejs" /usr/lib/node_modules/yuglify/bin/yuglify

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
