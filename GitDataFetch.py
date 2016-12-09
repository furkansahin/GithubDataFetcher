import urllib.request
import json
from pprint import pprint


def main():
    response = urllib.request.urlopen("https://api.github.com/users/furkansahin")
    output = response.read().decode('utf-8')

    the_root = json.loads(output)
    followers_url = the_root['followers_url']
    following_url = the_root['following_rul']
    


if __name__ == "__main__":
    main()