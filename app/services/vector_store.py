from qdrant_client import QdrantClient, models


class VectorStore:
    def __init__(self, path, collection, dimension):
        self.collection = collection
        self.client = QdrantClient(path=str(path))
        if not self.client.collection_exists(collection):
            self.client.create_collection(collection, vectors_config=models.VectorParams(
                size=dimension, distance=models.Distance.COSINE))

    @staticmethod
    def document_filter(document_id):
        return models.Filter(must=[models.FieldCondition(
            key="document_id", match=models.MatchValue(value=document_id))])

    def add(self, points):
        self.client.upsert(self.collection, points=points, wait=True)

    def delete(self, document_id):
        self.client.delete(self.collection, points_selector=models.FilterSelector(
            filter=self.document_filter(document_id)), wait=True)

    def chunk(self, chunk_id):
        points = self.client.retrieve(self.collection, ids=[chunk_id], with_payload=True)
        return points[0] if points else None

    def search(self, vector, limit, document_ids):
        return self.client.query_points(
            self.collection, query=vector, limit=limit, with_payload=True,
            query_filter=models.Filter(must=[
                models.FieldCondition(key="document_id", match=models.MatchAny(any=list(document_ids))),
                models.FieldCondition(key="status", match=models.MatchValue(value="ready"))
            ])).points

    def close(self):
        self.client.close()
