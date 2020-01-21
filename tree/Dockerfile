From python:3.7.5-slim
RUN pip install flask==1.1.1 tinydb==3.15.2
ADD ./src /src
WORKDIR /src
ENV PORT=80
ENV DEBUG=False
ENTRYPOINT ["python", "-u", "server.py"]