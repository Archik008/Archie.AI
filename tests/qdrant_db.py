from qdrant_client import QdrantClient, models
from qdrant_client.http.exceptions import UnexpectedResponse
from sentence_transformers import SentenceTransformer
from configure.pyconfig import QDRANT_HOST

class QdrantTesting:
    def __init__(self):
        self.client = QdrantClient(QDRANT_HOST)
        self.model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        self.vectors = None

    def drop_collection(self, collection_name):
        if self.client.collection_exists(collection_name):
            self.client.delete_collection(collection_name)

    def create_collection(self, collection_name, texts: list):        
        vectors = self.model.encode(texts)
        self.vectors = vectors

        # Создание новой коллекции
        self.client.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(
                size=vectors.shape[1],
                distance=models.Distance.COSINE
            )
        )
    
    def insert_data(self, collection_name, texts):
        self.client.upsert(
            collection_name=collection_name,
            points=[
                models.PointStruct(
                    id=i,
                    vector=vector.tolist(),
                    payload={"text": texts[i]}
                )
                for i, vector in enumerate(self.vectors)
            ]
        )

    def search_data(self, query: str, collection_name, limit: int = 3):
        query_vector = self.model.encode([query])[0]

        # Поиск похожих точек без фильтров
        try:
            query_result = self.client.query_points(
                collection_name=collection_name,
                query=query_vector.tolist(),
                limit=limit,  # ограничиваем количество результатов
                with_payload=True  # возьмем данные (payload) из точек
            )
        except UnexpectedResponse as e:
            return

        total_points = []

        for points_tuple in query_result:
            for point in points_tuple[1]:
                point_text = point.payload['text']
                print(f"Score: {point.score:.4f}, Text: {point_text}", flush=True)
                if point.score >= 0.9:
                    total_points.append(point_text)
        
        return total_points

if __name__ == '__main__':
    qt = QdrantTesting()
    texts = ["Привет, как дела?", "Что нового?", "Как ты?", "Какие новости?", "Погода сегодня хорошая."]
    qt.create_collection("test_collection", texts)
    qt.insert_data("test_collection", texts)

    # Поиск похожего текста
    qt.search_data("Как твои дела?", "test_collection")