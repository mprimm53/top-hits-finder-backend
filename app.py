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

# Decade-tagged trivia. Each fact carries the fields the app expects
# (id, decade, category, fact) and is filterable via ?decade=.
TRIVIA_FACTS = [
    {"id": 1, "decade": "1950s", "category": "Chart Records", "fact": "The Billboard Hot 100 debuted on August 4, 1958. Its first #1 was 'Poor Little Fool' by Ricky Nelson."},
    {"id": 2, "decade": "1950s", "category": "Genre Origins", "fact": "Rock 'n' roll broke into the mainstream in the late 1950s and reshaped popular music."},
    {"id": 3, "decade": "1950s", "category": "Artist Milestones", "fact": "Elvis Presley became the defining star of the late-'50s charts."},
    {"id": 4, "decade": "1950s", "category": "Cultural Impact", "fact": "TV appearances like Elvis on 'The Ed Sullivan Show' turned singers into national phenomena."},
    {"id": 5, "decade": "1960s", "category": "Artist Milestones", "fact": "The Beatles arrived in America in 1964 and went on to score a record 20 Hot 100 #1 hits."},
    {"id": 6, "decade": "1960s", "category": "Cultural Impact", "fact": "The 'British Invasion' brought The Beatles, The Rolling Stones and The Who to U.S. charts."},
    {"id": 7, "decade": "1960s", "category": "Chart Records", "fact": "Motown turned Detroit into a hit factory with The Supremes, The Temptations and Stevie Wonder."},
    {"id": 8, "decade": "1960s", "category": "Behind the Music", "fact": "The Beach Boys' 'Good Vibrations' (1966) was a famously elaborate and costly production."},
    {"id": 9, "decade": "1970s", "category": "Genre Origins", "fact": "Disco took over dance floors and the charts in the second half of the 1970s."},
    {"id": 10, "decade": "1970s", "category": "Cultural Impact", "fact": "1977's 'Saturday Night Fever' soundtrack sent disco into the mainstream."},
    {"id": 11, "decade": "1970s", "category": "Behind the Music", "fact": "Fleetwood Mac's 'Rumours' (1977) became one of the best-selling albums ever."},
    {"id": 12, "decade": "1970s", "category": "Artist Milestones", "fact": "Stevie Wonder's run of 1970s albums swept the Grammys multiple years."},
    {"id": 13, "decade": "1980s", "category": "Cultural Impact", "fact": "MTV launched on August 1, 1981, making the music video essential to a hit."},
    {"id": 14, "decade": "1980s", "category": "Artist Milestones", "fact": "Michael Jackson's 'Thriller' (1982) is the best-selling album of all time."},
    {"id": 15, "decade": "1980s", "category": "Chart Records", "fact": "Madonna piled up a remarkable streak of Top 5 hits across the decade."},
    {"id": 16, "decade": "1980s", "category": "Behind the Music", "fact": "Prince wrote, played and produced most of his 1980s work, including 'Purple Rain'."},
]

@app.route('/api/trivia', methods=['GET'])
def get_trivia():
    # Optional ?decade=1950s|1960s|1970s|1980s filter; otherwise all decades.
    decade = request.args.get('decade', '').strip()
    facts = [f for f in TRIVIA_FACTS if not decade or f['decade'] == decade]
    facts = facts[:]
    random.shuffle(facts)
    return jsonify(facts)

@app.route('/api/trivia/random', methods=['GET'])
def get_random_trivia():
    return jsonify(random.choice(TRIVIA_FACTS))

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