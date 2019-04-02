from config import cfg
import pymysql

db = pymysql.connect(host=cfg['database']['host'],
                     user=cfg['database']['user'],
                     passwd=cfg['database']['passwd'],
                     db=cfg['database']['db'],
                     charset=cfg['database']['charset'])
cur = db.cursor()

cur.execute("""SELECT `title` FROM `UnwatchedPages`""")
rows = cur.fetchall()
oldtitles = set()
for row in rows:
    oldtitles.add(row[0])

print('There are {} itmes in database'.format(len(oldtitles)))
print('Input titles:')

newtitles = set()
while len(newtitles) < cfg['list_size']:
    title = input()
    if not title:
        continue
    newtitles.add(title.strip())

print('-' * 50)

cntadd = 0
for title in newtitles:
    if title in oldtitles:
        oldtitles.remove(title)
    else:
        cur.execute("""INSERT INTO `UnwatchedPages` (`title`) VALUES (%s)""",
                    (title))
        print('Add', title)
        cntadd += 1

cntremove = 0
for title in oldtitles:
    cur.execute("""DELETE FROM `UnwatchedPages` WHERE `title` = %s""",
                (title))
    print('Remove', title)
    cntremove += 1

db.commit()
print('Done. {} added. {} removed.'.format(cntadd, cntremove))
