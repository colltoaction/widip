

# The Composer Functor (SerializationTree -> NodeGraph)
@symmetric.Diagram.from_callable(Node(), Node())
def compose(box: Any) -> symmetric.Diagram:
    """Functorial mapping: Serialization Tree -> Semantic Node Graph."""
    
    if isinstance(box, Sequence):
        return SemanticSequence(compose(box.inside), tag=box.tag)
        
    if isinstance(box, Mapping):
        return SemanticMapping(compose(box.inside), tag=box.tag)
        
    if isinstance(box, Document):
        return SemanticDocument(compose(box.inside))
        
    if isinstance(box, Stream):
        return SemanticStream(compose(box.inside))
        
    if isinstance(box, Anchor):
        return SemanticAnchor(box.name, compose(box.inside))

    if isinstance(box, Scalar):
        return SemanticScalar(box.tag, box.value)
        
    if isinstance(box, Alias):
        return SemanticAlias(box.name)
        
    return box

# Export 'compose' as the Composer functor
Composer = compose
