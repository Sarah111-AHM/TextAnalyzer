from flask import Flask, request, jsonify
from flask_cors import CORS
import string
import re
from collections import defaultdict, Counter

app = Flask(__name__)
CORS(app)

class TextHelper:
    def __init__(self):
        self.raw_stuff = ""
        self.word_list = []
        self.sentences = []
        self.undo_stack = []
        self.boring_words = {"the", "is", "and", "in", "of", "to", "a", "an", "on", "for", "with", "that", "this", "it"}
        
        # N-Grams
        self.pair_counts = defaultdict(lambda: defaultdict(int))
        self.trio_counts = defaultdict(lambda: defaultdict(int))

    def process(self, text):
        self.raw_stuff = text
        self.sentences = [s.strip() for s in re.split(r'[.!?]', text) if s.strip()]
        
        # تنظيف النص للكلمات
        clean = text.lower().translate(str.maketrans('', '', string.punctuation))
        self.word_list = clean.split()
        self._build_ngrams()

    def _build_ngrams(self):
        self.pair_counts.clear()
        self.trio_counts.clear()
        for i in range(len(self.word_list) - 1):
            self.pair_counts[self.word_list[i]][self.word_list[i+1]] += 1
        for i in range(len(self.word_list) - 2):
            key = f"{self.word_list[i]} {self.word_list[i+1]}"
            self.trio_counts[key][self.word_list[i+2]] += 1

    # ميزة التدقيق الإملائي (Levenshtein Distance)
    def get_spelling_suggestions(self, word):
        word = word.lower()
        unique_words = set(self.word_list)
        
        def edit_distance(s1, s2):
            if len(s1) < len(s2): return edit_distance(s2, s1)
            if not s2: return len(s1)
            previous_row = range(len(s2) + 1)
            for i, c1 in enumerate(s1):
                current_row = [i + 1]
                for j, c2 in enumerate(s2):
                    current_row.append(min(previous_row[j+1]+1, current_row[j]+1, previous_row[j]+(c1!=c2)))
                previous_row = current_row
            return previous_row[-1]

        # اقتراح الكلمات التي مسافتها 1 أو 2 فقط
        suggestions = [w for w in unique_words if edit_distance(word, w) <= 2]
        return sorted(suggestions, key=lambda x: self.word_list.count(x), reverse=True)[:5]

helper = TextHelper()

@app.route('/analyze', methods=['POST'])
def analyze():
    text = request.json.get("text", "")
    helper.process(text)
    
    # إحصائيات الحروف
    char_counts = Counter(c for c in text if c not in string.whitespace)
    # استخراج الكلمات المفتاحية (Keywords)
    keywords = [w for w, c in Counter(helper.word_list).most_common(20) if w not in helper.boring_words][:5]
    # بيانات Word Cloud
    word_freq = dict(Counter(helper.word_list).most_common(50))

    return jsonify({
        "stats": {
            "total_words": len(helper.word_list),
            "total_chars": sum(char_counts.values()),
            "unique_words": len(set(helper.word_list)),
            "char_freq": dict(char_counts.most_common(10))
        },
        "keywords": keywords,
        "word_cloud": word_freq
    })

@app.route('/search', methods=['GET'])
def search_phrase():
    phrase = request.args.get("q", "").lower()
    results = []
    for i, sent in enumerate(helper.sentences):
        if phrase in sent.lower():
            results.append({"line": i+1, "text": sent.strip()})
    return jsonify({"matches": results})

@app.route('/swap', methods=['POST'])
def swap():
    data = request.json
    old_w, new_w = data.get("old"), data.get("new")
    helper.undo_stack.append(helper.raw_stuff) # حفظ للـ Undo
    helper.raw_stuff = re.sub(rf'\b{old_w}\b', new_w, helper.raw_stuff, flags=re.IGNORECASE)
    helper.process(helper.raw_stuff)
    return jsonify({"new_text": helper.raw_stuff})

@app.route('/undo', methods=['POST'])
def undo():
    if not helper.undo_stack:
        return jsonify({"error": "Nothing to undo"}), 400
    helper.raw_stuff = helper.undo_stack.pop()
    helper.process(helper.raw_stuff)
    return jsonify({"text": helper.raw_stuff})

@app.route('/spell', methods=['GET'])
def spell_check():
    word = request.args.get("w", "")
    return jsonify({"suggestions": helper.get_spelling_suggestions(word)})

@app.route('/predict-trigram', methods=['GET'])
def predict_trigram():
    q = request.args.get("q", "").lower()
    return jsonify({"options": dict(helper.trio_counts.get(q, {}))})

app = app
