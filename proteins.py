import logging
import json
import time
from pathlib import Path
from argparse import ArgumentParser
from flask import Flask, Response, render_template
from gqlalchemy import Match, Memgraph
from gqlalchemy.models import MemgraphIndex


log = logging.getLogger(__name__)


def init_log():
    logging.basicConfig(level=logging.INFO)
    log.info("Logging enabled")
    logging.getLogger("werkzeug").setLevel(logging.WARNING)


init_log()


def parse_args():
    """
    Parse command line arguments.
    """
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--app-host", default="0.0.0.0", help="Host address.")
    parser.add_argument("--app-port", default=5000, type=int, help="App port.")
    parser.add_argument(
        "--template-folder",
        default="public/template",
        help="Path to the directory with flask templates.",
    )
    parser.add_argument(
        "--static-folder",
        default="public",
        help="Path to the directory with flask static files.",
    )
    parser.add_argument(
        "--debug",
        default=True,
        action="store_true",
        help="Run web server in debug mode.",
    )
    print(__doc__)
    return parser.parse_args()


args = parse_args()


memgraph = Memgraph()


app = Flask(
    __name__,
    template_folder=args.template_folder,
    static_folder=args.static_folder,
    static_url_path="",
)


def clear_db():
    """Delete everything from the database."""
    try:
        memgraph.execute_query("MATCH (n) DETACH DELETE n;")
    except BaseException:
        log.info("Clear database went wrong.")
        return ("", 204)


def load_tissue_data(tissue: str):
    """Load tissue-specific data into the database."""
    try:
        start_time = time.time()

        properties_addres = Path("/usr/lib/memgraph/import-data") / Path(
            "interactions_" + tissue + "_properties.csv"
        )
        interactions_addres = Path("/usr/lib/memgraph/import-data") / Path(
            "interactions_" + tissue + ".csv"
        )

        memgraph.execute_query(
            f"""LOAD CSV FROM "{properties_addres}"
            WITH HEADER DELIMITER "|" AS row
            CREATE (n:PROTEIN
                            {{EntrezGeneID: ToInteger(row.EntrezGeneID),
                            OfficialSymbol: row.OfficialSymbol,
                            OfficialFullName: row.OfficialFullName,
                            Summary: row.Summary}}
            );"""
        )

        memgraph.create_index(MemgraphIndex(label="PROTEIN", property="EntrezGeneID"))

        memgraph.execute_query(
            f"""LOAD CSV FROM "{interactions_addres}"
            WITH HEADER DELIMITER "|" AS row
            MATCH (a:PROTEIN {{EntrezGeneID: toInteger(row.EntrezGeneID1)}}),
            (b:PROTEIN {{EntrezGeneID: toInteger(row.EntrezGeneID2)}})
            CREATE (a)-[e:INTERACTION]->(b);"""
        )

        duration = time.time() - start_time
        log.info("Data loaded in: " + str(duration) + " seconds")
    except BaseException:
        log.info("Data loading went wrong.")
        return ("", 204)


def calculate_betweenness_centrality():
    """Call the Betweenness Centrality procesdure and store the results."""
    try:
        start_time = time.time()
        memgraph.execute_query(
            """CALL betweenness_centrality.get(FALSE, TRUE)
            YIELD node, betweeenness_centrality
            SET node.BetweennessCentrality = toFloat(betweeenness_centrality); """
        )
        duration = time.time() - start_time
        log.info("Betweenness Centrality calculated in: " + str(duration) + " seconds")
    except BaseException:
        log.info("Calculating betweenness centrality went wrong.")
        return ("", 204)


@app.route("/load-data/<tissue>")
def load_data(tissue):
    clear_db()
    load_tissue_data(tissue)
    calculate_betweenness_centrality()

    return Response(json.dumps(""), status=200, mimetype="application/json")


@app.route("/get-graph", methods=["GET"])
def get_data():
    """Load everything from the database."""
    try:
        start_time = time.time()

        results = (
            Match()
            .node("PROTEIN", variable="from")
            .to("INTERACTION")
            .node("PROTEIN", variable="to")
            .execute()
        )

        # Set for quickly check if we have already added the node or the edge
        nodes_set = set()
        links_set = set()
        for result in results:
            source_id = result["from"].properties["EntrezGeneID"]
            source_bc = result["from"].properties["BetweennessCentrality"]
            source_symbol = result["from"].properties["OfficialSymbol"]

            target_id = result["to"].properties["EntrezGeneID"]
            target_bc = result["to"].properties["BetweennessCentrality"]
            target_symbol = result["to"].properties["OfficialSymbol"]

            nodes_set.add((source_id, source_bc, source_symbol))
            nodes_set.add((target_id, target_bc, target_symbol))

            if (source_id, target_id) not in links_set and (
                target_id,
                source_id,
            ) not in links_set:
                links_set.add((source_id, target_id))

        nodes = [
            {"id": node_id, "bc": node_bc, "symbol": node_symbol}
            for node_id, node_bc, node_symbol in nodes_set
        ]
        links = [{"source": n_id, "target": m_id} for (n_id, m_id) in links_set]

        response = {"nodes": nodes, "links": links}

        duration = time.time() - start_time
        log.info("Data fetched in: " + str(duration) + " seconds")

        return Response(json.dumps(response), status=200, mimetype="application/json")

    except BaseException:
        log.info("Data fetching went wrong.")
        return ("", 204)


@app.route("/protein-properties/<protein_id>", methods=["GET"])
def get_properties(protein_id):
    try:
        start_time = time.time()

        results = (
            Match()
            .node(variable="node")
            .where("node.EntrezGeneID", "=", int(protein_id))
            .execute()
        )
        result = next(results)

        node_bc = result["node"].properties.get("BetweennessCentrality", "")
        node_id = result["node"].properties.get("EntrezGeneID", "")
        node_symbol = result["node"].properties.get("OfficialSymbol", "")
        node_name = result["node"].properties.get("OfficialFullName", "")
        node_summary = result["node"].properties.get("Summary", "")

        response = {
            "properties": {
                "EntrezGeneID": node_id,
                "OfficialSymbol": node_symbol,
                "OfficialFullName": node_name,
                "Summary": node_summary,
                "BetweennessCentrality": node_bc,
            }
        }

        duration = time.time() - start_time
        log.info("Protein properties fetched in: " + str(duration) + " seconds")

        return Response(json.dumps(response), status=200, mimetype="application/json")

    except BaseException:
        log.info("Protein properties fetching went wrong.")
        return ("", 204)


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


def main():
    load_data("cochlea")
    app.run(host=args.app_host, port=args.app_port, debug=args.debug)


if __name__ == "__main__":
    main()
