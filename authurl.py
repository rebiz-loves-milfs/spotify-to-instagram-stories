import os

# Distributed as it is.
# Run this file with the environment variable CLIENT_ID set, or fill it below.
client_id = os.environ.get("CLIENT_ID", "")
redirect_uri = "https://example.com/"
authorize_url = "https://accounts.spotify.com/authorize"

def get_auth_url():
    if not client_id:
        return "Error: client_id is not set. Please set the CLIENT_ID env variable or edit this file."
    return f"{authorize_url}?response_type=code&client_id={client_id}&redirect_uri={redirect_uri}&scope=user-read-currently-playing"

if __name__ == "__main__":
    print(get_auth_url())
