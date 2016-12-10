import psycopg2


def main():
    connect_str = "dbname='GithubData' host='localhost'"
    conn = psycopg2.connect(connect_str)
    cursor = conn.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS users (login char(40), followers text[], following text[], languages text[], organizations text[]);""")
    cursor.execute("""CREATE TABLE IF NOT EXISTS orgs (login char(40), members text[]);""")
    conn.commit()


if __name__ == "__main__":
    main()
