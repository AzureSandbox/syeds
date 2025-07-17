import sqlite3
from flask import Flask, request, jsonify, render_template_string
import nltk
from nltk.util import ngrams
from difflib import get_close_matches
import os

app = Flask(__name__)
nltk.download('punkt')
DB_NAME = 'library.db'



def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            year INTEGER,
            status INTEGER DEFAULT 1
        )
    ''')
    conn.commit()
    conn.close()

def get_all_titles():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT title FROM books")
    titles = [row[0] for row in c.fetchall()]
    conn.close()
    return titles


def autocomplete_title(partial):
    titles = get_all_titles()
    tokens = nltk.word_tokenize(partial.lower())
    all_ngrams = [' '.join(gram) for title in titles for gram in ngrams(nltk.word_tokenize(title.lower()), len(tokens))]
    close_matches = get_close_matches(partial.lower(), all_ngrams, n=5, cutoff=0.3)
    suggestions = [title for title in titles if any(ng in title.lower() for ng in close_matches)]
    return suggestions

@app.route('/')
def home():
    return render_template_string('''
        <h1>Library Management System</h1>
    ''')

@app.route('/search')
def search_books():
    query = request.args.get('q', '')
    suggestions = autocomplete_title(query)
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM books WHERE title LIKE ? OR author LIKE ?", 
              (f"%{query}%", f"%{query}%"))
    results = c.fetchall()
    conn.close()
    return jsonify({'results': results, 'suggestions': suggestions})

@app.route('/checkout/<int:book_id>', methods=['POST'])
def checkout_book(book_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE books SET status = 0 WHERE id = ?", (book_id,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Book checked out'})

@app.route('/checkin/<int:book_id>', methods=['POST'])
def checkin_book(book_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE books SET status = 1 WHERE id = ?", (book_id,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Book checked in'})

@app.route('/books')
def list_books():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM books")
    books = c.fetchall()
    conn.close()
    return jsonify({'books': books})

if __name__ == '__main__':
    init_db()
    app.run(debug=True)