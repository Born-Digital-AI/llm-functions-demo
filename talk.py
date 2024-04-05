import requests
import urllib.parse
import sys

def encode_text(text):
    return urllib.parse.quote(text)

def main():
    if len(sys.argv) != 3:
        print("Usage: python script.py <text>")
        sys.exit(1)

    CID = sys.argv[1]
    text_to_encode = sys.argv[2]
    encoded_text = encode_text(text_to_encode)

    url = f"http://0.0.0.0:8824/conversation/{CID}/user/"
    params = {
        'text': encoded_text
    }

    response = requests.get(url, params=params)

    print(response.text)

if __name__ == "__main__":
    main()

