import getpass
import urllib.request
import json
import psycopg2
from collections import deque
import github3


graph = set()
br_queue = deque()


def serialize_arr(array):
    if len(array) == 0:
        return "NULL"
    serialized = "ARRAY["

    for i in array:
        if i == "Ren'Py":
            i = "Ren''Py"
        serialized += "\'" + str(i) + "\',"

    return serialized[:-1] + "]"


def main(br_queue,G):
    br_queue.appendleft(" ")

    level = 0
    while len(br_queue) != 0 and level < 3:
        login = br_queue.pop()

        print(login)

        if login not in graph:
            followers = []
            following = []
            count = 0

            company = G.user(login).company
            if company and len(company) > 250:
                company = company[:250]
            iterator_follower = G.iter_followers(login)

            bool = False

            # weird!

            for f in iterator_follower:
                followers.append(str(f))
                count += 1
                if count > 350:
                    bool = True
                    break

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

            iterator_orgs = G.iter_orgs(login)

            organizations = []

            for f in iterator_orgs:
                organizations.append(str(f))

            graph.add(login)

            languages_set = set()

            br_queue.extendleft(followers)
            br_queue.extendleft(following)

            # repo languages digging part

            iterator_repos = G.iter_user_repos(login)

            for each in iterator_repos:
                if each.language not in languages_set:
                    languages_set.add(each.language)

            followers_serialized = serialize_arr(followers)
            followings_serialized = serialize_arr(following)
            organizations_serialized = serialize_arr(organizations)
            languages_serialized = serialize_arr(languages_set)

            sql = "INSERT INTO users SELECT %s, %s," + followers_serialized + "," + \
                  followings_serialized + "," + languages_serialized + "," + organizations_serialized + " WHERE NOT EXISTS (SELECT 1 FROM users WHERE login=%s);"
            cursor.execute(sql, (login, company, login,))
            conn.commit()



if __name__ == "__main__":
    # connect to db
    connect_str = "dbname='GithubData' host='localhost'"
    conn = psycopg2.connect(connect_str)
    cursor = conn.cursor()

    sql = "SELECT * FROM users;"
    cursor.execute(sql)
    conn.commit()

    for record in cursor:
        graph.add(record[0].strip())
        if record[2]:
            for each in record[2]:
                br_queue.appendleft(str(each))

        if record[3]:
            for each in record[3]:
                br_queue.appendleft(str(each))

    # github connection
    login = input("uname: ")
    login_pass = input("upass: ")
    token = input("token: ")
    br_queue.append(login)
    G = github3.login(username=login, password=login_pass, token=token,
                      two_factor_callback=None)
    while True:
        try:
            main(br_queue, G)
        except github3.models.GitHubError:
            uname = input("uname: ")
            upass = input("upass: ")
            G = github3.login(username=uname, password=upass, token=token,
                                      two_factor_callback=None)
