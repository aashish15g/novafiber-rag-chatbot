class EmbeddingService:
    dimension = 1024

    def __init__(self, name, device="cpu", cache_folder=None):
        self.name = name
        self.device = device
        self.cache_folder = str(cache_folder) if cache_folder else None
        self.model = None

    def load(self):
        from sentence_transformers import SentenceTransformer

        self.model = SentenceTransformer(
            self.name, device=self.device, cache_folder=self.cache_folder)

    @property
    def tokenizer(self):
        return self.model.tokenizer

    def encode(self, texts, query=False):
        """Embed passages or questions as normalized vectors."""
        options = {"prompt_name": "query"} if query else {}
        return self.model.encode(
            texts, batch_size=8, normalize_embeddings=True, **options).tolist()
