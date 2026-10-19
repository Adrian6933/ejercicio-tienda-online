"""Preparar data view, panel y regla de errores en el Kibana local de la práctica."""

import argparse
import json
from urllib.error import HTTPError
from urllib.request import Request, urlopen


def call(base, path, body=None, method=None):
    payload = json.dumps(body).encode() if body is not None else None
    req = Request(
        base + path,
        data=payload,
        method=method or ("POST" if body is not None else "GET"),
        headers={"Content-Type": "application/json", "kbn-xsrf": "master-exercise"},
    )
    try:
        with urlopen(req, timeout=30) as response:
            return json.load(response)
    except HTTPError as exc:
        raise RuntimeError(
            f"{path}: HTTP {exc.code}: {exc.read().decode()[:500]}"
        ) from exc


def configure(kibana, elastic):
    mapping = {
        "properties": {
            "@timestamp": {"type": "date"},
            "event.duration_ms": {"type": "float"},
            "http.response.status_code": {"type": "integer"},
            "event.action": {"type": "keyword"},
            "http.route": {"type": "keyword"},
            "trace.id": {"type": "keyword"},
        }
    }
    call(
        elastic,
        "/_index_template/taller-practica",
        {
            "index_patterns": ["taller-*"],
            "priority": 501,
            "data_stream": {},
            "template": {
                "settings": {"number_of_shards": 1, "number_of_replicas": 0},
                "mappings": mapping,
            },
        },
        "PUT",
    )
    call(elastic, "/_data_stream/taller-logs", method="PUT")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kibana", default="http://localhost:15601")
    parser.add_argument("--elastic", default="http://localhost:19200")
    args = parser.parse_args()
    try:
        configure(args.kibana, args.elastic)
    except RuntimeError as exc:
        if "resource_already_exists_exception" not in str(exc):
            raise
    call(
        args.kibana,
        "/api/data_views/data_view",
        {
            "data_view": {
                "id": "taller-data",
                "title": "taller-*",
                "name": "Taller · aplicación",
                "timeFieldName": "@timestamp",
            },
            "override": True,
        },
    )
    panels = []
    definitions = [
        (
            "traffic",
            "Tráfico de la tienda",
            "histogram",
            [
                {
                    "id": "1",
                    "enabled": True,
                    "type": "count",
                    "schema": "metric",
                    "params": {},
                },
                {
                    "id": "2",
                    "enabled": True,
                    "type": "date_histogram",
                    "schema": "segment",
                    "params": {"field": "@timestamp", "interval": "auto"},
                },
            ],
            "",
        ),
        (
            "latency",
            "Latencia p95 (ms)",
            "metric",
            [
                {
                    "id": "1",
                    "enabled": True,
                    "type": "percentiles",
                    "schema": "metric",
                    "params": {"field": "event.duration_ms", "percents": [95]},
                }
            ],
            "",
        ),
        (
            "checkouts",
            "Checkouts correctos",
            "metric",
            [
                {
                    "id": "1",
                    "enabled": True,
                    "type": "count",
                    "schema": "metric",
                    "params": {},
                }
            ],
            'http.route : "/orders/{order_id}/checkout" and http.response.status_code : 200',
        ),
    ]
    objects = []
    for index, (key, title, kind, aggregations, query) in enumerate(definitions):
        vid = "taller-" + key
        objects.append(
            {
                "type": "visualization",
                "id": vid,
                "attributes": {
                    "title": title,
                    "visState": json.dumps(
                        {
                            "title": title,
                            "type": kind,
                            "params": {"addLegend": False, "addTimeMarker": False},
                            "aggs": aggregations,
                        }
                    ),
                    "uiStateJSON": "{}",
                    "kibanaSavedObjectMeta": {
                        "searchSourceJSON": json.dumps(
                            {
                                "index": "taller-data",
                                "query": {"query": query, "language": "kuery"},
                                "filter": [],
                            }
                        )
                    },
                },
            }
        )
        panels.append(
            {
                "version": "8.17.6",
                "type": "visualization",
                "panelIndex": str(index + 1),
                "gridData": {
                    "x": index * 16,
                    "y": 0,
                    "w": 16,
                    "h": 15,
                    "i": str(index + 1),
                },
                "embeddableConfig": {},
                "panelRefName": "panel_" + str(index),
            }
        )
    objects.append(
        {
            "type": "dashboard",
            "id": "taller-dashboard",
            "attributes": {
                "title": "Taller · salud del producto",
                "description": "Tráfico, latencia y checkouts.",
                "panelsJSON": json.dumps(panels),
                "optionsJSON": json.dumps(
                    {"useMargins": True, "syncColors": False, "hidePanelTitles": False}
                ),
                "timeRestore": True,
                "timeFrom": "now-24h",
                "timeTo": "now",
                "kibanaSavedObjectMeta": {
                    "searchSourceJSON": '{"query":{"query":"","language":"kuery"},"filter":[]}'
                },
            },
            "references": [
                {
                    "type": "visualization",
                    "id": "taller-" + d[0],
                    "name": "panel_" + str(i),
                }
                for i, d in enumerate(definitions)
            ],
        }
    )
    result = call(
        args.kibana, "/api/saved_objects/_bulk_create?overwrite=true", objects
    )
    failures = [r for r in result.get("saved_objects", []) if r.get("error")]
    if failures:
        raise RuntimeError(json.dumps(failures))
    rule = {
        "name": "Taller: errores HTTP",
        "rule_type_id": ".es-query",
        "consumer": "alerts",
        "schedule": {"interval": "1m"},
        "actions": [],
        "params": {
            "searchType": "esQuery",
            "esQuery": json.dumps(
                {"query": {"range": {"http.response.status_code": {"gte": 400}}}}
            ),
            "index": ["taller-*"],
            "timeField": "@timestamp",
            "timeWindowSize": 1,
            "timeWindowUnit": "m",
            "threshold": [3],
            "thresholdComparator": ">=",
            "size": 100,
            "aggType": "count",
            "groupBy": "all",
            "excludeHitsFromPreviousRun": False,
        },
    }
    try:
        call(args.kibana, "/api/alerting/rule/taller-errors", rule, "POST")
    except RuntimeError as exc:
        if "409" not in str(exc):
            raise
    print(
        "Data view, panel y regla configurados. Panel: "
        + args.kibana
        + "/app/dashboards#/view/taller-dashboard"
    )


if __name__ == "__main__":
    main()
