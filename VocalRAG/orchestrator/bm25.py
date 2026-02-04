import math
from typing import List
from collections import Counter


class BM25:
    """Simple BM25 implementation for document ranking"""
    
    def __init__(self, corpus: List[str], k1: float = 1.5, b: float = 0.75):
        self.corpus = corpus
        self.k1 = k1
        self.b = b
        self.corpus_size = len(corpus)
        self.avgdl = sum(len(doc.split()) for doc in corpus) / self.corpus_size if self.corpus_size > 0 else 0
        self.doc_freqs = []
        self.idf = {}
        self.doc_len = []
        
        self._initialize()
    
    def _initialize(self):
        """Calculate document frequencies and IDF values"""
        df = {}
        
        for doc in self.corpus:
            tokens = doc.lower().split()
            self.doc_len.append(len(tokens))
            frequencies = Counter(tokens)
            self.doc_freqs.append(frequencies)
            
            for token in set(tokens):
                df[token] = df.get(token, 0) + 1
        
        # Calculate IDF
        for token, freq in df.items():
            self.idf[token] = math.log((self.corpus_size - freq + 0.5) / (freq + 0.5) + 1)
    
    def get_scores(self, query: List[str]) -> List[float]:
        """Get BM25 scores for each document given a query"""
        scores = []
        
        for idx, doc_freq in enumerate(self.doc_freqs):
            score = 0.0
            doc_len = self.doc_len[idx]
            
            for token in query:
                if token not in doc_freq:
                    continue
                
                freq = doc_freq[token]
                idf = self.idf.get(token, 0)
                
                # BM25 formula
                numerator = freq * (self.k1 + 1)
                denominator = freq + self.k1 * (1 - self.b + self.b * (doc_len / self.avgdl))
                score += idf * (numerator / denominator)
            
            scores.append(score)
        
        return scores
