from flask import Flask, send_from_directory
from flask_cors import CORS
import folium

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    center = [45, -30]
    m = folium.Map(location=center, zoom_start=3)
    
    folium.Marker(
        [33.756342349687586, -84.39351094004493],
        popup='<h1>My Favourite Stadium</h1><img src="stadium.jpeg" width=400px><p>This is the best stadium out in Atl</p>',
        tooltip='ElCruzo Stadium',
        icon=folium.Icon(icon='heart', color='red')
    ).add_to(m)
    
    
    m.save('static/map.html')
    return send_from_directory('static', 'map.html')

if __name__ == '__main__':
    app.run(debug=True, port=5001)