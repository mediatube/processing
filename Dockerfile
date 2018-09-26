FROM jrottenberg/ffmpeg:centos
RUN yum update -y && yum reinstall -y glibc-common && \
    yum install -y https://centos7.iuscommunity.org/ius-release.rpm && yum update -y && \
    yum install -y python36u python36u-libs python36u-devel python36u-pip && yum clean all

########## ENV ##########
# Set the locale(en_US.UTF-8)
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8
ENV PYTHONIOENCODING utf-8
# Set the locale(ja_JP.UTF-8)
#ENV LANG ja_JP.UTF-8
#ENV LANGUAGE ja_JP:ja
#ENV LC_ALL ja_JP.UTF-8

# Set app env
ENV HOME /root
########## ENV ##########
ADD . /root
WORKDIR /root
RUN pip3.6 install --upgrade -r requirements.txt

ENTRYPOINT ["python3.6","worker.py","processing"]
#CMD ["1"]
#CMD ["worker.py","static.250.19.216.95.clients.your-server.de"]
#CMD ["python","worker.py","s1.mediatube.xyz"]
