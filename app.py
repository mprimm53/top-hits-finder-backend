from flask import Flask, jsonify, request, redirect
from flask_cors import CORS
from datetime import date, datetime
from urllib.parse import quote_plus
from bisect import bisect_left
import gzip, json, os, random

app = Flask(__name__)

# Single source of truth for CORS.
# This handles preflight (OPTIONS) requests automatically.
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Bundled Billboard Hot 100 dataset (1958-1990). Loaded once at startup, so every
# chart lookup is instant and reliable — no live scraping of billboard.com (which
# was slow/unreliable and caused the gateway timeouts).
_DATA_PATH = os.path.join(os.path.dirname(__file__), 'data', 'hot100_1958_1990.json.gz')
with gzip.open(_DATA_PATH, 'rt', encoding='utf-8') as _f:
    _DATA = json.load(_f)
_WEEKS = _DATA['weeks']      # sorted list of 'YYYY-MM-DD' chart dates
_CHARTS = _DATA['charts']    # { 'YYYY-MM-DD': [{rank, title, artist}, ...] }

def _nearest_week(date_str):
    """Closest chart-week date in the dataset to the requested date."""
    target = datetime.strptime(date_str, '%Y-%m-%d').date()
    i = bisect_left(_WEEKS, date_str)
    candidates = [_WEEKS[j] for j in (i - 1, i) if 0 <= j < len(_WEEKS)]
    return min(candidates, key=lambda w: abs((datetime.strptime(w, '%Y-%m-%d').date() - target).days))

def fetch_hot100(date_str):
    """Return (chart_week_date, entries) for the chart week nearest date_str."""
    wk = _nearest_week(date_str)
    return wk, _CHARTS[wk]

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
    # "This week in music history" — today's date in a random in-range year.
    today = date.today()
    year = random.randint(1958, 1990)
    date_str = f"{year}-{today.month:02d}-{min(today.day, 28):02d}"
    try:
        chart_week, results = fetch_hot100(date_str)
        # Frontend expects { year, chartDate, song: {title, artist, rank} }.
        return jsonify({
            "year": int(chart_week[:4]),
            "chartDate": chart_week,
            "song": results[0] if results else None,
        })
    except Exception:
        return jsonify(None)

@app.route('/api/charts/<year>/<month>/<week>', methods=['GET'])
def get_chart_by_date(year, month, week):
    try:
        # The app sends the week selection (1-4); map it to a day of the month.
        week_to_day = {1: 1, 2: 8, 3: 15, 4: 22}
        day = week_to_day.get(int(week), 1)
        date_str = f"{year}-{int(month):02d}-{day:02d}"
        chart_week, results = fetch_hot100(date_str)
        # Frontend expects { year, month, week, chartDate, chart: [...] }.
        return jsonify({
            "year": int(year),
            "month": int(month),
            "week": int(week),
            "chartDate": chart_week,
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

        # Scan the full 1958-1990 dataset; return the first 20 unique matches.
        results = []
        seen = set()
        for wk in _WEEKS:
            for entry in _CHARTS[wk]:
                if query in entry['title'].lower() or query in entry['artist'].lower():
                    key = (entry['title'], entry['artist'])
                    if key in seen:
                        continue
                    seen.add(key)
                    results.append({
                        'rank': entry['rank'],
                        'title': entry['title'],
                        'artist': entry['artist'],
                        'year': int(wk[:4]),
                        'month': int(wk[5:7]),
                        'chartDate': wk,
                    })
                    if len(results) >= 20:
                        return jsonify({'results': results})

        return jsonify({'results': results})
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