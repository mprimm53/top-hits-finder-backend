from flask import Flask, jsonify, request, redirect
from flask_cors import CORS
import billboard
from datetime import date, timedelta
from urllib.parse import quote_plus
import random

app = Flask(__name__)

# Single source of truth for CORS. 
# This handles preflight (OPTIONS) requests automatically.
CORS(app, resources={r"/api/*": {"origins": "*"}})

# --- REMOVED THE AFTER_REQUEST BLOCK TO PREVENT CONFLICTS ---

@app.route('/', methods=['GET'])
def home():
    return jsonify({'status': 'Top Hits Finder API is running!'})

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy'})

@app.route('/api/charts/search', methods=['GET'])
def search_charts():
    try:
        query = request.args.get('q', '').lower()
        if not query:
            return jsonify({'results':[]})
        
        # Search just one year/month for speed
        year = random.randint(1958, 1990)
        results =[]
        try:
            date_str = f"{year}-01-01"
            chart = billboard.ChartData('hot-100', date=date_str)
            for entry in chart:
                if (query in entry.title.lower() or
                        query in entry.artist.lower()):
                    results.append({
                        'rank': entry.rank,
                        'title': entry.title,
                        'artist': entry.artist,
                        'year': year,
                        'month': 1,
                        'chartDate': date_str
                    })
        except:
            pass
        
        return jsonify({'results': results[:20]})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/trivia', methods=['GET'])
@app.route('/api/trivia/random', methods=['GET'])
def get_trivia():
    try:
        trivia_facts =[
            {"fact": "The Billboard Hot 100 was first published on August 4, 1958.", "category": "History"},
            {"fact": "Elvis Presley had 18 number-one hits on the Billboard Hot 100.", "category": "Artist"},
            {"fact": "The Beatles hold the record for most number-one hits with 20.", "category": "Record"},
            {"fact": "Michael Jackson's 'Thriller' is the best-selling album of all time.", "category": "Artist"},
            {"fact": "The first number-one song on the Hot 100 was 'Poor Little Fool' by Ricky Nelson.", "category": "History"},
            {"fact": "Mariah Carey has had 19 number-one singles on the Billboard Hot 100.", "category": "Artist"},
            {"fact": "Whitney Houston's 'I Will Always Love You' spent 14 weeks at number one in 1992.", "category": "Record"},
            {"fact": "MTV launched on August 1, 1981, revolutionizing the music industry.", "category": "History"},
            {"fact": "The Beach Boys' 'Good Vibrations' cost $50,000 to record in 1966.", "category": "History"},
            {"fact": "The Rolling Stones have charted more than 100 songs on the Hot 100.", "category": "Artist"},
        ]
        fact = random.choice(trivia_facts)
        return jsonify([fact])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/trivia/decade-<string:decade>', methods=['GET'])
def get_decade_trivia(decade):
    try:
        decade_facts = {
            '1950s': [{"fact": "Rock 'n' Roll was born in the late 1950s.", "category": "History"}],
            '1960s': [{"fact": "The Beatles arrived in America in 1964.", "category": "History"}],
            '1970s': [{"fact": "Disco dominated the charts in the late 1970s.", "category": "History"}],
            '1980s': [{"fact": "MTV launched on August 1, 1981.", "category": "History"}],
        }
        facts = decade_facts.get(decade, [{"fact": f"The {decade} was a great decade for music!", "category": "History"}])
        return jsonify(random.choice(facts))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/search/youtube', methods=['GET'])
def search_youtube():
    title = request.args.get('title', '')
    artist = request.args.get('artist', '')
    search_query = quote_plus(f"{title} {artist} official")
    url = f"https://www.youtube.com/results?search_query={search_query}"
    return redirect(url, code=302)

@app.route('/api/search/spotify', methods=['GET'])
def search_spotify():
    title = request.args.get('title', '')
    artist = request.args.get('artist', '')
    search_query = quote_plus(f"{title} {artist}")
    url = f"https://open.spotify.com/search/{search_query}"
    return redirect(url, code=302)

if __name__ == '__main__':
    app.run(debug=True)