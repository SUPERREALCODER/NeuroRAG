# Dummy example — replace with real embedding + Qdrant
def run_rag_pipeline(query: str, tenant_id: int, db=None):
    # In reality: filter documents by tenant_id, search Qdrant, generate answer with LLM
    return {"answer_text": f"Simulated answer for tenant {tenant_id} on query: {query}", "documents": []}
