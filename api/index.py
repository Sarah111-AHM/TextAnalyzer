"""
Smart Text Analyzer — Flask Web App
Entry point for Vercel deployment.
"""

from flask import Flask, request, jsonify, render_template_string
import re
from collections import Counter, defaultdict

app = Flask(__name__)

# ──────────────────────────────────────────────
# DATA STRUCTURES & LOGIC (ported from terminal version)
# ──────────────────────────────────────────────

class TrieNode:
    def __init__(self):
        self.children: dict = {}
        self.is_end: bool = False

class Trie:
    def __init__(self):
        self.root = TrieNode()

    def insert(self, word):
        node = self.root
        for ch in word:
            node = node.children.setdefault(ch, TrieNode())
        node.is_end = True

    def autocomplete(self, prefix, limit=8):
        node = self.root
        for ch in prefix:
            if ch not in node.children:
                return []
            node = node.children[ch]
        results = []
        self._dfs(node, list(prefix), results, limit)
        return results

    def _dfs(self, node, path, results, limit):
        if len(results) >= limit:
            return
        if node.is_end:
            results.append("".join(path))
        for ch, child in node.children.items():
            path.append(ch)
            self._dfs(child, path, results, limit)
            path.pop()

STOP_WORDS = {
    "the","a","an","and","or","but","in","on","at","to","for","of","with",
    "by","from","is","was","are","were","be","been","being","have","has",
    "had","do","does","did","will","would","could","should","may","might",
    "this","that","these","those","i","you","he","she","it","we","they",
    "me","him","her","us","them","my","your","his","its","our","their",
    "what","which","who","when","where","how","if","then","than","so","as",
    "up","out","about","into","not","no","very","just","also","more","some",
    "any","all","each","both","few","own","same","s","t","re","ve","ll","d"
}

POSITIVE_WORDS = {
    "good","great","excellent","amazing","wonderful","fantastic","love","happy",
    "joy","best","beautiful","awesome","positive","nice","superb","perfect",
    "brilliant","outstanding","magnificent","splendid","delightful","glad",
    "pleased","enjoy","fun","pleasant","remarkable","impressive","terrific",
    "blessed","cheerful","grateful","excited","helpful","kind","strong","smart",
}

NEGATIVE_WORDS = {
    "bad","terrible","awful","horrible","hate","sad","worst","ugly","negative",
    "poor","dreadful","disgusting","unpleasant","boring","failure","wrong",
    "broken","useless","pathetic","stupid","weak","angry","frustrated","miserable",
    "painful","frightening","disaster","problem","difficult","annoying","sorry",
    "unfortunate","depressing","disappointing","horrific","cruel","harsh",
}

def preprocess(raw_text):
    raw_sentences = re.split(r'(?<=[.!?])\s+', raw_text.strip())
    raw_sentences = [s.strip() for s in raw_sentences if s.strip()]
    sentences = []
    for sent in raw_sentences:
        cleaned = re.sub(r"[^\w\s']", " ", sent.lower())
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        w = cleaned.split()
        if w:
            sentences.append(w)
    words = [w for s in sentences for w in s]
    word_freq = dict(Counter(words))
    trie = Trie()
    for w in word_freq:
        trie.insert(w)
    bigrams = defaultdict(lambda: defaultdict(int))
    for i in range(len(words) - 1):
        bigrams[words[i]][words[i+1]] += 1
    return {
        "words": words,
        "sentences": sentences,
        "raw_sentences": raw_sentences,
        "word_freq": word_freq,
        "trie": trie,
        "bigrams": {k: dict(v) for k, v in bigrams.items()}
    }

# ──────────────────────────────────────────────
# API ROUTES
# ──────────────────────────────────────────────

@app.route("/api/word-stats", methods=["POST"])
def word_stats():
    data = request.json
    state = preprocess(data["text"])
    top_n = int(data.get("topN", 10))
    top = sorted(state["word_freq"].items(), key=lambda x: x[1], reverse=True)[:top_n]
    return jsonify({
        "total": len(state["words"]),
        "unique": len(state["word_freq"]),
        "top": top
    })

@app.route("/api/char-stats", methods=["POST"])
def char_stats():
    data = request.json
    state = preprocess(data["text"])
    flat = "".join(state["words"])
    char_freq = Counter(flat)
    return jsonify({
        "total": len(flat),
        "top": char_freq.most_common(20)
    })

@app.route("/api/search", methods=["POST"])
def search():
    data = request.json
    state = preprocess(data["text"])
    query = data["query"].lower().strip()
    q_tokens = query.split()
    results = []
    for si, sent in enumerate(state["sentences"]):
        for wi in range(len(sent) - len(q_tokens) + 1):
            if sent[wi: wi + len(q_tokens)] == q_tokens:
                ctx = " ".join(sent[max(0,wi-3): min(len(sent), wi+len(q_tokens)+3)])
                results.append({"sentence": si+1, "wordIndex": wi+1, "context": ctx})
    return jsonify({"count": len(results), "results": results})

@app.route("/api/replace", methods=["POST"])
def replace():
    data = request.json
    state = preprocess(data["text"])
    old = data["old"].lower()
    new = data["new"].lower()
    count = state["words"].count(old)
    new_text = re.sub(r'\b' + re.escape(old) + r'\b', new, data["text"], flags=re.IGNORECASE)
    return jsonify({"count": count, "newText": new_text})

@app.route("/api/autocomplete", methods=["POST"])
def autocomplete():
    data = request.json
    state = preprocess(data["text"])
    prefix = data["prefix"].lower().strip()
    suggestions = state["trie"].autocomplete(prefix, 10)
    suggestions.sort(key=lambda w: state["word_freq"].get(w, 0), reverse=True)
    result = [{"word": w, "freq": state["word_freq"].get(w, 0)} for w in suggestions]
    return jsonify({"suggestions": result})

@app.route("/api/predict", methods=["POST"])
def predict():
    data = request.json
    state = preprocess(data["text"])
    word = data["word"].lower().strip()
    following = state["bigrams"].get(word, {})
    if not following:
        return jsonify({"predictions": []})
    total = sum(following.values())
    top = sorted(following.items(), key=lambda x: x[1], reverse=True)[:8]
    predictions = [{"word": w, "count": c, "prob": round(c/total*100, 1)} for w, c in top]
    return jsonify({"predictions": predictions})

@app.route("/api/sentiment", methods=["POST"])
def sentiment():
    data = request.json
    sentence = data["sentence"]
    excl_count = sentence.count("!")
    tokens = re.sub(r"[^\w\s]", " ", sentence.lower()).split()
    NEGATORS = {"not","never","no","neither","nor","hardly","barely"}
    pos, neg, negation = 0, 0, False
    for token in tokens:
        if token in NEGATORS:
            negation = True
            continue
        if token in POSITIVE_WORDS:
            neg += 1 if negation else 0
            pos += 0 if negation else 1
        elif token in NEGATIVE_WORDS:
            pos += 1 if negation else 0
            neg += 0 if negation else 1
        negation = False
    if excl_count > 0:
        if pos >= neg: pos += excl_count
        else: neg += excl_count
    label = "POSITIVE" if pos > neg else "NEGATIVE" if neg > pos else "NEUTRAL"
    return jsonify({"pos": pos, "neg": neg, "label": label})

@app.route("/api/keywords", methods=["POST"])
def keywords():
    data = request.json
    state = preprocess(data["text"])
    top_n = int(data.get("topN", 10))
    freq = {}
    for w in state["words"]:
        if w not in STOP_WORDS and len(w) > 1:
            freq[w] = freq.get(w, 0) + 1
    top = sorted(freq.items(), key=lambda x: x[1], reverse=True)[:top_n]
    return jsonify({"keywords": top})

# ──────────────────────────────────────────────
# FRONTEND (single-page HTML served by Flask)
# ──────────────────────────────────────────────

HTML = open("static/index.html").read()

@app.route("/")
def index():
    return render_template_string(HTML)

if __name__ == "__main__":
    app.run(debug=True)
