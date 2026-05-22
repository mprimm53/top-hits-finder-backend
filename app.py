from flask import Flask, jsonify, request
from flask_cors import CORS
import billboard
from datetime import date, timedelta
from urllib.parse import quote_plus

app = Flask(__name__)
CORS(app)

@app.route('/', methods=['GET'])
def home():
    return jsonify({'status': 'Top Hits Finder API is running!'})

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy'})

@app.route('/api/charts/<int:year>/<int:month>', methods=['GET'])
def get_charts(year, month):
    try:
        date_str = f"{year}-{month:02d}-01"
        chart = billboard.ChartData('hot-100', date=date_str)
        songs = []
        for entry in chart:
            songs.append({
                'rank': entry.rank,
                'title': entry.title,
                'artist': entry.artist,
            })
        return jsonify({'chart': songs})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/charts/<int:year>/<int:month>/weeks', methods=['GET'])
def get_chart_weeks(year, month):
    try:
        weeks = []
        d = date(year, month, 1)
        while d.month == month:
            weeks.append({
                'label': d.strftime('%b %d, %Y'),
                'value': d.strftime('%Y-%m-%d')
            })
            d += timedelta(days=7)
        return jsonify({'weeks': weeks})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/charts/<int:year>/<int:month>/<int:week>', methods=['GET'])
def get_chart_by_week(year, month, week):
    try:
        date_str = f"{year}-{month:02d}-{week:02d}"
        chart = billboard.ChartData('hot-100', date=date_str)
        songs = []
        for entry in chart:
            songs.append({
                'rank': entry.rank,
                'title': entry.title,
                'artist': entry.artist,
            })
        return jsonify({'chart': songs})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/weeks/<int:year>/<int:month>', methods=['GET'])
def get_weeks(year, month):
    try:
        weeks = []
        d = date(year, month, 1)
        while d.month == month:
            weeks.append({
                'label': d.strftime('%b %d, %Y'),
                'value': d.strftime('%Y-%m-%d')
            })
            d += timedelta(days=7)
        return jsonify({'weeks': weeks})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/search/youtube', methods=['GET'])
def search_youtube():
    try:
        title = request.args.get('title', '').strip()
        artist = request.args.get('artist', '').strip()
        search_query = ' '.join(filter(None, [title, artist, 'official']))
        encoded_query = quote_plus(search_query)
        return jsonify({
            'url': f"https://www.youtube.com/results?search_query={encoded_query}"
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/search/spotify', methods=['GET'])
def search_spotify():
    try:
        title = request.args.get('title', '').strip()
        artist = request.args.get('artist', '').strip()
        search_query = ' '.join(filter(None, [title, artist]))
        encoded_query = quote_plus(search_query)
        return jsonify({
            'url': f"https://open.spotify.com/search/{encoded_query}"
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
