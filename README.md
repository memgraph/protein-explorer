<h1 align="center">
 🔍 Proteins Explorer 🔍
</h1>

<p align="center">
  <a href="https://github.com/memgraph/protein-explorer/LICENSE">
    <img src="https://img.shields.io/github/license/memgraph/protein-explorer" alt="license" title="license"/>
  </a>
  <a href="https://github.com/memgraph/protein-explorer">
    <img src="https://img.shields.io/badge/PRs-welcome-brightgreen.svg" alt="build" title="build"/>
  </a>
</p>

<p align="center">
  <a href="https://memgr.ph/join-discord">
    <img src="https://img.shields.io/badge/Discord-7289DA?style=for-the-badge&logo=discord&logoColor=white" alt="Discord"/>
  </a>
</p>

<p align="center">
  <a href="https://github.com/memgraph/protein-explorer">
    <img src="https://public-assets.memgraph.com/github/protein-explorer/protein-explorer.png" 
         alt="protein-explorer" 
         title="protein-explorer"
         style="width: 70%"/>
  </a>
</p>

## Docker and Compose Installation

Install [docker and docker-compose](https://docs.docker.com/get-docker/). Docker
is an open platform for developing, shipping, and running applications. It
enables you to separate your application from your infrastructure (host
machine). If you are installing Docker Desktop on Windows or macOS,
docker-compose will already be included. For Linux visit [this
site](https://docs.docker.com/compose/install/).

## Starting the app

Position yourself in the root folder of the `protein-explorer` project. Next,
build the Docker image and run the application with the following commands:

```
docker-compose build
docker-compose up
```

If everything was successful, you can open the app in your browser. The app will
be listening on: [http://localhost:5000/](http://localhost:5000/).
