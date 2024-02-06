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
        tag = self.peek_event().tag
        node = self.compose_node(tag, None)

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
        tag = event.tag
        if event.value and tag:
            node = H.from_box(Box(
                tag.lstrip("!"),
                Ty(str(event.value)),
                Ty(str(event.value))))
        elif event.value:
            node = H.id(Ty(str(event.value)))
        elif tag:
            node = H.from_box(Box(
                tag.lstrip("!"),
                Ty(""),
                Ty("")))
        elif not event.value and not tag:
            node = H.id()
        
        if anchor is not None:
            self.anchors[anchor] = node
        return node

    def compose_sequence_node(self, parent, anchor):
        start_event = self.get_event()
        tag = start_event.tag
        tag = tag.lstrip("!") if tag else ""
        node = None
        if anchor is not None:
            self.anchors[anchor] = node
        index = 0
        while not self.check_event(SequenceEndEvent):
            value_tag = self.peek_event().tag
            value_tag = value_tag.lstrip("!") if value_tag else ""
            value = self.compose_node(parent, index)
            if node is None:
                node = value
            else:
                node = compose_entry(node, value)
            index += 1
        end_event = self.get_event()
        node.end_mark = end_event.end_mark

        if tag:
            b = H.from_box(Box(
                tag.lstrip("!"),
                node.dom,
                node.cod))
            # spiders should be less intrusive
            node = H.spiders(1, 2, node.dom) \
                >> b @ node \
                >> H.spiders(2, 1, node.cod)
        return node


    def compose_mapping_node(self, parent, anchor):
        start_event = self.get_event()
        tag = start_event.tag
        if tag is None:
            tag = ""
        tag = tag.lstrip("!")
        node = H.id()
        if anchor is not None:
            self.anchors[anchor] = node
        keys, values = H.id(), H.id()
        while not self.check_event(MappingEndEvent):
            key = self.compose_node(tag, None)
            value = self.compose_node(tag, key)
            keys @= key
            values @= value
            # TODO if tag
            kv = compose_entry(key, value)
            node @= kv
        end_event = self.get_event()
        node.end_mark = end_event.end_mark
        if tag:
            b = H.from_box(Box(
                tag,
                node.dom,
                node.cod))
            node = compose_entry(b, node)
        return node

def compose_entry(k, v):
    """connects two diagrams by creating spiders between them"""
    if v == H.id():
        return k
    names = {x.name for x in k.dom.inside + k.cod.inside + v.dom.inside + v.cod.inside}
    # scalar_spiders = {
    #     n.name
    #     for s in k.scalar_spiders + v.scalar_spiders
        # for n in s.inside}
    names = tuple(sorted(names))
    io_names = tuple(sorted({x.name for x in k.dom.inside + v.cod.inside}))
    spider_types = {n: Ty(n) if n in io_names else Ty("") for n in names}
    g = H(
        dom=k.cod, cod=v.dom,
        boxes=(),
        wires=(
            # tuple(Ob(s.name) for s in k.cod.inside), # input wires of the hypergraph
            tuple(x.name for x in k.cod.inside), # input wires of the hypergraph
            (
            ),#tuple(((s,),(s,)) for s in spider_types),
            # tuple(Ob(s.name) for s in v.dom.inside), # input wires of the hypergraph
            tuple(x.name for x in v.dom.inside), # input wires of the hypergraph
        ),
        # spider_types=spider_types,
    )
    g = k >> g >> v
    return g


class HypergraphLoader(Reader, Scanner, Parser, HypergraphComposer, SafeConstructor, Resolver):

    def __init__(self, stream):
        Reader.__init__(self, stream)
        Scanner.__init__(self)
        Parser.__init__(self)
        HypergraphComposer.__init__(self)
        SafeConstructor.__init__(self)
        Resolver.__init__(self)

