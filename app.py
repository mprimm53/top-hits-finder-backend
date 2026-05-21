from flask import Flask, jsonify
from flask_cors import CORS
import billboard

app = Flask(__name__)
CORS(app)

@app.route('/api/charts/<int:year>/<int:month>', methods=['GET'])
def get_charts(year, month):
    try:
        # Format date for Billboard
        date = f"{year}-{month:02d}-01"
        chart = billboard.ChartData('hot-100', date=date)
        
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
        from datetime import date, timedelta
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

@app.route('/', methods=['GET'])
def home():
    return jsonify({'status': 'Top Hits Finder API is running!'})

if __name__ == '__main__':
    app.run(debug=True)
