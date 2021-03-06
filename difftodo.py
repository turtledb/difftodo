# Copyright (c) 2009 Jonathan M. Lange <jml@mumak.net>

"""A library for extracting TODOs from comments in Python source code."""

__all__ = [
    'Comment',
    'get_comments_from_diff',
    'Todo',
    'todo_from_comment',
    'todos_from_comments',
    ]

from bzrlib import patches

from extensions import filter_none


class Comment(object):
    """A comment block in a Python source file."""

    def __init__(self, filename, start_line, raw_lines):
        self.filename = filename.split('\t')[0]
        self.start_line = start_line
        self.raw_lines = raw_lines

    @classmethod
    def is_comment(self, line):
        return line.lstrip().startswith('#')

    def __eq__(self, other):
        return all([
            self.filename == other.filename,
            self.start_line == other.start_line,
            self.raw_lines == other.raw_lines])

    def __ne__(self, other):
        return not (self == other)

    def __repr__(self):
        return '%s(%r, %s, %s)' % (
            self.__class__.__name__,
            self.filename,
            self.start_line,
            self.raw_lines)

    def __str__(self):
        lines = ["%s:%s:" % (self.filename, self.start_line)]
        lines.extend(["  " + line for line in self.lines])
        lines.append('')
        return '\n'.join(lines)

    def __contains__(self, text):
        return text in self.text

    def append(self, new_line):
        self.raw_lines.append(new_line)

    @property
    def lines(self):
        return (
            line.lstrip()[2:].rstrip()
            for line in self.raw_lines)

    @property
    def text(self):
        return '\n'.join(self.lines)


class Todo(object):

    def __init__(self, filename, start_line, lines):
        self.filename = filename
        self.start_line = start_line
        self.lines = lines

    def __repr__(self):
        return '%s(%r, %r, %r)' % (
            self.__class__.__name__,
            self.filename, self.start_line, self.lines)

    def __str__(self):
        lines = ["%s:%s:" % (self.filename, self.start_line + 1)]
        lines.extend(["  " + line for line in self.lines])
        lines.append('')
        return '\n'.join(lines)

    def __eq__(self, other):
        return all([
            self.filename == other.filename,
            self.start_line == other.start_line,
            self.lines == other.lines])

    def __ne__(self, other):
        return not (self == other)


def todo_from_comment(comment, tags):
    """Yield all todos hiding in 'comment'."""
    lines = list(comment.lines)
    current_todo_start = None

    for offset, line in enumerate(lines):
        if any(tag in line for tag in tags):
            if current_todo_start is not None:
                yield Todo(
                    comment.filename,
                    comment.start_line + current_todo_start,
                    lines[current_todo_start:offset])
            current_todo_start = offset
    if current_todo_start is not None:
        yield Todo(
            comment.filename,
            comment.start_line + current_todo_start,
            lines[current_todo_start:])


def todos_from_comments(comments, tags):
    for comment in comments:
        for todo in todo_from_comment(comment, tags):
            yield todo


class PatchParser(object):
    """An event parser for patches."""

    def __init__(self, patch):
        self.patch = patch
        self._hunks = getattr(patch, 'hunks', [])

    def _iter_patch_lines(self):
        for hunk in self._hunks:
            pos = hunk.mod_pos - 1
            for line in hunk.lines:
                yield (pos, line)
                pos += 1

    def _get_handler_for_line(self, line):
        if isinstance(line, patches.ContextLine):
            return self.context_line_received
        elif isinstance(line, patches.InsertLine):
            return self.insert_line_received
        elif isinstance(line, patches.RemoveLine):
            return self.remove_line_received
        else:
            raise AssertionError("Cannot handle %r" % (line,))

    @filter_none
    def parse(self):
        for pos, line in self._iter_patch_lines():
            for result in self.line_received(pos, line):
                yield result
        for result in self.patch_finished():
            yield result

    def patch_finished(self):
        """Called when patch parsing is finished."""

    def line_received(self, line_number, line):
        handler = self._get_handler_for_line(line)
        yield handler(line_number, line.contents)

    def insert_line_received(self, line_number, line_contents):
        """Called when a insert line of diff is received."""

    def context_line_received(self, line_number, line_contents):
        """Called when a context line of diff is received."""

    def remove_line_received(self, line_number, line_contents):
        """Called when a remove line of diff is received."""


class CommentParser(PatchParser):
    """A patch parser that yields comments added in a patch."""

    def __init__(self, patch):
        super(CommentParser, self).__init__(patch)
        self._insert_in_comment = False
        self._current_comment = None

    def is_comment(self, contents):
        return Comment.is_comment(contents)

    def _end_comment(self):
        if self._current_comment is None:
            return
        current_comment, self._current_comment = self._current_comment, None
        if not self._insert_in_comment:
            return
        self._insert_in_comment = False
        return current_comment

    def _add_to_comment(self, line_number, contents):
        if self._current_comment is None:
            self._current_comment = Comment(
                self.patch.newname, line_number, [contents])
        else:
            self._current_comment.append(contents)

    def line_received(self, line_number, line):
        if self.is_comment(line.contents):
            upcall = super(CommentParser, self).line_received
            for result in upcall(line_number, line):
                yield result
        else:
            yield self._end_comment()

    def insert_line_received(self, line_number, contents):
        self._insert_in_comment = True
        self._add_to_comment(line_number, contents)

    def context_line_received(self, line_number, contents):
        self._add_to_comment(line_number, contents)

    def patch_finished(self):
        yield self._end_comment()


def get_comments_from_diff(patches):
    for patch in patches:
        for comment in CommentParser(patch).parse():
            yield comment
