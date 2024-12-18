import os
import pprint

from misskey import Misskey

test = "a1xol9w99kiu0487"

INSTANCE = os.getenv("INSTANCE")
TOKEN = os.getenv("TOKEN")
USERNAME = os.getenv("USERNAME")

mk = Misskey(INSTANCE, i=TOKEN)

# pprint.pprint(mk.notes_show(note_id='a0tvbygse4ps000g'))

# user = mk.users_show(user_id='a0ctf40bhc3a09cv')
user = mk.users_show(user_id='a0cj5mqxoz2e0001')

if user['host']:
    username = '@' + user['username'] + '@' + user['host']
else:
    username = '@' + user['username']

print(username)
#
# pprint.pprint(mk.users_following(user_id='a0cj5mqxoz2e0001'))
