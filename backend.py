import random

from flask import Flask, render_template, request, redirect, session
import json
import requests
from urllib.parse import quote
import pickle

app = Flask(__name__)
app.debug = True
counter = 2
app.secret_key = 'secret_key'

#  Client Keys
CLIENT_ID = "3286c890030e4098865771e067e7ae24"
CLIENT_SECRET = "4724330b48ee4412b5d64efbb69c5218"

# Spotify URLS
SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_API_BASE_URL = "https://api.spotify.com"
API_VERSION = "v1"
SPOTIFY_API_URL = "{}/{}".format(SPOTIFY_API_BASE_URL, API_VERSION)

# Server-side Parameters
CLIENT_SIDE_URL = "http://127.0.0.1"
PORT = 5000
REDIRECT_URI = "{}:{}/callback/q".format(CLIENT_SIDE_URL, PORT)
SCOPE = "playlist-modify-public playlist-modify-private user-top-read"
STATE = ""
SHOW_DIALOG_bool = True
SHOW_DIALOG_str = str(SHOW_DIALOG_bool).lower()

auth_query_parameters = {
    "response_type": "code",
    "redirect_uri": REDIRECT_URI,
    "scope": SCOPE,
    # "state": STATE,
    # "show_dialog": SHOW_DIALOG_str,
    "client_id": CLIENT_ID
}

MOOD = ['Energetic', 'Depressed', 'Sad', 'Calm', 'Happy', 'Contentment', 'Frantic', 'Exuberant']

allPosts = [{'title': 'Post 1', 'content': 'First Post', 'author': 'Me', 'id': 0},
            {'title': 'Post 2', 'content': 'Second Post', 'id': 1}]

# Load the data - No need to do Feature Engineering again
with open('MOODAI.pickle', 'rb') as fe_data_file:
    feature_engineered_data = pickle.load(fe_data_file)


# Continue with your modeling

# done
def add_to_playlist(playlist_id, uris):
    request_body = json.dumps({
        "uris": uris
    })

    authorization_header = {"Accept": "application/json", "Content-Type": "application/json",
                            "Authorization": "Bearer {}".format(session['access_token'])}

    new_track_endpoint = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"

    response = requests.post(new_track_endpoint, data=request_body, headers=authorization_header)
    return response.status_code


def music_algorithm(playlist_data, duration, genres, moods):  # fazer verificação da era;
    playlist = []
    artists = []
    vec = []
    authorization_header = {"Accept": "application/json", "Content-Type": "application/json",
                            "Authorization": "Bearer {}".format(session['access_token'])}

    # get favourites
    artists_api_endpoint = "https://api.spotify.com/v1/me/top/artists"
    artists_response = requests.get(artists_api_endpoint, headers=authorization_header)
    if artists_response.status_code != 200:
        return artists_response.status_code
    artists_data = artists_response.json()['items']

    tracks_api_endpoint = "https://api.spotify.com/v1/me/top/tracks"
    tracks_response = requests.get(tracks_api_endpoint, headers=authorization_header)
    if tracks_response.status_code != 200:
        return artists_response.status_code
    tracks_data = tracks_response.json()['items']

    for artist in artists_data:
        for genre in genres:
            if genre in artist['genres'] and artists not in artists:
                artists.append(artist)
                continue

    for track in tracks_data:
        for artist in artists:
            if artist['name'] == track['album']['artists'][0]['name']:
                playlist.append(track)
                continue

    seed_api_endpoint = "https://api.spotify.com/v1/recommendations?limit=100&market=ES"

    seed_api_endpoint = seed_api_endpoint + '&seed_genres='
    for count, genre in enumerate(genres):
        if count > 0:
            seed_api_endpoint = seed_api_endpoint + '2C'
        seed_api_endpoint = seed_api_endpoint + f'{genre}%'
    seed_api_endpoint = seed_api_endpoint[:-1]  # remove last

    if len(playlist) != 0:
        seed_api_endpoint = seed_api_endpoint + '&seed_tracks='
        for count, track in enumerate(playlist):
            name = track['id']
            if count > 0:
                seed_api_endpoint = seed_api_endpoint + '2C'
            seed_api_endpoint = seed_api_endpoint + f'{name}%'
        seed_api_endpoint = seed_api_endpoint[:-1]  # remove last

    seed_response = requests.get(seed_api_endpoint, headers=authorization_header)
    if seed_response.status_code != 200:
        return seed_response.status_code
    seed_data = seed_response.json()
    for track in seed_data['tracks']:
        if track not in playlist:
            playlist.append(track)

    for track in playlist:
        # IA feature_engineered_data nome, artista, id, danceability, energy,
        # feature_engineered_data.predict()

        duration_aux = int(duration) - int(track['duration_ms'])
        if duration_aux >= 0:
            features_api_endpoint = f"https://api.spotify.com/v1/audio-features/{track['id']}"
            features_response = requests.get(features_api_endpoint, headers=authorization_header)
            if features_response.status_code != 200:
                return features_response.status_code
            features_data = features_response.json()
            index = int(feature_engineered_data.predict(
                [[features_data['danceability'], features_data['loudness'], features_data['speechiness'],
                 features_data['acousticness'], features_data['liveness']]]))

            # test if right mood
            if MOOD[index] in moods:
                vec.append(track['uri'])
                duration = duration_aux

    random.shuffle(vec)

    return add_to_playlist(playlist_data['id'], vec)


def podcast_algorithm(playlist_data, duration, genres):
    return


@app.route('/')
def hello_world():
    return render_template('index.html')


@app.route("/spotify")
def index():
    # Auth Step 1: Authorization
    url_args = "&".join(["{}={}".format(key, quote(val)) for key, val in auth_query_parameters.items()])
    auth_url = "{}/?{}".format(SPOTIFY_AUTH_URL, url_args)
    return redirect(auth_url)


@app.route("/create/<playlist_name>/<duration>")  # o html faz put -> change
def generate_playlist(playlist_name, duration):
    # creates empty playlist
    request_body = json.dumps({
        'name': playlist_name,
        'description': 'Your new playlist created with love by SpotTheTime ❤',
        'public': False
    })

    authorization_header = {"Accept": "application/json", "Content-Type": "application/json",
                            "Authorization": "Bearer {}".format(session['access_token'])}

    new_playlist_endpoint = f"https://api.spotify.com/v1/users/{session['display_arr'][0]['id']}/playlists"
    new_playlist = requests.post(new_playlist_endpoint, data=request_body, headers=authorization_header)
    new_playlist_data = new_playlist.json()

    music_algorithm(new_playlist_data, duration, ['electropop'], ['Sad', 'Depressed']) # DEBUG

    return render_template("indexSpotify.html")


# autorização
@app.route("/callback/q")
def callback():
    # Auth Step 4: Requests refresh and access tokens
    auth_token = request.args['code']
    session['auth_token'] = auth_token
    code_payload = {
        "grant_type": "authorization_code",
        "code": str(auth_token),
        "redirect_uri": REDIRECT_URI,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
    }
    post_request = requests.post(SPOTIFY_TOKEN_URL, data=code_payload)

    # Auth Step 5: Tokens are Returned to Application
    response_data = json.loads(post_request.text)
    access_token = response_data["access_token"]
    refresh_token = response_data["refresh_token"]
    token_type = response_data["token_type"]
    expires_in = response_data["expires_in"]
    session['access_token'] = access_token

    # Auth Step 6: Use the access token to access Spotify API
    authorization_header = {"Authorization": "Bearer {}".format(access_token)}

    # Get profile data
    user_profile_api_endpoint = "{}/me".format(SPOTIFY_API_URL)
    profile_response = requests.get(user_profile_api_endpoint, headers=authorization_header)
    profile_data = json.loads(profile_response.text)

    playlist_api_endpoint = "{}/playlists".format(profile_data["href"])
    playlists_response = requests.get(playlist_api_endpoint, headers=authorization_header)
    playlist_data = json.loads(playlists_response.text)

    # Combine profile and playlist data to display
    session['display_arr'] = [profile_data] + playlist_data["items"]
    return render_template("indexSpotify.html", sorted_array=session['display_arr'])


if __name__ == '__main__':
    app.run(debug=True)
