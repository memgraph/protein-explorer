# Proteins Explorer

## Docker and Compose Installation

Install [docker and docker-compose](https://docs.docker.com/get-docker/). Docker is an open platform for developing, shipping, and running applications. It enables you to separate your application from your infrastructure (host machine). If you are installing Docker on Windows, docker-compose will already be included. For Linux and macOS visit [this site](https://docs.docker.com/compose/install/).

## Make sure to have memgraph/memgraph-mage Docker image

Run the command below in your command line:
```
docker pull memgraph/memgraph-mage
```

## Start the app

To start the app, follow these instructions:

1. Position yourself in the root folder of the Protein Explorer project.
2. Create an empty directory with the name `/memgraph`
3. Download the [data](https://download.memgraph.com/dataset/proteins/proteins_blog.zip).
4. Create the `import-data` directory inside the `/memgraph` directory and extract the downloaded data there.

Now, you can build the Docker image and run the application with the following commands:

```
docker-compose build
docker-compose up
```

If everything was successful, you can open it in your browser. The app will be listening on: [http://localhost:5000/](http://localhost:5000/).
