import random
import json
import requests
import pickle
import datetime

#  Client Keys
CLIENT_ID = "3286c890030e4098865771e067e7ae24"
CLIENT_SECRET = "4724330b48ee4412b5d64efbb69c5218"

# Spotify URLS
SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_API_BASE_URL = "https://api.spotify.com"
API_VERSION = "v1"
SPOTIFY_API_URL = "{}/{}".format(SPOTIFY_API_BASE_URL, API_VERSION)

THRESHOLD = 180000  # 3 minutes

# Server-side Parameters
CLIENT_SIDE_URL = "http://127.0.0.1"
PORT = 5000
REDIRECT_URI = "{}:{}/callback/q".format(CLIENT_SIDE_URL, PORT)
SCOPE = "playlist-modify-public playlist-modify-private user-top-read user-read-playback-position"

MOOD = ['Energetic', 'Depressed', 'Sad', 'Calm', 'Happy', 'Contentment', 'Frantic', 'Exuberant']
MUSIC_MOOD = ["Happy", 'Energetic', 'Calm', 'Sad']

# Load the data - No need to do Feature Engineering again
with open('MOODAI.pickle', 'rb') as fe_data_file:
    feature_engineered_data = pickle.load(fe_data_file)


def add_to_playlist(playlist_id, uris, access_token):
    request_body = json.dumps({
        "uris": uris
    })

    authorization_header = {"Accept": "application/json", "Content-Type": "application/json",
                            "Authorization": "Bearer {}".format(access_token)}

    new_track_endpoint = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"

    response = requests.post(new_track_endpoint, data=request_body, headers=authorization_header)
    return response.status_code


def music_algorithm(playlist_data, duration, moods, access_token):  # fazer verificação da era;
    playlist = []
    vec = []
    genres = []

    for i in range(len(moods)):
        if moods[i] == 'Depressed':
            moods[i] = 'Sad'
        elif moods[i] == 'Contentment':
            moods[i] = 'Calm'
        elif moods[i] == 'Frantic':
            moods[i] = 'Sad'
        elif moods[i] == 'Exuberant':
            moods[i] = 'Happy'

    authorization_header = {"Accept": "application/json", "Content-Type": "application/json",
                            "Authorization": "Bearer {}".format(access_token)}

    # get favourites
    artists_api_endpoint = "https://api.spotify.com/v1/me/top/artists"
    artists_response = requests.get(artists_api_endpoint, headers=authorization_header)
    if 400 <= artists_response.status_code < 600:  # se não for aceite
        return artists_response.status_code
    artists = artists_response.json()['items']

    tracks_api_endpoint = "https://api.spotify.com/v1/me/top/tracks"
    tracks_response = requests.get(tracks_api_endpoint, headers=authorization_header)
    if 400 <= tracks_response.status_code < 600:  # se não for aceite
        return tracks_response.status_code
    tracks_data = tracks_response.json()['items']

    for artist in artists:
        for genre in artist['genres']:
            if genre not in genres:
                genres.append(genre)

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
    if 400 <= seed_response.status_code < 600:  # se não for aceite
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
            # gets track features
            if 400 <= features_response.status_code < 600:  # se não for aceite
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


def podcast_algorithm(playlist_data, duration, moods, access_token):
    podcasts = []
    vec = []
    authorization_header = {"Accept": "application/json", "Content-Type": "application/json",
                            "Authorization": "Bearer {}".format(access_token)}

    random.seed(datetime.datetime.now())

    with open('podcasts.json') as json_file:
        data = json.load(json_file)

    # avaliar mood <- talvez ver um só?
    for mood in moods:
        for podcast in data[mood]:
            notExists = True
            # ver se na lista não existe
            for inList in podcasts:
                if inList[1] == podcast:
                    notExists = False
                    inList[0] += 1
            if notExists:
                podcasts.append([1, podcast])

    # ordenar por [0]
    podcasts = sorted(podcasts, key=lambda pod: pod[0], reverse=True)

    i = 0
    while int(duration) > int(THRESHOLD) and i < len(podcasts):
        podcast_api = f"https://api.spotify.com/v1/shows/{podcasts[i][1]}/episodes?limit=20"
        podcast = requests.get(podcast_api, headers=authorization_header)
        if 400 <= podcast.status_code < 600:  # se não for aceite
            return podcast.status_code
        podcast_data = podcast.json()

        limit = int(podcast_data['limit'])
        index = random.randint(0, limit - 1)

        duration_aux = int(duration) - int(podcast_data['items'][index]['duration_ms'])
        if duration_aux >= 0:
            vec.append(podcast_data['items'][index]['uri'])
            duration = duration_aux
        else:
            added = False
            j = 0
            while not added and j < 5:  # tries other if can't add
                j += 1
                index = random.randint(0, limit - 1)
                duration_aux = int(duration) - int(podcast_data['items'][index]['duration_ms'])
                if duration_aux >= 0:
                    vec.append(podcast_data['items'][index]['uri'])
                    duration = duration_aux
                    added = True
        i += 1

    return add_to_playlist(playlist_data['id'], vec)


# type -> 0 podcast; 1 -> playlist
def generate_playlist(playlist_name, duration, mood, type, display_arr, access_token):
    # creates empty playlist
    request_body = json.dumps({
        'name': playlist_name,
        'description': 'Your new playlist created with love by Dr. Music ❤',
        'public': False
    })

    authorization_header = {"Accept": "application/json", "Content-Type": "application/json",
                            "Authorization": "Bearer {}".format(access_token)}

    new_playlist_endpoint = f"https://api.spotify.com/v1/users/{display_arr[0]['id']}/playlists"
    new_playlist = requests.post(new_playlist_endpoint, data=request_body, headers=authorization_header)
    if 400 <= new_playlist.status_code < 600:  # se não for aceite
        return new_playlist.status_code
    new_playlist_data = new_playlist.json()

    if type:  # playlist
        music_algorithm(new_playlist_data, duration, mood)
    else:  # podcast
        podcast_algorithm(new_playlist_data, duration, mood)
    return  # HERE


# autorização
def callback(auth_token):
    # Auth Step 4: Requests refresh and access tokens
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
    display_arr = [profile_data] + playlist_data["items"]
    return {'auth_token': auth_token, 'access_token': access_token, 'display_arr': display_arr}


if __name__ == '__main__':
    app.run(debug=True)
