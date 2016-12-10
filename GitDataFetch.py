import urllib.request
import json
import psycopg2


def fetch_from_mult(url, key):
    out_arr = []

    response = urllib.request.urlopen(url)
    output = response.read().decode('utf-8')
    _json = json.loads(output)

    for each in _json:
        out_arr.append(each['login'])
    return out_arr


def serialize_arr(array):
    serialized = "ARRAY["

    for i in array:
        serialized += "\\\'" + str(i) + "\\\',"

    return serialized[:-1] + "]"


def main():
    connect_str = "dbname='GithubData' host='localhost'"
    conn = psycopg2.connect(connect_str)
    cursor = conn.cursor()
#    cursor.execute("""CREATE TABLE users (login char(40), followers text[], following text[], languages text[], organizations text[]);""")
#    conn.commit()

    response = urllib.request.urlopen("https://api.github.com/users/furkansahin")
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
    print("hey")

    followers_serialized = serialize_arr(followers)
    followings_serialized = serialize_arr(following)
    organizations_serialized = serialize_arr(organization_map.keys())
    languages_serialized = serialize_arr(languages_map.keys())

    sql = "INSERT INTO users VALUES('furkansahin'," + followers_serialized + "," + followings_serialized + "," + languages_serialized + "," + organizations_serialized + ");"
    cursor.execute(sql)
    conn.commit()


if __name__ == "__main__":
    main()