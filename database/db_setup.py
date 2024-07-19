import psycopg2

conn = psycopg2.connect("dbname=yourdatabase user=yourusername password=yourpassword")
cur = conn.cursor()

cur.execute(open("init.sql", "r").read())
conn.commit()

cur.close()
conn.close()
