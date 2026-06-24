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

# Simple in-memory cache. A Billboard chart for a given date never changes,
# so we scrape billboard.com only once per date and reuse the result.
# This turns repeat requests from ~30s into instant responses.
_chart_cache = {}

def fetch_hot100(date_str):
    """Return Hot 100 entries for date_str, scraping billboard.com at most once per date."""
    if date_str not in _chart_cache:
        chart = billboard.ChartData('hot-100', date=date_str)
        _chart_cache[date_str] = [
            {'title': entry.title, 'artist': entry.artist, 'rank': entry.rank}
            for entry in chart
        ]
    return _chart_cache[date_str]

@app.route('/', methods=['GET'])
def home():

    return jsonify({'status': 'Top Hits Finder API is running!'})

# --- ADD YOUR NEW ROUTES HERE ---

@app.route('/api/charts/<year>/<month>/weeks', methods=['GET'])
def get_weeks(year, month):
    # The frontend expects { year, month, weeks: [{week, date, label}] }.
    # `week` (1-4) is the selection value the app sends back to the chart route.
    m = int(month)
    days = [1, 8, 15, 22]
    weeks = [
        {"week": i + 1, "date": f"{year}-{m:02d}-{d:02d}", "label": f"Week {i + 1} ({m}/{d:02d}/{year})"}
        for i, d in enumerate(days)
    ]
    return jsonify({"year": int(year), "month": m, "weeks": weeks})

@app.route('/api/charts/on-this-day', methods=['GET'])
def get_on_this_day():
    # Fetch for today's date in a random year from the 80s as a fallback, 
    # or just use today's actual date
    today = date.today()
    date_str = f"{today.year}-{today.month:02d}-{today.day:02d}"
    try:
        results = fetch_hot100(date_str)
        # Frontend expects { year, chartDate, song: {title, artist, rank} }.
        return jsonify({
            "year": today.year,
            "chartDate": date_str,
            "song": results[0] if results else None,
        })
    except:
        return jsonify(None)

@app.route('/api/charts/<year>/<month>/<week>', methods=['GET'])
def get_chart_by_date(year, month, week):
    try:
        # The app sends the week selection (1-4); map it to a day of the month.
        week_to_day = {1: 1, 2: 8, 3: 15, 4: 22}
        day = week_to_day.get(int(week), 1)
        date_str = f"{year}-{int(month):02d}-{day:02d}"
        results = fetch_hot100(date_str)
        # Frontend expects { year, month, week, chartDate, chart: [...] }.
        return jsonify({
            "year": int(year),
            "month": int(month),
            "week": int(week),
            "chartDate": date_str,
            "chart": results,
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
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
            for entry in fetch_hot100(date_str):
                if (query in entry['title'].lower() or
                        query in entry['artist'].lower()):
                    results.append({
                        'rank': entry['rank'],
                        'title': entry['title'],
                        'artist': entry['artist'],
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