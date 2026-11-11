"""Controles de recuperación por lote y resolución compartida de enlaces."""

import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src" / "engine"))
import brain
import document_utils


class EngineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        corpus = root / "docs"
        corpus.mkdir()
        (corpus / "a.md").write_text(
            "# Acceso\nRoles y permisos. Ver [[b]].\n", encoding="utf-8"
        )
        (corpus / "b.md").write_text(
            "# Archivos\nLectura y acceso.\n", encoding="utf-8"
        )
        db = root / "index.sqlite"
        brain.index(corpus, db)
        self.connection, self.config, self.settings = brain.checked(db)
        self.addCleanup(self.connection.close)

    def test_batch_matches_single_queries_in_one_index_scan(self):
        queries = ["acceso lectura", "roles permisos", "sin coincidencia", ""]
        reference = [
            brain.ranking(self.connection, self.settings, query) for query in queries
        ]
        statements = []
        self.connection.set_trace_callback(statements.append)
        actual = brain.rank_queries(self.connection, self.settings, queries)
        self.connection.set_trace_callback(None)
        self.assertEqual(reference, actual)
        scans = [line for line in statements if "FROM search s JOIN chunks" in line]
        self.assertEqual(len(scans), 1)
        self.assertEqual(actual[0][0][0]["path"], "b.md")
        self.assertEqual(actual[2][0], [])

    def test_shared_link_lookup_has_same_resolution(self):
        lookup = document_utils.relation_index(self.connection)
        links = document_utils.relations(self.connection, "a.md", lookup)
        self.assertEqual(links, document_utils.relations(self.connection, "a.md"))
        self.assertEqual(links[0]["resolved"], ["b.md"])

    def test_verifier_counts_citations_separately_from_missing_fields(self):
        session = brain.session_load(None, self.config["revision"])
        brain.show(
            self.connection, self.config, session, "a.md", 1, 2, 10, brain.Budget(10000)
        )
        result = {
            "cases": [{"id": "C1", "sources": [{"path": "a.md", "start": 1, "end": 2}]}]
        }
        checked = brain.verify(self.connection, self.config, session, result)
        self.assertEqual(checked["invalid_or_unseen_citations"], 0)
        self.assertEqual(
            {item["reason"] for item in checked["failures"]},
            {"missing-oracle", "missing-expected"},
        )
        result["cases"][0]["sources"][0]["start"] = True
        self.assertEqual(
            brain.verify(self.connection, self.config, session, result)[
                "invalid_or_unseen_citations"
            ],
            1,
        )


if __name__ == "__main__":
    unittest.main()
