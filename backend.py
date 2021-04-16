from flask import Flask, render_template, request, redirect, session
import json
import requests
from urllib.parse import quote

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
auth_token = ""

auth_query_parameters = {
    "response_type": "code",
    "redirect_uri": REDIRECT_URI,
    "scope": SCOPE,
    # "state": STATE,
    # "show_dialog": SHOW_DIALOG_str,
    "client_id": CLIENT_ID
}


allPosts = [{'title': 'Post 1', 'content': 'First Post', 'author': 'Me', 'id': 0},
            {'title': 'Post 2', 'content':  'Second Post', 'id':1}]

@app.route('/')
def hello_world():
    return render_template('index.html')


@app.route('/posts', methods=['GET', 'POST'])
def posts():
    global counter
    if request.method == 'POST':
        post_title = request.form['title']
        post_content = request.form['content']
        post_author = request.form['author']
        allPosts.append({'title': post_title, 'content': post_content, 'author': post_author, 'id': counter})
        counter += 1
        return redirect('/posts')
    else:
        return render_template('posts.html', posts=allPosts)


@app.route('/posts/delete/<int:id>')
def delete(id):
    global allPosts
    print(id)
    allPosts.pop(id)
    return redirect('/posts')



@app.route('/posts/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    global allPosts
    post = allPosts[id]
    if request.method == 'POST':
        post['title'] = request.form['title']
        post['content'] = request.form['content']
        post['author'] = request.form['author']
        return redirect('/posts')
    else:
        return render_template('edit.html', post=post)


@app.route("/spotify")
def index():
    # Auth Step 1: Authorization
    url_args = "&".join(["{}={}".format(key, quote(val)) for key, val in auth_query_parameters.items()])
    auth_url = "{}/?{}".format(SPOTIFY_AUTH_URL, url_args)
    return redirect(auth_url)

@app.route("/playlist")
def generate_playlist():

    authorization_header = {"Accept": "application/json", "Content-Type": "application/json",
                            "Authorization": "Bearer {}".format(session['access_token'])}

    # Get profile data
    # user_profile_api_endpoint = "{}/me".format(SPOTIFY_API_URL)
    # profile_response = requests.get(user_profile_api_endpoint, headers=authorization_header)

    artist_api_endpoist = "https://api.spotify.com/v1/me/top/artists"
    artist = requests.get(artist_api_endpoist, headers=authorization_header)
    artist_data = artist.json()
    print(artist_data)
    # Auth Step 1: Authorization
    return render_template("indexSpotify.html", sorted_array=display_arr)


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


    # Get user playlist data
    playlist_api_endpoint = "{}/playlists".format(profile_data["href"])
    playlists_response = requests.get(playlist_api_endpoint, headers=authorization_header)
    playlist_data = json.loads(playlists_response.text)


    # Combine profile and playlist data to display
    display_arr = [profile_data] + playlist_data["items"] + [{"token": auth_token}]
    return render_template("indexSpotify.html", sorted_array=display_arr)


if __name__ == '__main__':
    app.run(debug=True)