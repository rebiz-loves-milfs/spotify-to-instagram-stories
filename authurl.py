#Distributed as it is.
#Run this file by filling the client id to get the SPOTIFY_TOKEN
client_id=''
redirect_uri="https://example.com/"
authorize_url = "https://accounts.spotify.com/authorize"
token_url = "https://accounts.spotify.com/api/token"







def getAuthUrl():
        authorization_redirect_url = authorize_url + '?response_type=code&client_id=' + \
            client_id + '&redirect_uri=' + redirect_uri + \
            '&scope=user-read-currently-playing'
        return authorization_redirect_url
print(getAuthUrl())
