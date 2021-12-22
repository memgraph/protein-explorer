import logging
import json
import time
from pathlib import Path
from argparse import ArgumentParser
from functools import wraps
from flask import Flask, Response, render_template
from gqlalchemy import Match, Memgraph
from gqlalchemy.models import MemgraphIndex
from enum import Enum


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
    parser.add_argument("--host", default="0.0.0.0", help="Host address.")
    parser.add_argument("--port", default=5000, type=int, help="App port.")
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
connection_established = False
while not connection_established:
    try:
        if memgraph._get_cached_connection().is_active():
            connection_established = True
    except:
        log.info("Memgraph probably isn't running.")
        time.sleep(4)


app = Flask(
    __name__,
    template_folder=args.template_folder,
    static_folder=args.static_folder,
    static_url_path="",
)


class Properties(Enum):
    ENTREZ_GENE_ID = "EntrezGeneID"
    OFFICIAL_SYMBOL = "OfficialSymbol"
    OFFICIAL_FULL_NAME = "OfficialFullName"
    SUMMARY = "Summary"
    BETWEENNESS_CENTRALITY = "BetweennessCentrality"


def log_time(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start_time
        log.info(f"Time for {func.__name__} is {duration}")
        return result

    return wrapper


@log_time
def load_tissue_data(tissue: str):
    """Load tissue-specific data into the database."""
    properties_address = Path("/usr/lib/memgraph/import-data").joinpath(
        f"interactions_{tissue}_properties.csv"
    )
    interactions_address = Path("/usr/lib/memgraph/import-data").joinpath(
        f"interactions_{tissue}.csv"
    )

    memgraph.execute(
        f"""LOAD CSV FROM "{properties_address}"
        WITH HEADER DELIMITER "|" AS row
        CREATE (n:PROTEIN
                        {{{Properties.ENTREZ_GENE_ID.value}: ToInteger(row.{Properties.ENTREZ_GENE_ID.value}),
                        {Properties.OFFICIAL_SYMBOL.value}: row.{Properties.OFFICIAL_SYMBOL.value},
                        {Properties.OFFICIAL_FULL_NAME.value}: row.{Properties.OFFICIAL_FULL_NAME.value},
                        {Properties.SUMMARY.value}: row.{Properties.SUMMARY.value}}}
        );"""
    )

    memgraph.create_index(
        MemgraphIndex(label="PROTEIN", property=Properties.ENTREZ_GENE_ID.value)
    )

    memgraph.execute(
        f"""LOAD CSV FROM "{interactions_address}"
        WITH HEADER DELIMITER "|" AS row
        MATCH (a:PROTEIN {{{Properties.ENTREZ_GENE_ID.value}: toInteger(row.{Properties.ENTREZ_GENE_ID.value}1)}}),
        (b:PROTEIN {{{Properties.ENTREZ_GENE_ID.value}: toInteger(row.{Properties.ENTREZ_GENE_ID.value}2)}})
        CREATE (a)-[e:INTERACTION]->(b);"""
    )


@log_time
def calculate_betweenness_centrality():
    """Call the Betweenness Centrality procesdure and store the results."""
    memgraph.execute(
        """CALL betweenness_centrality.get(FALSE, TRUE)
        YIELD node, betweenness_centrality
        SET node.BetweennessCentrality = toFloat(betweenness_centrality); """
    )


@app.route("/load-data/<tissue>")
def load_data(tissue):
    try:
        memgraph.drop_database()
        load_tissue_data(tissue)
        calculate_betweenness_centrality()
    except Exception as e:
        log.error(f"Loading data failed: {e}")
        return ("", 500)

    return Response(json.dumps(""), status=200, mimetype="application/json")


@app.route("/get-graph", methods=["GET"])
@log_time
def get_data(*args, **kwargs):
    """Load everything from the database."""
    try:
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
            source_id = result["from"].properties[Properties.ENTREZ_GENE_ID.value]
            source_bc = result["from"].properties[
                Properties.BETWEENNESS_CENTRALITY.value
            ]
            source_symbol = result["from"].properties[Properties.OFFICIAL_SYMBOL.value]

            target_id = result["to"].properties[Properties.ENTREZ_GENE_ID.value]
            target_bc = result["to"].properties[Properties.BETWEENNESS_CENTRALITY.value]
            target_symbol = result["to"].properties[Properties.OFFICIAL_SYMBOL.value]

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

        return Response(json.dumps(response), status=200, mimetype="application/json")

    except Exception:
        log.info("Data fetching went wrong.")
        return ("", 500)


@app.route("/protein-properties/<protein_id>", methods=["GET"])
@log_time
def get_properties(*args, **kwargs):
    try:
        protein_id = kwargs["protein_id"]

        results = (
            Match()
            .node(variable="node")
            .where(f"node.{Properties.ENTREZ_GENE_ID.value}", "=", int(protein_id))
            .execute()
        )
        result = next(results)

        node_bc = result["node"].properties.get(
            Properties.BETWEENNESS_CENTRALITY.value, ""
        )
        node_id = result["node"].properties.get(Properties.ENTREZ_GENE_ID.value, "")
        node_symbol = result["node"].properties.get(
            Properties.OFFICIAL_SYMBOL.value, ""
        )
        node_name = result["node"].properties.get(
            Properties.OFFICIAL_FULL_NAME.value, ""
        )
        node_summary = result["node"].properties.get(Properties.SUMMARY.value, "")

        response = {
            "properties": {
                Properties.ENTREZ_GENE_ID.value: node_id,
                Properties.OFFICIAL_SYMBOL.value: node_symbol,
                Properties.OFFICIAL_FULL_NAME.value: node_name,
                Properties.SUMMARY.value: node_summary,
                Properties.BETWEENNESS_CENTRALITY.value: node_bc,
            }
        }

        return Response(json.dumps(response), status=200, mimetype="application/json")

    except Exception:
        log.info("Protein properties fetching went wrong.")
        return ("", 500)


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


def main():
    load_data("cochlea")
    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()
