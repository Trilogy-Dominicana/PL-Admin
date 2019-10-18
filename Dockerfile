FROM python:3.7-alpine

ENV LD_LIBRARY_PATH /usr/local/instantclient
ENV ORACLE_HOME /usr/local/instantclient

WORKDIR /app

# COPY requirements.txt .

RUN apk update; \
  apk add gcc musl-dev libnsl libaio autoconf curl unzip git

RUN curl -k -o /tmp/basic.zip https://gitlab.viva.com.do/public-repos/oracle-instaclient/raw/master/instantclient-basic-linux.x64-11.2.0.4.0.zip && \
  curl -k -o /tmp/devel.zip https://gitlab.viva.com.do/public-repos/oracle-instaclient/raw/master/instantclient-sdk-linux.x64-11.2.0.4.0.zip && \
  curl -k -o /tmp/sqlplus.zip https://gitlab.viva.com.do/public-repos/oracle-instaclient/raw/master/instantclient-sqlplus-linux.x64-11.2.0.4.0.zip

# # Install Oracle Client and build OCI8 (Oracle Command Interface 8 - PHP extension)
RUN unzip -d /usr/local/ /tmp/basic.zip && \
  unzip -d /usr/local/ /tmp/devel.zip && \
  unzip -d /usr/local/ /tmp/sqlplus.zip && \
  ## Links are required for older SDKs
  ln -s /usr/local/instantclient_11_2 ${ORACLE_HOME} && \
  ln -s ${ORACLE_HOME}/libclntsh.so.* ${ORACLE_HOME}/libclntsh.so && \
  ln -s ${ORACLE_HOME}/libocci.so.* ${ORACLE_HOME}/libocci.so && \
  ln -s ${ORACLE_HOME}/lib* /usr/lib && \
  ln -s ${ORACLE_HOME}/sqlplus /usr/bin/sqlplus && \
  ln -s /usr/lib/libnsl.so.2.0.0  /usr/lib/libnsl.so.1

RUN rm -rf /tmp/*.zip /var/cache/apk/* /tmp/oracle-sdk

RUN python -m pip install --upgrade pip setuptools wheel && \
  python -m pip install tqdm && \
  python -m pip install --user --upgrade twine

# Create package global
# RUN 

# CMD ["python --version"]
