"""Tests for Datadoc."""
from src.core import Datadoc
def test_init(): assert Datadoc().get_stats()["ops"] == 0
def test_op(): c = Datadoc(); c.analyze(x=1); assert c.get_stats()["ops"] == 1
def test_multi(): c = Datadoc(); [c.analyze() for _ in range(5)]; assert c.get_stats()["ops"] == 5
def test_reset(): c = Datadoc(); c.analyze(); c.reset(); assert c.get_stats()["ops"] == 0
def test_service_name(): c = Datadoc(); r = c.analyze(); assert r["service"] == "datadoc"
