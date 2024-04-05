import requests
import urllib.parse
import sys

def main():
    if len(sys.argv) != 2:
        print("Usage: python script.py <text>")
        sys.exit(1)

    CID = sys.argv[1]

    url = f"http://0.0.0.0:8824/conversation/simulate/{CID}"

    response = requests.get(url)

    print(response.text)

if __name__ == "__main__":
    main()

