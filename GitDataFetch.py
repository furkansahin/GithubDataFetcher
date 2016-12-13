import getpass
import urllib.request
import json
import psycopg2
from collections import deque
import github3


def serialize_arr(array):
    if len(array) == 0:
        return "NULL"
    serialized = "ARRAY["

    for i in array:
        serialized += "\'" + str(i) + "\',"

    return serialized[:-1] + "]"


def main():
    G = github3.login(username="furkansahin", password="X", token="X",
                      two_factor_callback=None)
    # connect to db
    connect_str = "dbname='GithubData' host='localhost'"
    conn = psycopg2.connect(connect_str)
    cursor = conn.cursor()

    login = "furkansahin"
    graph = set()
    br_queue = deque()
    br_queue.append(login)

    while len(br_queue) != 0:
        login = br_queue.pop()

        if login not in graph:
            followers = []
            following = []
            count = 0

            try:
                iterator_follower = G.iter_followers(login)
            except github3.models.GitHubError:
                uname = input("uname: ")
                upass = input("upass: ")
                G = github3.login(username=uname, password=upass, token="X",
                                  two_factor_callback=None)
                iterator_follower = G.iter_followers(login)

            bool = False

            # weird!

            for f in iterator_follower:
                followers.append(str(f))
                count += 1
                if count > 350:
                    bool = True
                    break

            try:
                iterator_following = G.iter_following(login)
            except github3.models.GitHubError:
                uname = input("uname: ")
                upass = input("upass: ")
                G = github3.login(username=uname, password=upass, token="b9a4f10e9eda529d094837981b931a2aea5ace99",
                                  two_factor_callback=None)
                iterator_following = G.iter_following(login)


            count = 0
            for f in iterator_following:
                following.append(str(f))
                count += 1
                if count > 350:
                    bool = True
                    break

            if bool:
                graph.add(login)
                print(login + " ~~~~~~~~~~~~~~ ")
                continue

            try:
                iterator_orgs = G.iter_orgs(login)
            except github3.models.GitHubError:
                uname = input("uname: ")
                upass = input("upass: ")
                G = github3.login(username=uname, password=upass, token="X",
                                  two_factor_callback=None)
                iterator_orgs = G.iter_orgs(login)

            organizations = []

            for f in iterator_orgs:
                organizations.append(str(f))

            graph.add(login)

            organization_map = {}
            languages_set = set()

            br_queue.extendleft(followers)
            br_queue.extendleft(following)

            # # organization map filling part
            # response = urllib.request.urlopen(organizations_url)
            # if response.getcode() != 200:
            #     return
            #
            # output = response.read().decode('utf-8')
            # _json = json.loads(output)
            # for each in _json:
            #     members = []
            #     response = urllib.request.urlopen(each['members_url'][:-9])
            #
            #     if response.getcode() != 200:
            #         return
            #
            #     output = response.read().decode('utf-8')
            #     members_json = json.loads(output)
            #     for each_member in members_json:
            #         members.append(each_member['login'])
            #
            #     br_queue.extend(members)
            #     members_serialized = serialize_arr(members)
            #     sql = "INSERT INTO orgs SELECT %s," + members_serialized + " WHERE NOT EXISTS (SELECT 1 FROM orgs WHERE login=%s);"
            #     cursor.execute(sql, (each['login'], each['login'],))
            #     organization_map[each['login']] = members

            # repo languages digging part
            try:
                iterator_repos = G.iter_user_repos(login)
            except github3.models.GitHubError:
                uname = input("uname: ")
                upass = input("upass: ")
                G = github3.login(username=uname, password=upass, token="X",
                                  two_factor_callback=None)
                iterator_repos = G.iter_user_repos(login)

            for each in iterator_repos:
                if each.language not in languages_set:
                    languages_set.add(each.language)

            followers_serialized = serialize_arr(followers)
            followings_serialized = serialize_arr(following)
            organizations_serialized = serialize_arr(organization_map.keys())
            languages_serialized = serialize_arr(languages_set)

            sql = "INSERT INTO users SELECT %s," + followers_serialized + "," + \
                  followings_serialized + "," + languages_serialized + "," + organizations_serialized + " WHERE NOT EXISTS (SELECT 1 FROM users WHERE login=%s);"
            cursor.execute(sql, (login, login,))
            conn.commit()

            print(login)


if __name__ == "__main__":
    main()
