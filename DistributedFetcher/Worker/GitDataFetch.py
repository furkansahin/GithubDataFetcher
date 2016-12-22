import sys
import hazelcast
import psycopg2
import github3
import time
exit_code = "%%%%%%%%%%%"

def serialize_arr(array):
    if len(array) == 0:
        return "NULL"
    serialized = "ARRAY["

    for i in array:
        if i == "Ren'Py":
            i = "Ren''Py"
        serialized += "\'" + str(i) + "\',"

    return serialized[:-1] + "]"


def main(br_queue, new_queue, graph_set,lock, G):

    while True:

        print "loop is running"

        while lock.is_locked():
            print "waiting"
            time.sleep(2)

        login = br_queue.poll(5)
        if login == exit_code:
            sys.exit()

        if login:
            if not graph_set.contains(login):
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
                    graph_set.add(login)
                    print(login + " ~~~~~~~~~~~~~~ ")
                    continue

                iterator_orgs = G.iter_orgs(login)

                organizations = []

                for f in iterator_orgs:
                    organizations.append(str(f))

                graph_set.add(login)

                languages_set = set()

                new_queue.add_all(followers)
                new_queue.add_all(following)

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
    connect_str = "dbname='GithubData' host='localhost' user='datauser' password='datapassword'"
    conn = psycopg2.connect(connect_str)
    cursor = conn.cursor()

    #Hazelcast Connections
    config = hazelcast.ClientConfig()
    config.group_config.name = "app1"
    config.group_config.password = "app1-pass"
    config.network_config.addresses.append('207.154.200.83:5701')
    client = hazelcast.HazelcastClient(config)

    credentials = client.get_queue("Credentials").blocking()
    infomap = client.get_map("infoMap").blocking()
    token = infomap.get("token")
    exit_code =  infomap.get("exit")

    logcre = credentials.poll().split("||")
    login = logcre[0]
    login_pass = logcre[1]

    br_queue = client.get_queue("BreadthSearch").blocking()
    new_queue = client.get_queue("NewQueue").blocking()
    graph_set = client.get_set("GraphSet").blocking()

    lock = client.get_lock("QueueLock").blocking()
    G = github3.login(username=login, password=login_pass, token=token,
                      two_factor_callback=None)
    while True:
        try:
            main(br_queue, new_queue, graph_set,lock, G)
        except github3.models.GitHubError:
            logcre = credentials.poll().split("||")
            uname = logcre[0]
            upass = logcre[1]
            G = github3.login(username=uname, password=upass, token=token,
                                      two_factor_callback=None)
