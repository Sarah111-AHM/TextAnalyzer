# TextAnalyzer 

Hello Guys, We built this **Smart Text Analyzer**  basically a tool that lets you throw in any text (like an essay, article, or just random words) and it gives you all kinds of cool insights. It’s got both a terminal version and a web version (yup, even deployed it on Vercel ✨).

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Vercel-blue?style=for-the-badge&logo=vercel)](https://text-analyzer-fb68.vercel.app/)

---

### What it does:

- Gives you the **word count**, **unique words**, and **top keywords**.
- Lets you **search** for a word and tells you exactly where it appears (sentence + position).
- You can **replace** words and even **undo** if you change your mind.
- Has smart features like **autocomplete** (kinda like Google search), **next word prediction** (bigram + trigram), **spell check** (with edit distance), and **sentiment analysis** (detects if the vibe is happy, sad, or neutral).
- Also pulls out **keywords** by ignoring boring words (stopwords) and can even generate **word cloud data**.

### Why it’s cool:

Everything’s built from scratch — **Trie** for autocomplete, **n-gram models** for prediction, **edit distance** for spell check, and a **stack** for undo.

No cheating with fancy libraries, just pure Python and data structures.

Deployed on **Vercel** so you can actually play with it online. Pretty much a full-on text playground for nerds 🤓

👉 **[Try it live here!](https://text-analyzer-fb68.vercel.app/)**
