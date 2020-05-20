FROM python:3.8.2-alpine3.11
LABEL maintainer="Wilowayne De La Cruz <wilo0087@gmail.com>"

ENV LD_LIBRARY_PATH=/usr/local/instantclient_11_2
ENV ORACLE_HOME=/usr/local/instantclient

WORKDIR /app
RUN mkdir -p /plsql

COPY . /app

RUN apk add gcc libnsl libaio curl unzip openssl-dev autoconf musl-dev tzdata

# Setup timezone to avoid: Error while trying to retrieve text for error ORA-01804
 RUN cp /usr/share/zoneinfo/America/Santo_Domingo /etc/localtime

# Setup instaclient to be use by Cx_Oracle python extenxion
RUN curl -k -o /tmp/basic.zip https://raw.githubusercontent.com/wilo087/Oracle-Instaclient_11_2/master/instantclient-basic-linux.x64-11.2.0.4.0.zip
RUN unzip -d /usr/local/ /tmp/basic.zip; \
  ## Links are required for older SDKs
  ln -s /usr/local/instantclient_11_2 ${ORACLE_HOME}; \
  ln -s ${ORACLE_HOME}/libclntsh.so.* ${ORACLE_HOME}/libclntsh.so; \
  ln -s ${ORACLE_HOME}/libocci.so.* ${ORACLE_HOME}/libocci.so; \
  ln -s ${ORACLE_HOME}/lib* /usr/lib; \
  ln -s /usr/lib/libnsl.so.2.0.0  /usr/lib/libnsl.so.1

RUN rm -rf /tmp/*.zip /var/cache/apk/* /tmp/oracle-sdk
RUN apk del unzip curl

# Create command to the app globally 
RUN ln -sf /app/cli.py /usr/local/bin/pladmin

# Create package global
RUN pip install --upgrade pip && pip install -r requirements.txt

# TODO: The entry has to be tu validate if exists duplicated objects
# ENTRYPOINT ["sh", "/app/docker/setup.sh"]
