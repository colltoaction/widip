from yaml import compose_all as yaml_compose_all
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


def compose_all(stream):
    diagrams = yaml_compose_all(stream, Loader=HypergraphLoader)
    # glueing between diagrams
    gbox = Box("glue_diagrams", Ty("left") @ Ty("right"), Ty(""))
    diagrams = Id().tensor(*diagrams)
    cbox = Box("compose_node", Ty("stream"), diagrams.dom)
    return diagrams

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

        node = self.compose_node(None, None)

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
        tag = event_tag(event) or ""#"str"
        if event.value and tag:
            node = Box(tag, Ty(str(event.value)), Ty(str(event.value)))
        elif event.value:
            node = Id(str(event.value))
        elif event.tag:
            node = Box(tag, Ty(""), Ty(""))
        # elif not event.tag:
        #     return Id("")
        else:
            node = Id("")

        if anchor is not None:
            self.anchors[anchor] = node
        return node

    def compose_sequence_node(self, parent, anchor):
        """becomes a set of equations l0->l1, l1->l2,... in a symmetric monoidal theory"""
        start_event = self.get_event()
        tag = event_tag(start_event) or ""#"seq"
        if anchor is not None:
            self.anchors[anchor] = node
        index = 0
        node = None
        # prev_value_tag = None
        while not self.check_event(SequenceEndEvent):
            # value_tag = event_tag(self.peek_event())
            value = self.compose_node(parent, index)
            if index == 0:
                node = value
            else:
                # if prev_value_tag:
                #     b = Box(prev_value_tag, node.cod, node.cod)
                #     node = node >> b
                node = glue_diagrams(node, value)
            # prev_value_tag = value_tag
            index += 1
        end_event = self.get_event()
        node.end_mark = end_event.end_mark

        if index == 0:
            return Id()
        # elif prev_value_tag:
        #     b = Box(prev_value_tag, node.cod, node.cod)
        # node = node >> b
        return node


    def compose_mapping_node(self, parent, anchor):
        """becomes a set of equations l->r in a symmetric monoidal theory"""
        start_event = self.get_event()
        tag = event_tag(start_event) or "map"
        index = 0
        node = None
        lefts, rights = [], []
        if anchor is not None:
            self.anchors[anchor] = node
        while not self.check_event(MappingEndEvent):

            # TODO mapping entries

            # left_tag = event_tag(self.peek_event())
            left = self.compose_node(tag, None)
            # right_tag = event_tag(self.peek_event())
            right = self.compose_node(tag, left)

            # e.g a set
            if right == Id(""):
                kv = left
            else:
                kv = left >> Box(tag, left.cod, right.dom) >> right

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

def event_tag(event):
    match event.tag:
        case None | "" | "!": return None
        case t: return t.lstrip("!")
