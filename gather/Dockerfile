From python:3.7.5-slim
RUN pip install paramiko==2.6.0 requests==2.22.0
ADD ./src /src
WORKDIR /src
ENV NUTANIX_VIP=10.149.11.41
ENV CVM_USER=nutanix
ENV CVM_PASS=nutanix/4u
ENV PRISM_USER=admin
ENV PRISM_PASS=Nutanix/4u!
ENV TREE_SERVER=127.0.0.1:80
ENV INTERVAL=60
ENV DEBUG=False
ENTRYPOINT ["python", "-u", "cron.py"]