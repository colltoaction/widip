from yaml.reader import *
from yaml.scanner import *
from yaml.parser import *
from yaml.constructor import *
from yaml.resolver import *
from yaml.events import *
from yaml.tokens import *
from yaml.composer import ComposerError

from discopy.frobenius import Hypergraph as H, Id, Ob, Ty, Box, Spider

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
            b = H.from_box(Box(
                tag,
                node.dom,
                node.cod))
            node = compose_entry(b, node)

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
            node = H.id(Ty(str(event.value)))
        else:
            node = H.id()

        if anchor is not None:
            self.anchors[anchor] = node
        return node

    def compose_sequence_node(self, parent, anchor):
        start_event = self.get_event()
        tag = (start_event.tag or "").lstrip("!")
        node = None
        if anchor is not None:
            self.anchors[anchor] = node
        index = 0
        prev_value_tag, value_tag = None, None
        while not self.check_event(SequenceEndEvent):
            prev_value_tag = value_tag
            value_tag = (self.peek_event().tag or "").lstrip("!")
            value = self.compose_node(parent, index)
            if node is None:
                node = value
            else:
                if prev_value_tag:
                    b = H.from_box(Box(
                        prev_value_tag,
                        node.cod,
                        value.cod))
                    node = node >> b
                node = compose_entry(node, value)
            index += 1
        end_event = self.get_event()
        node.end_mark = end_event.end_mark

        if value_tag and not prev_value_tag:
            b = H.from_box(Box(
                value_tag,
                node.cod,
                node.cod))
            node = node >> b
        return node


    def compose_mapping_node(self, parent, anchor):
        start_event = self.get_event()
        tag = (start_event.tag or "").lstrip("!")
        node = H.id()
        if anchor is not None:
            self.anchors[anchor] = node
        keys, values = H.id(), H.id()
        while not self.check_event(MappingEndEvent):
            key_tag = (self.peek_event().tag or "").lstrip("!")
            key = self.compose_node(tag, None)
            value_tag = (self.peek_event().tag or "").lstrip("!")
            value = self.compose_node(tag, key)

            kv = None
            if key_tag and value_tag:
                bk = H.from_box(Box(
                    key_tag,
                    key.cod,
                    value.dom))
                bv = H.from_box(Box(
                    value_tag,
                    value.cod,
                    value.dom))
                key = key >> bk
                value = value >> bv
            elif key_tag:
                b = H.from_box(Box(
                    key_tag,
                    key.cod,
                    value.dom))
                value = value << b
                kv = compose_entry(key, value)
            elif value_tag:
                b = H.from_box(Box(
                    value_tag,
                    key.cod,
                    value.dom))
                value = b >> value
                kv = compose_entry(key, value)
            else:
                kv = compose_entry(key, value)
            keys @= key
            values @= value
            # TODO if tag
            node @= kv
        end_event = self.get_event()
        node.end_mark = end_event.end_mark
        # if tag:
        #     b = H.from_box(Box(
        #         tag,
        #         node.dom,
        #         node.dom))
        #     node = b >> node
        return node

def compose_entry(left, right):
    """connects two diagrams by removing the interfaces and connecting open wires"""
    if right == H.id():
        return left
    mid = Ty(*set(left.cod.inside + right.dom.inside))
    mid_to_left_ports = {
        t: tuple(i for i, lt in enumerate(left.cod) if lt == t)
        for t in mid}
    mid_to_right_ports = {
        t: tuple(i + len(left.cod) for i, lt in enumerate(right.dom) if lt == t)
        for t in mid}
    boxes = tuple(
        # special cases to avoid dots in drawings,
        Id() if len(mid_to_left_ports[t]) == len(mid_to_right_ports[t]) == 0
        else (
            Id(Ty(*tuple(t.name for _ in range(len(mid_to_right_ports[t])))))
            if len(mid_to_left_ports[t]) == len(mid_to_right_ports[t])
            else Spider(
                len(mid_to_left_ports[t]),
                len(mid_to_right_ports[t]),
                t))
        for t in mid)

    g = H(
        dom=left.cod, cod=right.dom,
        boxes=boxes,
        wires=(
            tuple(i for i in range(len(left.cod))), # input wires of the hypergraph
            tuple((mid_to_left_ports[t], mid_to_right_ports[t]) for t in mid),
            tuple(i + len(left.cod) for i in range(len(right.dom))), # input wires of the hypergraph
        ),
        # spider_types=mid,
    )
    g = left >> g >> right
    return g


class HypergraphLoader(Reader, Scanner, Parser, HypergraphComposer, SafeConstructor, Resolver):

    def __init__(self, stream):
        Reader.__init__(self, stream)
        Scanner.__init__(self)
        Parser.__init__(self)
        HypergraphComposer.__init__(self)
        SafeConstructor.__init__(self)
        Resolver.__init__(self)

