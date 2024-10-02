#--------- Generic stuff all our Dockerfiles should start with so we get caching ------------
FROM python:3.12.3-slim-bookworm as prod
MAINTAINER Dimas Ciputra <dimas@kartoza.com>

# Set up directories
RUN mkdir -p /usr/src/{app,geonode}

WORKDIR /usr/src/app

# Install system dependencies
RUN echo "Updating apt-get" && \
    apt-get update && \
    echo "Installing build dependencies" && \
    apt-get install -y --no-install-recommends \
    nodejs npm \
    gcc make libc-dev musl-dev libpcre3 libpcre3-dev g++ \
    libgdal-dev libcurl4-gnutls-dev librtmp-dev curl git && \
    echo "Python server" && \
    pip install uwsgi && \
    echo "Removing build dependencies and cleaning up" && \
    apt-get -y --purge autoremove make libc-dev musl-dev g++ && \
    rm -rf /var/lib/apt/lists/* && \
    rm -rf ~/.cache/pip

# Add application requirements
COPY deployment/docker/REQUIREMENTS.txt /REQUIREMENTS.txt
RUN pip install --no-cache-dir -r /REQUIREMENTS.txt

# Add and install Node.js dependencies
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

ENTRYPOINT ["/entrypoint.sh"]
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

ADD deployment/docker/REQUIREMENTS-dev.txt /REQUIREMENTS-dev.txt
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

