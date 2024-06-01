from yaml.reader import *
from yaml.scanner import *
from yaml.parser import *
from yaml.constructor import *
from yaml.resolver import *
from yaml.events import *
from yaml.tokens import *
from yaml.composer import ComposerError

from discopy.frobenius import Hypergraph as H, Id, Ob, Ty, Box, Spider

from .composing import glue_diagrams

class HypergraphComposer:

    def __init__(self):
        self.anchors = {}

    def check_node(self):
        # Drop the STREAM-START event.
        if self.check_event(StreamStartEvent):
            self.get_event()

        # If there are more documents available?
        return not self.check_event(StreamEndEvent)

    def get_node(self):
        # Get the root node of the next document.
        if not self.check_event(StreamEndEvent):
            return self.compose_document()

    def get_single_node(self):
        # Drop the STREAM-START event.
        self.get_event()

        # Compose a document if the stream is not empty.
        document = None
        if not self.check_event(StreamEndEvent):
            document = self.compose_document()

        # Ensure that the stream contains no more documents.
        if not self.check_event(StreamEndEvent):
            event = self.get_event()
            raise ComposerError("expected a single document in the stream",
                    document.start_mark, "but found another document",
                    event.start_mark)

        # Drop the STREAM-END event.
        self.get_event()

        return document

    def compose_document(self):
        # Drop the DOCUMENT-START event.
        self.get_event()

        # Compose the root node.
        tag = (self.peek_event().tag or "").lstrip("!")
        node = self.compose_node(tag, None)
        if tag:
            # b = Id().tensor(*(Spider(0, 1, x) for x in node.dom))
            b = Box(tag, node.dom, node.dom)
            node = b >> node

        # Drop the DOCUMENT-END event.
        self.get_event()

        self.anchors = {}
        return node

    def compose_node(self, parent, index):
        if self.check_event(AliasEvent):
            event = self.get_event()
            anchor = event.anchor
            if anchor not in self.anchors:
                raise ComposerError(None, None, "found undefined alias %r"
                        % anchor, event.start_mark)
            return self.anchors[anchor]
        event = self.peek_event()
        anchor = event.anchor
        if anchor is not None:
            if anchor in self.anchors:
                raise ComposerError("found duplicate anchor %r; first occurrence"
                        % anchor, self.anchors[anchor].start_mark,
                        "second occurrence", event.start_mark)
        self.descend_resolver(parent, index)
        if self.check_event(ScalarEvent):
            node = self.compose_scalar_node(parent, anchor)
        elif self.check_event(SequenceStartEvent):
            node = self.compose_sequence_node(parent, anchor)
        elif self.check_event(MappingStartEvent):
            node = self.compose_mapping_node(parent, anchor)
        self.ascend_resolver()
        return node

    def compose_scalar_node(self, parent, anchor):
        event = self.get_event()
        if event.value:
            node = Id(str(event.value))
        else:
            node = Id("")

        if anchor is not None:
            self.anchors[anchor] = node
        return node

    def compose_sequence_node(self, parent, anchor):
        """becomes a set of equations l0->l1, l1->l2,... in a symmetric monoidal theory"""
        start_event = self.get_event()
        tag = (start_event.tag or "").lstrip("!")
        if anchor is not None:
            self.anchors[anchor] = node
        index = 0
        node = None
        prev_value_tag = None
        while not self.check_event(SequenceEndEvent):
            value_tag = (self.peek_event().tag or "").lstrip("!")
            value = self.compose_node(parent, index)
            if index == 0:
                node = value
            else:
                if prev_value_tag:
                    b = Box(prev_value_tag, node.cod, node.cod)
                    node = node >> b
                node = glue_diagrams(node, value)
            prev_value_tag = value_tag
            index += 1
        end_event = self.get_event()
        node.end_mark = end_event.end_mark

        if index == 0:
            return Id()
        elif prev_value_tag:
            b = Box(prev_value_tag, node.cod, node.cod)
            node = node >> b
        return node


    def compose_mapping_node(self, parent, anchor):
        """becomes a set of equations l->r in a symmetric monoidal theory"""
        start_event = self.get_event()
        tag = (start_event.tag or "").lstrip("!")
        index = 0
        node = None
        if anchor is not None:
            self.anchors[anchor] = node
        while not self.check_event(MappingEndEvent):
            left_tag = (self.peek_event().tag or "").lstrip("!")
            left = self.compose_node(tag, None)
            right_tag = (self.peek_event().tag or "").lstrip("!")
            right = self.compose_node(tag, left)

            kv = None
            if left_tag and right_tag:
                bk = Box(left_tag, left.cod, right.dom)
                bv = Box(right_tag, right.cod, right.dom)
                left = left >> bk
                right = right >> bv
                kv = glue_diagrams(left, right)
            elif left_tag and right == Id(Ty("")):
                # empty-valued entry case
                # left = Id().tensor(*(Spider(0, 1, x) for x in left.dom))
                b = Box(left_tag, left.cod, right.dom)
                kv = left >> b >> right
            elif left_tag:
                b = Box(left_tag, left.cod, right.dom)
                kv = left >> b >> right
            elif right_tag:
                b = Box(right_tag, left.cod, right.dom)
                kv = left >> b >> right
            elif right == Id(Ty("")):
                # empty-valued entry case
                kv = left
            else:
                kv = glue_diagrams(left, right)
            
            if index == 0:
                node = kv
            else:
                node @= kv
            index += 1
        _ = self.get_event()
        if index == 0:
            return Id()
        return node


class HypergraphLoader(Reader, Scanner, Parser, HypergraphComposer, SafeConstructor, Resolver):

    def __init__(self, stream):
        Reader.__init__(self, stream)
        Scanner.__init__(self)
        Parser.__init__(self)
        HypergraphComposer.__init__(self)
        SafeConstructor.__init__(self)
        Resolver.__init__(self)

