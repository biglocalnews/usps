FROM ubuntu:jammy

# Install dependencies, including gdal which comes from the ubuntugis repo.
RUN apt-get update \
&& apt-get install -y software-properties-common \
&& apt-add-repository ppa:ubuntugis/ppa \
&& apt-get update \
&& DEBIAN_FRONTEND=noninteractive apt-get install -y \
    postgis \
    wget \
    unzip \
    gdal-bin \
&& rm -rf /var/lib/apt/lists/*

# NOTE: ideally /gisdata is mounted as a persistent volume, so that TIGER data
# doesn't have to be re-downloaded constantly. This can take quite a long time.
# Same is true of /addrdata, which contains OpenAddresses data.
RUN mkdir -p /gisdata
RUN mkdir -p /addrdata
COPY ./scripts/*.sh .
COPY ./scripts/*.sql .

# Set DB credentials in the environment
RUN echo "source /db.sh" >> /root/.bashrc

CMD ["tail", "-f", "/dev/null"]
