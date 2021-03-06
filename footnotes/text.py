from collections import defaultdict
from enum import Enum
import re

class Range(object):
    def __init__(self, i, j):
        self.i = i
        self.j = j

    @staticmethod
    def from_str(s):
        return Range(0, len(s))

    @staticmethod
    def from_match(match, group):
        return Range(match.start(group), match.end(group))

    def __str__(self):
        return 'Range({}, {})'.format(self.i, self.j)

    def __repr__(self):
        return str(self)

    def __len__(self):
        return self.j - self.i

    def copy(self):
        return Range(self.i, self.j)

    def slice(self):
        return slice(self.i, self.j)

    def combine(self, next):
        self.j = next.j

    def split(self, text, separator):
        start_idx = self.i
        tokens = []
        while True:
            end_idx = text.find(separator, start_idx, self.j)
            if end_idx < 0:
                yield Range(start_idx, self.j)
                break

            yield Range(start_idx, end_idx)
            start_idx = end_idx + len(separator)

Location = Enum('Location', 'TEXT TAIL')

def _str_insert(original, offset, fragment):
    return ''.join((original[:offset], fragment, original[offset:]))

class Insertion(object):
    """An object representing inserting `s` into text of `element` at `offset`."""

    def __init__(self, element, location, offset, s):
        self.element = element
        self.location = location
        self.offset = offset
        self.s = s

    def __str__(self):
        return repr(self)

    def __repr__(self):
        return 'Insertion({!r}, {!r}, {!r}, {!r})'.format(
            self.element, self.location, self.offset, self.s
        )

    def _fulltext(self):
        return (self.element.text or '') if self.location == Location.TEXT else (self.element.tail or '')

    def _set_fulltext(self, s):
        if self.location == Location.TEXT:
            self.element.text = s
        else:
            self.element.tail = s

    def apply(self, additional_offset=0):
        self._set_fulltext(_str_insert(self._fulltext(), self.offset + additional_offset, self.s))

    @staticmethod
    def apply_all(insertions):
        # First, group by element and location. Multiple insertions to the same element disrupt offset math.
        grouped = defaultdict(lambda: [])
        for i in insertions:
            key = i.element, i.location
            grouped[key].append(i)

        for key, group in grouped.items():
            group.sort(key=lambda i: i.offset)
            accumulated_offset = 0
            for i in group:
                i.apply(accumulated_offset)
                accumulated_offset += len(i.s)

class TextRef(object):
    """A slice of the text/tail (`location`) of `element`."""

    def __init__(self, element, location, range):
        self.element = element
        self.location = location
        self.range = range

    @staticmethod
    def from_text(element):
        return TextRef(element, Location.TEXT, Range(0, len(element.text or '')))

    @staticmethod
    def from_tail(element):
        return TextRef(element, Location.TAIL, Range(0, len(element.tail or '')))

    def fulltext(self):
        return (self.element.text or '') if self.location == Location.TEXT else (self.element.tail or '')

    def __str__(self):
        return self.fulltext()[self.range.slice()]

    def __repr__(self):
        return 'TextRef({!r}, {!r}, {!r})'.format(self.element, self.location, self.range)

    def __len__(self):
        return len(self.range)

    def __getitem__(self, key):
        if isinstance(key, slice):
            if key.step is not None and key.step != 1:
                raise TypeError('TextObject slice step not supported.')

            start, stop = key.start, key.stop
            if start is None: start = 0
            if start < 0: start += len(self)
            if stop is None: stop = len(self)
            if stop < 0: stop += len(self)

            new_range = Range(self.range.i + start, self.range.i + stop)
            return TextRef(self.element, self.location, new_range)
        else:
            raise TypeError('TextObject indices must be slices.')

    def insert(self, offset, s):
        """
        Make an object representing inserting string `s` at `offset` into this ref's underlying XML.
        """
        assert 0 <= offset and offset <= len(self)
        return Insertion(self.element, self.location, self.range.i + offset, s)
