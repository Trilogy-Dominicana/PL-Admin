FROM python:3.8.2-alpine3.11
# FROM python:alpine3.10
ENV LD_LIBRARY_PATH=/usr/local/instantclient
ENV ORACLE_HOME=/usr/local/instantclient

WORKDIR /app
RUN mkdir -p /plsql

# COPY requirements.txt .
COPY . /app

RUN apk update; \
  apk add gcc musl-dev libnsl libaio autoconf curl unzip openssl-dev tzdata

# Setup timezone 
RUN cp /usr/share/zoneinfo/America/Santo_Domingo /etc/localtime

# Get instaclient
RUN curl -k -o /tmp/basic.zip https://download.oracle.com/otn_software/mac/instantclient/instantclient-basic-macos.zip
  # curl -k -o /tmp/devel.zip https://gitlab.viva.com.do/public-repos/oracle-instaclient/raw/master/instantclient-sdk-linux.x64-11.2.0.4.0.zip
  # curl -k -o /tmp/sqlplus.zip https://gitlab.viva.com.do/public-repos/oracle-instaclient/raw/master/instantclient-sqlplus-linux.x64-11.2.0.4.0.zip

# # Install Oracle Client and build OCI8 (Oracle Command Interface 8 - PHP extension)
RUN unzip -d /usr/local/ /tmp/basic.zip; \
  unzip -d /usr/local/ /tmp/devel.zip; \
  # unzip -d /usr/local/ /tmp/sqlplus.zip && \
  ## Links are required for older SDKs
  ln -s /usr/local/instantclient_11_2 ${ORACLE_HOME}; \
  ln -s ${ORACLE_HOME}/libclntsh.so.* ${ORACLE_HOME}/libclntsh.so; \
  ln -s ${ORACLE_HOME}/libocci.so.* ${ORACLE_HOME}/libocci.so; \
  ln -s ${ORACLE_HOME}/lib* /usr/lib; \
  ln -s ${ORACLE_HOME}/sqlplus /usr/bin/sqlplus; \
  ln -s /usr/lib/libnsl.so.2.0.0  /usr/lib/libnsl.so.1

RUN rm -rf /tmp/*.zip /var/cache/apk/* /tmp/oracle-sdk
RUN apk del unzip

# Create command to the app
RUN ln -sf /app/cli.py /usr/local/bin/pladmin

# Create package global
RUN pip install --upgrade pip && pip install -r requirements.txt

# Modifying permissions of setup.sh (avoid windows bug related to file line endings (CRLF))
# RUN ["chmod", "+x", "/app/docker/setup.sh"]
# RUN sed -i -e 's/\r$//' /app/docker/setup.sh

# ENTRYPOINT ["sh", "/app/docker/setup.sh"]
