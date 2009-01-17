# Copyright (c) 2009 Jonathan M. Lange <jml@mumak.net>

"""Tests for extracting TODOs from comments in Python source code."""


from bzrlib import patches
from bzrlib.tests import TestCase

from difftodo import get_comments_from_diff


class TestCommentsFromDiff(TestCase):

    def parse_diff(self, diff_text):
        diff_lines = (line + '\n' for line in diff_text.splitlines())
        return patches.parse_patches(diff_lines)

    def test_no_comments(self):
        # If the diff doesn't change any comments, then get_comments won't
        # yield anything.
        diff = """\
=== modified file 'a'
--- a	2009-01-17 02:28:16 +0000
+++ a	2009-01-17 02:28:21 +0000
@@ -3,7 +3,7 @@
 import unittest
 
 
-class TestFoo(unittest.TestCase):
+class TestBar(unittest.TestCase):
 
-    def test_foo(self):
+    def test_bar(self):
         pass
"""
        patch = self.parse_diff(diff)
        self.assertEqual([], list(get_comments_from_diff(patch)))

    def test_comment_added(self):
        # If the diff adds a comment, then it's in the stream.
        diff = """\
=== modified file 'a'
--- a	2009-01-17 02:47:22 +0000
+++ a	2009-01-17 02:47:31 +0000
@@ -6,4 +6,5 @@
 class TestBar(unittest.TestCase):
 
     def test_bar(self):
+        # This test is going to be awesome.
         pass
"""
        patch = self.parse_diff(diff)
        comments = list(get_comments_from_diff(patch))
        self.assertEqual(["# This test is going to be awesome.\n"], comments)

    def test_comment_removed(self):
        # If the diff removes a comment, then it's not in the stream.
        diff = """\
=== modified file 'a'
--- a	2009-01-17 02:47:22 +0000
+++ a	2009-01-17 02:47:31 +0000
@@ -6,4 +6,5 @@
 class TestBar(unittest.TestCase):
 
     def test_bar(self):
-        # This test is going to be awesome.
         pass
"""
        patch = self.parse_diff(diff)
        comments = list(get_comments_from_diff(patch))
        self.assertEqual([], comments)

    def test_multiline_comment_added(self):
        diff = """\
=== modified file 'a'
--- a	2009-01-17 02:47:22 +0000
+++ a	2009-01-17 02:47:31 +0000
@@ -6,4 +6,5 @@
 class TestBar(unittest.TestCase):
 
     def test_bar(self):
+        # This test is going to be awesome.
+        # So awesome, I cannot tell you how awesome.
         pass
"""
        patch = self.parse_diff(diff)
        comments = list(get_comments_from_diff(patch))
        self.assertEqual([
            "# This test is going to be awesome.\n"
            "# So awesome, I cannot tell you how awesome.\n"], comments)

    def test_multiple_comments_added(self):
        diff = """\
=== modified file 'a'
--- a	2009-01-17 02:47:22 +0000
+++ a	2009-01-17 03:09:45 +0000
@@ -6,4 +6,7 @@
 class TestBar(unittest.TestCase):
 
     def test_bar(self):
+        # This test is going to be awesome.
+        # So awesome, I cannot tell you how awesome.
         pass
+    # Awesome, I tell you.

"""
        patch = self.parse_diff(diff)
        comments = list(get_comments_from_diff(patch))
        self.assertEqual([
            ("# This test is going to be awesome.\n"
             "# So awesome, I cannot tell you how awesome.\n"),
            "# Awesome, I tell you.\n"], comments)

    def test_comment_modified(self):
        diff = """\
=== modified file 'a'
--- a	2009-01-17 04:04:42 +0000
+++ a	2009-01-17 04:04:48 +0000
@@ -7,6 +7,6 @@
 
     def test_bar(self):
         # Line 1
-        # Lone 2
+        # Line 2
         # Line 3
         pass

"""
        patch = self.parse_diff(diff)
        comments = list(get_comments_from_diff(patch))
        self.assertEqual(["# Line 1\n# Line 2\n# Line 3\n"], comments)

