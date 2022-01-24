#--------- Generic stuff all our Dockerfiles should start with so we get caching ------------
FROM python:3.7-slim-stretch as prod
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
RUN git clone -b '3.1' --depth=1 git://github.com/GeoNode/geonode.git --branch '3.1' /usr/src/geonode
RUN cd /usr/src/geonode/; pip install -r requirements.txt --no-cache-dir; pip install -e .

# Install python dependencies
RUN echo "Geonode python dependencies"
RUN pip install celery==4.4.2

# Install pygdal (after requirements https://github.com/GeoNode/geonode/pull/4599)
RUN pip install pygdal==$(gdal-config --version).*

# COPY . /usr/src/app
#
#RUN chmod +x /usr/src/app/tasks.py \
#    && chmod +x /usr/src/app/entrypoint.sh

# app-specific requirements
#RUN pip install --no-cache-dir -r /usr/src/app/requirements.txt
#RUN pip install -e /usr/src/app

ADD deployment/docker/REQUIREMENTS.txt /REQUIREMENTS.txt
RUN pip install -r /REQUIREMENTS.txt; pip install uwsgi
RUN npm --quiet -g install yuglify

RUN pip install MarkupSafe==1.1.1 && pip install pygbif==0.6.0

# Debian is messed up and aliases node as nodejs
# So when yuglify is installed it references the wrong node binary...
# lets fix that here...

# RUN rpl "env node" "env nodejs" /usr/lib/node_modules/yuglify/bin/yuglify

# Install grunt
RUN npm install -g grunt-cli
ADD deployment/docker/package.json /package.json
ADD deployment/docker/Gruntfile.js /Gruntfile.js
RUN cd / && npm install

#USER www-data
ADD . /home/web/django_project
WORKDIR /home/web/django_project
RUN cd bims && npm install --quiet -g webpack@5.50.0 && npm install --quiet -g webpack-cli@4.8.0 && npm install --quiet && webpack --mode production

ADD deployment/docker/uwsgi.conf /uwsgi.conf

# Open port 8080 as we will be running our uwsgi socket on that
EXPOSE 8080

# ENTRYPOINT ["/usr/src/app/entrypoint.sh"]

CMD ["uwsgi", "--ini", "/uwsgi.conf"]

FROM prod as dev

# This section taken on 2 July 2015 from
# https://docs.docker.com/examples/running_ssh_service/
# Sudo is needed by pycharm when it tries to pip install packages
RUN apt-get update && apt-get install -y openssh-server sudo
RUN mkdir /var/run/sshd
RUN echo 'root:docker' | chpasswd
RUN echo "PermitRootLogin yes" >> /etc/ssh/sshd_config

# SSH login fix. Otherwise user is kicked off after login
RUN sed 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' -i /etc/pam.d/sshd

ENV NOTVISIBLE "in users profile"
RUN echo "export VISIBLE=now" >> /etc/profile

# End of cut & paste section

ADD REQUIREMENTS-dev.txt /REQUIREMENTS-dev.txt
RUN pip install -r /REQUIREMENTS-dev.txt
ADD bashrc /root/.bashrc

RUN apt-get install -y chromium
RUN mkdir -p /opt/karma
RUN npm install -g karma
RUN cd / && npm install

RUN apt-get install vim -y
ADD karma.conf.docker.js /karma.conf.js

# --------------------------------------------------------
# Open ports as needed
# --------------------------------------------------------

# Open port 8080 as we will be running our django dev server on
EXPOSE 8080
# Open port 22 as we will be using a remote interpreter from pycharm
EXPOSE 22

CMD ["/usr/sbin/sshd", "-D"]

