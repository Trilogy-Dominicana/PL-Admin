FROM python:3.8.2-alpine3.11
LABEL maintainer="Wilowayne De La Cruz <wilo0087@gmail.com>"

ENV LD_LIBRARY_PATH=/usr/local/instantclient_11_2

WORKDIR /app
RUN mkdir -p /plsql

COPY . /app

RUN apk add gcc libnsl libaio curl unzip openssl-dev autoconf musl-dev


# Setup instaclient to be use by Cx_Oracle python extenxion
RUN curl -k -o /tmp/basic.zip https://raw.githubusercontent.com/wilo087/Oracle-Instaclient_11_2/master/instantclient-basic-linux.x64-11.2.0.4.0.zip
RUN unzip -d /usr/local/ /tmp/basic.zip; \
  ln -sf ${LD_LIBRARY_PATH}/libclntsh.so.19.1 ${LD_LIBRARY_PATH}/libclntsh.so; \
  ln -sf /usr/lib/libnsl.so.2.0.0  /usr/lib/libnsl.so.1


RUN rm -rf /tmp/*.zip /var/cache/apk/* /tmp/oracle-sdk ${LD_LIBRARY_PATH}/libociei.so ${LD_LIBRARY_PATH}/libocci.so.11.1
RUN apk del unzip curl

# Create command to the app globally 
RUN ln -sf /app/cli.py /usr/local/bin/pladmin

# Create package global
RUN pip install --upgrade pip && pip install -r requirements.txt

# TODO: The entry has to be tu validate if exists duplicated objects
# ENTRYPOINT ["sh", "/app/docker/setup.sh"]
