import sqlite3, json, os, datetime, requests, numpy
import matplotlib.pyplot as plt
import pandas as pd


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


def corp_already_added(corp_id, db):
    query_output = db.execute("SELECT * FROM corps WHERE id=?", corp_id).fetchall()
    return len(query_output) > 0


def added_characters(db):
    return db.execute("SELECT DISTINCT character FROM transfers").fetchall()


def transfer_already_added(record_id, db):
    query_output = db.execute("SELECT * FROM transfers WHERE id=" + str(record_id)).fetchall()
    return len(query_output) > 0


def valid_transfer_record(record, db):
    return (not isinstance(record, str) and
            "record_id" in record and
            "corporation_id" in record and
            "start_date" in record and
            not transfer_already_added(record["record_id"], db))


def read_corp_history(filename, db):
    cursor = db.cursor()
    file = open("./char_histories/" + filename, "r").read()
    data = json.loads(file)
    character_id = int(filename.replace("-history.json", ""))
    # put character into character table
    current_corp = ""
    for transfer in data:
        if valid_transfer_record(transfer, db):
            if current_corp == "":
                current_corp = int(transfer["corporation_id"])
            else:
                target = int(transfer["corporation_id"])
                cursor.execute(
                 "INSERT INTO transfers VALUES (?, ?, ?, ?, ?)",
                    (
                        str(transfer["record_id"]),
                        str(transfer["start_date"]),
                        character_id,
                        current_corp,
                        target
                     )
                )
                current_corp = target
                db.commit()


def transfer():
    db = sqlite3.connect('WHHistory.sqlite3')
    set_up_tables(db)
    i = 0
    files = os.listdir("./char_histories")
    characters = added_characters(db)
    print(characters)
    for file in files:
        character_id = int(file.replace("-history.json", ""))
        if not (int(character_id),) in characters:
            print("File " + str(i) + " of " + str(len(files)))
            read_corp_history(file, db)
        i += 1
    db.close()


def write_short_record(record, db):
    db.execute(
        "INSERT INTO transfers_minus_short_npc VALUES (?, ?, ?, ?, ?)",
        (
            record["record_id"],
            record["start_date"],
            record["character_id"],
            record["source"],
            record["destination"]
        )
    )


def skip_short_npc_transfers(db):
    character_ids = list(map(lambda r: r[0], db.execute("SELECT DISTINCT character from transfers").fetchall()))
    for i in character_ids:
        data = list(set(db.execute("SELECT * FROM transfers WHERE character=?", (i,)).fetchall()))
        last_transfer = 0
        last_corp = ""
        for record in data:
            record = {
                "record_id": record[0],
                "start_date": record[1],
                "character_id": record[2],
                "source": record[3],
                "destination": record[4]
            }
            if last_corp == "":
                write_short_record(record, db)
            if isinstance(last_transfer, str):
                last_date = datetime.fromisoformat(last_transfer)
                current_date = datetime.fromisoformat(record["start_date"])
                diff = last_date.timedelta(current_date)
                print(diff)
            last_corp = record["source"]
            last_transfer = record["start_date"]
        db.commit()


def split(array, n):
    return [array[i * n:(i + 1) * n] for i in range((len(array) + n - 1) // n)]


def populate_corps(db):
    source_corp_list = list(map(lambda r: r[0], db.execute("SELECT source FROM transfers").fetchall()))
    destination_corp_list = list(map(lambda r: r[0], db.execute("SELECT destination FROM transfers").fetchall()))
    corp_list = list(set(source_corp_list + destination_corp_list))
    split_array = split(corp_list, 100)
    for sublist in split_array:
        resp = requests.post(
            "https://esi.evetech.net/latest/universe/names/?datasource=tranquility&language=en",
            data=json.dumps(sublist),
            headers={'Accept': 'application/json', 'Accept-Language': 'en', 'Content-Type': 'application/json'}
        ).json()
        for corp in resp:
            print(corp)
            db.execute("INSERT INTO corps VALUES (?, ?)", (corp["id"], corp["name"]))
        db.commit()


def get_corp_id(db, corp_name):
    return db.execute("SELECT id FROM corps WHERE name=?", (corp_name,)).fetchall()[0][0]


def get_eviction_dict():
    data = []
    file = open("./evictions.dat", "r")
    for line in file:
        split = line.split(": ")
        target = split[0]
        datestring = split[1]
        target = target.strip()
        datestring = datestring.strip()
        ts = datetime.datetime.fromisoformat(datestring.replace("Z", "").replace("T", " ").replace("/", "-"))
        data += [{"ts": ts, "corp_name": target}]
    file.close
    data.sort(key=lambda i: i["ts"].timestamp())
    return data


def graph_corp_char_movement(db, corp_name):
    data_in = pd.Series(dtype=int)
    data_out = pd.Series(dtype=int)
    corp_id = get_corp_id(db, corp_name)
    print(corp_id)
    e_data = get_eviction_dict()
    transfers_in = db.execute("SELECT * FROM transfers WHERE destination=? ORDER BY date ASC", (corp_id,)).fetchall()
    transfers_out = db.execute("SELECT * FROM transfers WHERE source=? ORDER BY date ASC", (corp_id,)).fetchall()
    start_date_string = db.execute("SELECT MIN(date) FROM transfers WHERE destination=?", (corp_id,)).fetchall()[0][0]
    start = datetime.datetime.fromisoformat(start_date_string.replace("T", " ").replace("Z", ""))
    end = datetime.datetime.now()
    date_range = pd.Series(pd.period_range(start=start, end=end, freq="W"))
    for interval in date_range:
        print(interval.start_time)
        count_in = 0
        count_out = 0
        for transfer in transfers_in:
            ts = datetime.datetime.fromisoformat(transfer[1].replace("T", " ").replace("Z", ""))
            if interval.start_time < ts < interval.end_time:
                count_in += 1
        for transfer in transfers_out:
            ts = datetime.datetime.fromisoformat(transfer[1].replace("T", " ").replace("Z", ""))
            if interval.start_time < ts < interval.end_time:
                count_out -= 1
        data_in[interval.start_time] = count_in
        data_out[interval.start_time] = count_out
    print(data_in)
    data_in = data_in.rolling(window=8).mean()
    data_out = data_out.rolling(window=8).mean()
    d = {"in": data_in, "out": data_out}
    data = pd.DataFrame(d)
    print(data)
    plt.close("all")
    plt.figure(figsize=(20, 7.5))
    plt.plot(data)
    plt.axhline(y=0, color='k')
    plt.legend(["In", "Out"])
    plt.title(label=corp_name)
    file = open("./evictions.dat", "r")
    i = data_out.min()
    j = data_in.max()
    print(j)
    for entry in e_data:
        if entry["ts"] > start:
            plt.axvline(entry["ts"])
            plt.text(x=entry["ts"], y=i, s=entry["corp_name"])
            if i >= (j - (j / 6)):
                i = data_out.min()
            else:
                i += j / 6
    file.close()
    plt.savefig("./graphs/" + corp_name + ".png")


def main():
    db = sqlite3.connect('WHHistory2.sqlite3')
    set_up_tables(db)
    for name in ["All-Out",
                 "All Consuming Darkness",
                 "Almost Dangerous",
                 "Another War",
                 "Arctic Light Inc.",
                 "Avanto",
                 "Adhocracy Incorporated",
                 "Dark Venture Corporation",
                 "Epicentre Syndicate",
                 "EyEs.FR",
                 "Foxholers",
                 "Hard Knocks Inc.",
                 "Hidden Baguette",
                 "Holesale",
                 "Inner Hell",
                 "Isogen 5",
                 "Krypted Gaming",
                 "Lazerhawks",
                 "Little Red Riding Hole",
                 "Mass Collapse",
                 "Mind Collapse",
                 "Mouth Trumpet Cavalry",
                 "No Vacancies",
                 "Oruze Cruise",
                 "Out of Focus",
                 "Outfit 418",
                 "POS Party",
                 "Protean Concept",
                 "ShekelSquad",
                 "Singularity Expedition Services",
                 "Violence is the Answer",
                 "Vision Inc",
                 "Wormhole Outlaw",
                 "Wormhole Rats and Fromage",
                 "Ricochet Inc",
                 "Suddenly Carebears",
                 "X-Zest Voyage",
                 "X Legion",
                 "The Dark Space Initiative",
                 "Adhocracy Incorporated"]:
        try:
            graph_corp_char_movement(db, name)
        except:
            print("")


main()
