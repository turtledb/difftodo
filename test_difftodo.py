# Copyright (c) 2009 Jonathan M. Lange <jml@mumak.net>

"""Tests for extracting TODOs from comments in Python source code."""


from bzrlib import patches
from bzrlib.tests import TestCase

from difftodo import Comment, get_comments_from_diff, Todo, todo_from_comment


class TestComment(TestCase):
    """Tests for the `Comment` class."""

    def test_construction(self):
        comment = Comment("foo.py", 42, ["# hahaha\n", "# hohoho\n"])
        self.assertEqual("foo.py", comment.filename)
        self.assertEqual(42, comment.start_line)
        self.assertEqual(["# hahaha\n", "# hohoho\n"], comment.raw_lines)

    def test_equality(self):
        comment1 = Comment("foo.py", 42, ["# hahaha\n", "# hohoho\n"])
        comment2 = Comment("foo.py", 42, ["# hahaha\n", "# hohoho\n"])
        self.assertEqual(comment1, comment2)
        self.assertEqual(comment2, comment1)

    def test_trailing_filename_discarded(self):
        comment = Comment("a\t2009-01-17 02:47:31 +0000", 42, ["# foo"])
        self.assertEqual('a', comment.filename)

    def test_lines(self):
        # The text attribute gets rid of the hash character and just has the
        # text.
        comment = Comment("foo.py", 42, ["# hahaha\n", "# hohoho  \n"])
        self.assertEqual(["hahaha", "hohoho"], list(comment.lines))

    def test_lines_disregards_pre_comment_indentation(self):
        comment = Comment("foo.py", 42, ["# hahaha\n", "    # hohoho  \n"])
        self.assertEqual(["hahaha", "hohoho"], list(comment.lines))

    def test_lines_preserves_post_comment_indentation(self):
        comment = Comment("foo.py", 42, ["# hahaha\n", "#     hohoho  \n"])
        self.assertEqual(["hahaha","    hohoho"], list(comment.lines))

    def test_str(self):
        comment = Comment("foo.py", 42, ["# hahaha\n", "# hohoho\n"])
        self.assertEqual(
            ("foo.py:42:\n"
             "  hahaha\n"
             "  hohoho\n"), str(comment))

    def test_append(self):
        comment = Comment("foo.py", 42, ["# hahaha\n"])
        comment.append("# hohoho\n")
        self.assertEqual(["# hahaha\n", "# hohoho\n"], comment.raw_lines)

    def test_contains(self):
        # We can look for text in comments.
        comment = Comment("foo.py", 42, ["# hahaha\n"])
        self.assertTrue("ha" in comment)
        self.assertTrue("# h" not in comment)


class TestTodo(TestCase):

    def test_constructor(self):
        todo = Todo('filename.py', 32, ['XXX: hello', 'bar'])
        self.assertEqual('filename.py', todo.filename)
        self.assertEqual(32, todo.start_line)
        self.assertEqual(['XXX: hello', 'bar'], todo.lines)

    def test_str(self):
        todo = Todo('filename.py', 32, ['XXX: hello', 'bar'])
        self.assertEqual('filename.py:32:\n  XXX: hello\n  bar\n', str(todo))

    def test_equality(self):
        todo1 = Todo('filename.py', 32, ['XXX: hello', 'bar'])
        todo2 = Todo('filename.py', 32, ['XXX: hello', 'bar'])
        self.assertEqual(todo2, todo1)
        self.assertEqual(todo1, todo2)


class TestTodoFromComment(TestCase):

    def makeComment(self, comment_text):
        return Comment(
            'arbitrary.py', 1, ['# ' + line for line in comment_text])

    def test_no_todos(self):
        comment = self.makeComment(['hello australia!'])
        todos = list(todo_from_comment(comment, ['XXX', 'TODO']))
        self.assertEqual([], todos)

    def test_one_todo(self):
        comment = self.makeComment(['XXX: hello australia!'])
        todos = list(todo_from_comment(comment, ['XXX', 'TODO']))
        self.assertEqual(
            [Todo(
                comment.filename, comment.start_line,
                ['XXX: hello australia!'])], todos)

    def test_one_todo_embedded(self):
        comment = self.makeComment([
            'first line',
            'XXX: hello australia!',
            'second line'])
        todos = list(todo_from_comment(comment, ['XXX', 'TODO']))
        # XXX: Maybe we want to change this so that the todo starts at the
        # XXX or TODO.
        self.assertEqual(
            [Todo(
                comment.filename, comment.start_line + 1,
                ['XXX: hello australia!', 'second line'])],
            todos)

    def test_two_todos(self):
        comment = self.makeComment([
            'XXX: first line',
            'TODO: hello australia!',
            'second line'])
        todos = list(todo_from_comment(comment, ['XXX', 'TODO']))
        # XXX: Maybe we want to change this so that the todo starts at the
        # XXX or TODO.
        self.assertEqual(
            [Todo(comment.filename, comment.start_line, ['XXX: first line']),
             Todo(comment.filename, comment.start_line + 1,
                  ['TODO: hello australia!', 'second line']),], todos)


class TestCommentsFromDiff(TestCase):

    def assertCommentsEqual(self, patch, comments):
        # Assert that the raw text of the comments added in 'patch' is
        # 'comments'.
        found_comments = get_comments_from_diff(patch)
        self.assertEqual(
            comments,
            [''.join(line.lstrip() for line in comment.raw_lines)
             for comment in found_comments])

    def parse_diff(self, diff_text):
        diff_lines = (line + '\n' for line in diff_text.splitlines())
        return patches.parse_patches(diff_lines)

    def test_no_comments(self):
        # If the diff doesn't change any comments, then get_comments won't
        # yield anything.
        diff = ("""\
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
""")
        patch = self.parse_diff(diff)
        self.assertCommentsEqual(patch, [])

    def test_comment_added(self):
        # If the diff adds a comment, then it's in the stream.
        diff = ("""\
=== modified file 'a'
--- a	2009-01-17 02:47:22 +0000
+++ a	2009-01-17 02:47:31 +0000
@@ -6,4 +6,5 @@
 class TestBar(unittest.TestCase):
 
     def test_bar(self):
+        # This test is going to be awesome.
         pass
""")
        patch = self.parse_diff(diff)
        self.assertCommentsEqual(
            patch, ["# This test is going to be awesome.\n"])

    def test_comment_metadata(self):
        diff = ("""\
=== modified file 'a'
--- a	2009-01-17 02:47:22 +0000
+++ a	2009-01-17 02:47:31 +0000
@@ -6,4 +6,5 @@
 class TestBar(unittest.TestCase):
 
     def test_bar(self):
+        # This test is going to be awesome.
         pass
""")
        patch = self.parse_diff(diff)
        comments = list(get_comments_from_diff(patch))
        self.assertEqual(
            [Comment('a', 8,
                     ['        # This test is going to be awesome.\n'])],
            comments)

    def test_comment_removed(self):
        # If the diff removes a comment, then it's not in the stream.
        diff = ("""\
=== modified file 'a'
--- a	2009-01-17 02:47:22 +0000
+++ a	2009-01-17 02:47:31 +0000
@@ -6,4 +6,5 @@
 class TestBar(unittest.TestCase):
 
     def test_bar(self):
-        # This test is going to be awesome.
         pass
""")
        patch = self.parse_diff(diff)
        self.assertCommentsEqual(patch, [])

    def test_multiline_comment_added(self):
        diff = ("""\
=== modified file 'a'
--- a	2009-01-17 02:47:22 +0000
+++ a	2009-01-17 02:47:31 +0000
@@ -6,4 +6,5 @@
 class TestBar(unittest.TestCase):
 
     def test_bar(self):
+        # This test is going to be awesome.
+        # So awesome, I cannot tell you how awesome.
         pass
""")
        patch = self.parse_diff(diff)
        self.assertCommentsEqual(patch, [
            "# This test is going to be awesome.\n"
            "# So awesome, I cannot tell you how awesome.\n"])

    def test_multiple_comments_added(self):
        diff = ("""\
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

""")
        patch = self.parse_diff(diff)
        self.assertCommentsEqual(patch, [
            ("# This test is going to be awesome.\n"
             "# So awesome, I cannot tell you how awesome.\n"),
            "# Awesome, I tell you.\n"])

    def test_comment_modified(self):
        diff = ("""\
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

""")
        patch = self.parse_diff(diff)
        self.assertCommentsEqual(patch, ["# Line 1\n# Line 2\n# Line 3\n"])

    def test_comment_appended(self):
        diff = ("""\
=== modified file 'a'
--- a	2009-01-17 05:07:59 +0000
+++ a	2009-01-17 05:08:20 +0000
@@ -9,4 +9,5 @@
         # Line 1
         # Line 2
         # Line 3
+        # Line 4
         pass
""")
        patch = self.parse_diff(diff)
        self.assertCommentsEqual(
            patch, ["# Line 1\n# Line 2\n# Line 3\n# Line 4\n"])

    def test_comment_prepended(self):
        diff = ("""\
=== modified file 'a'
--- a	2009-01-17 05:07:59 +0000
+++ a	2009-01-17 05:10:39 +0000
@@ -6,6 +6,7 @@
 class TestBar(unittest.TestCase):
 
     def test_bar(self):
+        # Line 0
         # Line 1
         # Line 2
         # Line 3

""")
        patch = self.parse_diff(diff)
        self.assertCommentsEqual(
            patch, ["# Line 0\n# Line 1\n# Line 2\n# Line 3\n"])
