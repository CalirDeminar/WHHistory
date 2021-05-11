import requests, json, time, os, sqlite3, datetime
from multiprocessing import Pool


def set_up_tables(db):
    db.execute('''CREATE TABLE IF NOT EXISTS corps (id number, name text)''')
    db.execute('''CREATE TABLE IF NOT EXISTS characters (id number, name text)''')
    db.execute(
        '''CREATE TABLE IF NOT EXISTS transfers ''' +
        '''(id text, date text, character number, source number, destination number)'''
    )
    db.execute(
        '''CREATE TABLE IF NOT EXISTS transfers_minus_short_npc ''' +
        '''(id text, date text, character number, source number, destination number)'''
    )


def transfer_already_added(record_id, db):
    query_output = db.execute("SELECT * FROM transfers WHERE id=" + str(record_id)).fetchall()
    return len(query_output) > 0


def fetch_character_history(character_id, db, existing_records):
    charId = character_id.replace("\n", "")
    print("\nGetting " + charId)
    headers = requests.utils.default_headers()
    headers.update({'User-Agent': 'Contact Calir Deminar'})
    url = ("https://esi.evetech.net/latest/characters/" +
           charId +
           "/corporationhistory/?datasource=tranquility")
    resp = requests.get(url, headers=headers).json()
    current_corp = 0
    for line in resp:
        if "corporation_id" in line and \
                "record_id" in line and \
                "start_date" in line and \
                current_corp != 0 and \
                (line["record_id"],) not in existing_records:
            output = {
                "character": charId,
                "date": line["start_date"],
                "id": line["record_id"],
                "source": int(current_corp),
                "destination": int(line["corporation_id"])
            }
            db.execute("INSERT INTO transfers VALUES(?, ?, ?, ?, ?)",
                       (output["id"], output["date"], output["character"], output["source"], output["destination"]))
        if "corporation_id" in line:
            current_corp = line["corporation_id"]
    db.commit()


def get_combined_corp_history(db):
    with open("./combined_ids.dat", "r") as file:
        existing_records = db.execute("SELECT id FROM transfers").fetchall()
        print(existing_records)
        last = datetime.datetime.now()
        for line in file:
            fetch_character_history(line, db, existing_records)
            now = datetime.datetime.now()
            print(now - last)
            last = now

    file.close()


if __name__ == '__main__':
    db = sqlite3.connect('WHHistory2.sqlite3')
    set_up_tables(db)
    get_combined_corp_history(db)
