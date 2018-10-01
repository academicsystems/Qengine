FROM alpine
MAINTAINER Academic Systems

ARG DOMAIN=localhost

# update, upgrade, & install packages

RUN apk update && apk upgrade
RUN apk add lighttpd openssl python2 py-setuptools wget git 
RUN apk add py2-pip gcc g++ make libffi-dev openssl-dev python-dev

RUN pip2.7 install pycrypto flask python-Levenshtein munkres requests pyyaml

# configure lighttpd

RUN adduser www-data -G www-data -H -s /bin/false -D

COPY assets/lighttpd.conf /etc/lighttpd/lighttpd.conf

RUN touch /var/log/lighttpd/error.log && chmod 664 /var/log/lighttpd/error.log && chown -R www-data:www-data /var/log/lighttpd
RUN touch /var/run/lighttpd.pid && chmod 664 /var/run/lighttpd.pid && chown -R www-data:www-data /var/run/lighttpd.pid
RUN mkdir -p /var/cache/lighttpd/compress/ && chmod 755 /var/cache/lighttpd/compress/ && chown -R www-data:www-data /var/cache/lighttpd/compress/

RUN rm -rf /var/www/localhost

# add files for running container

COPY assets/ssldomain /etc/lighttpd/ssldomain
COPY assets/load /bin/load
RUN chmod 550 /bin/load

# configure ssl

RUN mkdir -p /etc/lighttpd/ssl
RUN rm -rf /etc/lighttpd/ssl/*

RUN openssl genrsa -des3 -passout pass:x -out /etc/lighttpd/ssl/qengine.pass.key 2048
RUN openssl rsa -passin pass:x -in /etc/lighttpd/ssl/qengine.pass.key -out /etc/lighttpd/ssl/qengine.key
RUN rm /etc/lighttpd/ssl/qengine.pass.key
RUN openssl req -new -key /etc/lighttpd/ssl/qengine.key -out /etc/lighttpd/ssl/qengine.csr -subj "/CN=$DOMAIN"
RUN openssl x509 -req -days 3650 -in /etc/lighttpd/ssl/qengine.csr -signkey /etc/lighttpd/ssl/qengine.key -out /etc/lighttpd/ssl/qengine.crt
RUN cat /etc/lighttpd/ssl/qengine.key /etc/lighttpd/ssl/qengine.crt > /etc/lighttpd/ssl/qengine.pem
RUN chmod 400 /etc/lighttpd/ssl/*

# configure web.py server

RUN wget --no-check-certificate https://www.saddi.com/software/flup/dist/flup-1.0.2.tar.gz
RUN tar xzf flup-1.0.2.tar.gz && rm flup-1.0.2.tar.gz
RUN cd flup-1.0.2 && python setup.py install && cd ..

RUN wget --no-check-certificate http://webpy.org/static/web.py-0.38.tar.gz
RUN tar xzf web.py-0.38.tar.gz && rm web.py-0.38.tar.gz
RUN cd web.py-0.38 && python setup.py install && cd ..

COPY . /var/www

RUN chown www-data:www-data /var/www/qengine.py && chown www-data:www-data /var/www
RUN chown -R www-data:www-data /var/www/logs
RUN chown -R www-data:www-data /var/www/questions
RUN chmod 555 /var/www/entry.fcgi

# create necessary directories

RUN mkdir -p /tmp/qengine_cache && chown www-data:www-data /tmp/qengine_cache
RUN mkdir -p /var/www/questions
RUN chown www-data:www-data /var/www/questions

# this conf must be provided by the person building the image
COPY config/default-configuration.yaml /var/www/config/default-configuration.yaml

CMD ["load"]

