FROM python:3.8
 
# Install CMake
RUN apt-get update && \
  apt-get --yes install cmake && \
  rm -rf /var/lib/apt/lists/*
  
# Install packages
COPY requirements.txt ./
RUN pip3 install -r requirements.txt

COPY public /app/public
COPY proteins.py /app/proteins.py
WORKDIR /app
 
ENV FLASK_ENV=development
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8
 
ENTRYPOINT ["python3", "proteins.py"]
