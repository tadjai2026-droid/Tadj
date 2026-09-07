import os
_model=None
MODEL=os.getenv("EMBEDDING_MODEL","intfloat/multilingual-e5-small")

def embed(text):
    global _model
    try:
        from fastembed import TextEmbedding
        if _model is None:_model=TextEmbedding(model_name=MODEL)
        vec=next(_model.embed([text]))
        return [float(x) for x in vec]
    except Exception:
        return None
