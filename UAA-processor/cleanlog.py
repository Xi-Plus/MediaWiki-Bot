import datetime
import pymysql

from config import DB  # pylint: disable=E0611,W0614

db = pymysql.connect(
    host=DB['host'],
    user=DB['user'],
    passwd=DB['pass'],
    db=DB['db'],
    charset=DB['charset']
)
cur = db.cursor()

timestamp = (datetime.datetime.now() - datetime.timedelta(days=30)).strftime('%Y-%m-%d %H:%M:%S')
print('Delete log before {}'.format(timestamp))

cur.execute("""DELETE FROM `{}` WHERE `time` < %s""".format(DB['table']), (timestamp))
db.commit()

cur.close()
db.close()
