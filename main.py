import datetime
import logging
import os
import threading
import time

import schedule
import sentry_sdk
from misskey import Misskey, NoteVisibility
from sentry_sdk.integrations.asyncio import AsyncioIntegration
from sentry_sdk.integrations.logging import LoggingIntegration

INSTANCE = os.getenv("INSTANCE")
TOKEN = os.getenv("TOKEN")
USERNAME = os.getenv("USERNAME")
SENTRY_DSN = os.getenv("SENTRY_DSN")

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", encoding='utf-8')

sentry_sdk.init(SENTRY_DSN,
                integrations=[LoggingIntegration(level=logging.INFO, event_level=logging.WARN),
                              AsyncioIntegration()], traces_sample_rate=1.0, profiles_sample_rate=1.0)

mk = Misskey(INSTANCE, i=TOKEN)


def summarize_user(user_id: str):
    user = mk.users_show(user_id=user_id)
    if user['host']:
        mention = '@' + user['username'] + '@' + user['host']
    else:
        mention = '@' + user['username']

    logging.info(f'Summarizing user {mention}')

    notes = 0
    renotes = 0
    quotes = 0
    replies = 0

    total_reactions = 0
    reactions = {}

    total = 0

    for note in mk.users_notes(user_id=user_id, include_replies=True, include_my_renotes=True, limit=100,
                               since_date=datetime.datetime.today() - datetime.timedelta(days=1)):
        if 'reactions' in note:
            for k, v in note['reactions'].items():
                if not k in reactions:
                    reactions[k] = 0
                reactions[k] = reactions[k] + 1
                total_reactions = total_reactions + v

        total = total + 1
        if note['renoteId'] and note['text']:
            quotes = quotes + 1
        elif note['renoteId']:
            renotes = renotes + 1
        elif note['replyId']:
            replies = replies + 1
        else:
            notes = notes + 1

    reactions = sorted(reactions.items(), key=lambda x: x[1], reverse=True)

    logging.info(f'Notes: {notes}, Renotes: {renotes}, Quotes: {quotes}, Replies: {replies}')
    logging.info(f'Total: {total}')
    logging.info(f'{notes + renotes + quotes + replies} === {total}')
    logging.info(f'Summarizing user {mention} finished')

    base_note = f'''
$[x2 Fedi Note Summary]

{mention}

- **Notes**: {notes}
- **Quote Notes**: {quotes}
- **Reply Notes**: {replies}
- **Renotes**: {renotes}'''

    if len(reactions) > 0:
        base_note = base_note + f'''

$[x2 Reactions on Your Posts]
- **Total Reactions**: {total_reactions}
- **Most Popular Reaction**: {reactions[0][0]} {reactions[0][1]}x'''

    mk.notes_create(base_note, visibility=NoteVisibility.SPECIFIED, visible_user_ids=[user_id])


def do_summarization():
    logging.info('Running summarization')
    user = mk.i()
    followers = mk.users_followers(user_id=user['id'])
    threads = []

    for follower in followers:
        t = threading.Thread(target=summarize_user, args=(follower['followerId'],))
        t.start()
        logging.info('Started thread', t.name)

    for thread in threads:
        thread.join()


if __name__ == "__main__":
    logging.info('Startup')
    schedule.every().day.at("00:00:00").do(do_summarization)

    while True:
        schedule.run_pending()
        time.sleep(1)
