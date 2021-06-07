# Proteins Explorer

## Docker and Compose Installation

Install [docker and docker-compose](https://docs.docker.com/get-docker/). Docker is an open platform for developing, shipping, and running applications. It enables you to separate your application from your infrastructure (host machine). If you are installing Docker on Windows, docker-compose will already be included. For Linux and macOS visit [this site](https://docs.docker.com/compose/install/).

## Make sure to have memgraph:latest Docker image

Download the [Memgraph Docker image](https://download.memgraph.com/memgraph/v1.5.0/docker/memgraph-1.5.0-community-docker.tar.gz) and save it to a location you can quickly access.

Run the command below in your command line to begin the installation. Simply replace the <version> placeholder with the version number included in the filename of the Docker image you’ve just downloaded:
'''
docker load -i /path/to/memgraph-<version>-docker.tar.gz
'''

## Installing MAGE with Docker

To build and install MAGE query modules you will need: **Python3**, **Make**, **CMake** and **Clang**. 

Clone the [MAGE repository](https://github.com/memgraph/mage). 

Position yourself in the root folder of the MAGE project and build MAGE tagged Docker image with the following command.
'''
docker build . -t memgraph:mage
'''

## Start the app

Position yourself in the root folder of the Protein Explorer project. Build the Docker image and run the application with the following commands:

'''
docker-compose build
docker-compose up
'''

If everything was successful, you can open it in your browser. The app will be listening on: [http://localhost:5000/](http://localhost:5000/).
