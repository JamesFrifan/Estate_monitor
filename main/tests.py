"""Testing code."""

import tempfile
import unittest
import client as emr


class TestTuning(unittest.TestCase):
    def setUp(self):
        self.content_demo = "a_1,a_2,b_1"

    def test_01_set_preferred_properties_1(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(f"{tmpdir}/preference.txt", "w+") as f:
                f.write(self.content_demo)
            emr.set_preferred_properties(tmpdir + "/", "b_2")
            with open(f"{tmpdir}/preference.txt", "r") as f:
                result = sorted(f.read().split(","))
            expect = ["a_1", "a_2", "b_1", "b_2"]
            self.assertEqual(expect, result)

    def test_02_set_preferred_properties_2(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(f"{tmpdir}/preference.txt", "w+") as f:
                f.write(self.content_demo)
            emr.set_preferred_properties(tmpdir + "/", ["b_2", "a_3"])
            with open(f"{tmpdir}/preference.txt", "r") as f:
                result = sorted(f.read().split(","))
            expect = ["a_1", "a_2", "a_3", "b_1", "b_2"]
            self.assertEqual(expect, result)

    def test_03_set_preferred_properties_3(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(f"{tmpdir}/preference.txt", "w+") as f:
                f.write(self.content_demo)
            emr.set_preferred_properties(tmpdir + "/", "a_2", False)
            with open(f"{tmpdir}/preference.txt", "r") as f:
                result = sorted(f.read().split(","))
            expect = ["a_1", "b_1"]
            self.assertEqual(expect, result)

    def test_04_set_preferred_properties_4(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(f"{tmpdir}/preference.txt", "w+") as f:
                f.write(self.content_demo)
            emr.set_preferred_properties(tmpdir + "/", ["a_2", "a_1"], False)
            with open(f"{tmpdir}/preference.txt", "r") as f:
                result = sorted(f.read().split(","))
            expect = ["b_1"]
            self.assertEqual(expect, result)

    def test_05_set_ignored_streets_1(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(f"{tmpdir}/ignore_street.txt", "w+") as f:
                f.write(self.content_demo)
            emr.set_ignored_streets(tmpdir + "/", "b_2")
            with open(f"{tmpdir}/ignore_street.txt", "r") as f:
                result = sorted(f.read().split(","))
            expect = ["a_1", "a_2", "b_1", "b_2"]
            self.assertEqual(expect, result)

    def test_06_set_ignored_streets_2(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(f"{tmpdir}/ignore_street.txt", "w+") as f:
                f.write(self.content_demo)
            emr.set_ignored_streets(tmpdir + "/", ["b_2", "a_3"])
            with open(f"{tmpdir}/ignore_street.txt", "r") as f:
                result = sorted(f.read().split(","))
            expect = ["a_1", "a_2", "a_3", "b_1", "b_2"]
            self.assertEqual(expect, result)

    def test_07_set_ignored_streets_3(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(f"{tmpdir}/ignore_street.txt", "w+") as f:
                f.write(self.content_demo)
            emr.set_ignored_streets(tmpdir + "/", "a_2", False)
            with open(f"{tmpdir}/ignore_street.txt", "r") as f:
                result = sorted(f.read().split(","))
            expect = ["a_1", "b_1"]
            self.assertEqual(expect, result)

    def test_08_set_ignored_streets_4(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(f"{tmpdir}/ignore_street.txt", "w+") as f:
                f.write(self.content_demo)
            emr.set_ignored_streets(tmpdir + "/", ["a_2", "a_1"], False)
            with open(f"{tmpdir}/ignore_street.txt", "r") as f:
                result = sorted(f.read().split(","))
            expect = ["b_1"]
            self.assertEqual(expect, result)
