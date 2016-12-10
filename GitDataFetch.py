import urllib.request
import json
import psycopg2
from collections import deque


def fetch_from_mult(url, key):
    out_arr = []

    response = urllib.request.urlopen(url)
    output = response.read().decode('utf-8')
    _json = json.loads(output)

    for each in _json:
        out_arr.append(each['login'])
    return out_arr


def serialize_arr(array):
    if len(array) == 0:
        return "NULL"
    serialized = "ARRAY["

    for i in array:
        serialized += "\'" + str(i) + "\',"

    return serialized[:-1] + "]"


def main():
    limit = 10000


    # connect to db
    connect_str = "dbname='GithubData' host='localhost'"
    conn = psycopg2.connect(connect_str)
    cursor = conn.cursor()

    password_mgr = urllib.request.HTTPPasswordMgrWithDefaultRealm()
    top_level_url = "https://api.github.com/"
    password_mgr.add_password(None, top_level_url, 'furkansahin', '707494Fb')

    handler = urllib.request.HTTPBasicAuthHandler(password_mgr)

    opener = urllib.request.build_opener(handler)

    # use the opener to fetch a URL
    opener.open("https://api.github.com/users/furkansahin")

    # Install the opener.
    # Now all calls to urllib.request.urlopen use our opener.
    urllib.request.install_opener(opener)

    login = 'furkansahin'
    graph = set()
    br_queue = deque()
    br_queue.append(login)

    while len(br_queue) != 0:
        login = br_queue.popleft()

        if login not in graph:
            graph.add(login)

            response = urllib.request.urlopen("https://api.github.com/users/" + login)
            output = response.read().decode('utf-8')

            the_root = json.loads(output)
            followers_url = the_root['followers_url']
            following_url = the_root['following_url'][:-13]
            organizations_url = the_root['organizations_url']
            repos_url = the_root['repos_url']

            login = the_root['login']
            followers = fetch_from_mult(followers_url, "login")
            following = fetch_from_mult(following_url, "login")
            organization_map = {}
            languages_map = {}

            br_queue.extend(followers)
            br_queue.extend(following)

            # organization map filling part
            response = urllib.request.urlopen(organizations_url)
            output = response.read().decode('utf-8')
            _json = json.loads(output)
            for each in _json:
                members = []
                response = urllib.request.urlopen(each['members_url'][:-9])
                output = response.read().decode('utf-8')
                members_json = json.loads(output)
                for each_member in members_json:
                    members.append(each_member['login'])

                br_queue.extend(members)
                members_serialized = serialize_arr(members)
                sql = "INSERT INTO orgs SELECT %s," + members_serialized +" WHERE NOT EXISTS (SELECT 1 FROM orgs WHERE login=%s);"
                cursor.execute(sql, (each['login'],each['login'],))
                organization_map[each['login']] = members

            # repo languages digging part
            response = urllib.request.urlopen(repos_url)
            output = response.read().decode('utf-8')
            _json = json.loads(output)
            for each in _json:
                if each['language'] in languages_map:
                    languages_map[each['language']] += 1
                else:
                    languages_map[each['language']] = 1

            followers_serialized = serialize_arr(followers)
            followings_serialized = serialize_arr(following)
            organizations_serialized = serialize_arr(organization_map.keys())
            languages_serialized = serialize_arr(languages_map.keys())

            sql = "INSERT INTO users SELECT %s," + followers_serialized + "," + \
                  followings_serialized + "," + languages_serialized + "," + organizations_serialized + " WHERE NOT EXISTS (SELECT 1 FROM users WHERE login=%s);"
            cursor.execute(sql, (login,login,))
            conn.commit()


if __name__ == "__main__":
    main()
