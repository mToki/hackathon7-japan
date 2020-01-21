From python:3.7.5-slim
RUN pip install flask==1.1.1 Pillow==6.1.0
ADD ./src /src
WORKDIR /src
ENV PORT=80
ENV DEBUG=False
ENTRYPOINT ["python", "-u", "server.py"]