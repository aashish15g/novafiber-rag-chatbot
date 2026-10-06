from qdrant_client import QdrantClient, models


class VectorStore:
    def __init__(self, path, collection: str, dimension: int):
        self.collection = collection
        self.client = QdrantClient(path=str(path))
        if not self.client.collection_exists(collection):
            self.client.create_collection(collection, vectors_config=models.VectorParams(
                size=dimension, distance=models.Distance.COSINE))
        config = self.client.get_collection(collection).config.params.vectors
        if not isinstance(config, models.VectorParams) or config.size != dimension or config.distance != models.Distance.COSINE:
            self.client.close()
            raise ValueError("Existing collection does not match the embedding configuration. Use a new collection.")

    @staticmethod
    def document_filter(document_id):
        return models.Filter(must=[models.FieldCondition(key="document_id", match=models.MatchValue(value=document_id))])

    def add(self, points):
        for start in range(0, len(points), 64):
            self.client.upsert(self.collection, points=points[start:start + 64], wait=True)

    def publish(self, document_id):
        self.client.set_payload(self.collection, payload={"status": "ready"},
                                points=self.document_filter(document_id), wait=True)

    def delete(self, document_id):
        self.client.delete(self.collection, points_selector=models.FilterSelector(
            filter=self.document_filter(document_id)), wait=True)

    def search(self, vector, limit):
        return self.client.query_points(self.collection, query=vector, limit=limit, with_payload=True,
            query_filter=models.Filter(must=[models.FieldCondition(key="status", match=models.MatchValue(value="ready"))])).points

    def close(self):
        self.client.close()
