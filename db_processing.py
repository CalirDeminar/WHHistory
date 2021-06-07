import sqlite3, json, os, datetime, requests, numpy
import matplotlib.pyplot as plt
from matplotlib import cm
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
    min_delta = datetime.timedelta(weeks=2)
    t = 0
    j = 0
    for i in character_ids:
        data = list(set(db.execute("SELECT * FROM transfers WHERE character=? ORDER BY date ASC", (i,)).fetchall()))
        data = sorted(data, key=lambda x: x[1])
        last_record = {
            "record_id": "",
            "start_date": 0,
            "character_id": "",
            "source": "",
            "destination": ""
        }
        for record in data:
            record = {
                "record_id": record[0],
                "start_date": record[1],
                "character_id": record[2],
                "source": record[3],
                "destination": record[4]
            }
            if last_record["source"] == "":
                write_short_record(record, db)
                last_record = record
            if isinstance(last_record["start_date"], str):
                last_date = datetime.datetime.fromisoformat(last_record["start_date"].replace("Z", "").replace("T", " "))
                current_date = datetime.datetime.fromisoformat(record["start_date"].replace("Z", "").replace("T", " "))
                diff = current_date - last_date
                is_short_npc_stay = diff < min_delta and record["source"] < 2000000
                if is_short_npc_stay:
                    last_record = {
                        "record_id": record["record_id"],
                        "start_date": record["start_date"],
                        "character_id": record["character_id"],
                        "source": last_record["source"],
                        "destination": record["destination"]
                    }
                else:
                    last_record = record
                    j += 1
                    write_short_record(record, db)

            if t % 1000 == 0:
                print(str(j) + ": " + str(t))
            t += 1
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
    data_net = pd.Series(dtype=int)
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
        data_net[interval.start_time] = count_in + count_out
    print(data_in)
    data_in = data_in.rolling(window=8).mean()
    data_out = data_out.rolling(window=8).mean()
    data_net = data_net.rolling(window=8).mean()
    d = {"In": data_in, "Out": data_out, "Net": data_net}
    data = pd.DataFrame(d)
    print(data)
    plt.close("all")
    plt.figure(figsize=(20, 7.5))
    plt.plot(data["In"], color="green")
    plt.plot(data["Out"], color="red")
    plt.plot(data["Net"], color="grey")
    plt.axhline(y=0, color='k')
    plt.legend(["In", "Out", "Net"])
    plt.title(label=corp_name)
    i = data_out.min()
    j = data_in.max()
    print(j)
    for entry in e_data:
        if entry["ts"] > start:
            plt.axvline(entry["ts"])
            if i >= (j - (j / 6)):
                i = data_out.min()
            else:
                i += j / 6
    plt.savefig("./graphs/" + corp_name + ".png")


def get_corp_dict(db):
    corps = db.execute("SELECT * FROM corps")
    output = {}
    for line in corps:
        output[line[0]] = line[1]
    return output


def graph_corp_to_corp_char_movement(db, corp_name):
    corp_id = get_corp_id(db, corp_name)
    print(corp_id)
    transfers_in = db.execute("SELECT * FROM transfers_minus_short_npc WHERE destination=? ORDER BY date ASC", (corp_id,)).fetchall()
    transfers_out = db.execute("SELECT * FROM transfers_minus_short_npc WHERE source=? ORDER BY date ASC", (corp_id,)).fetchall()
    all_corps = list(set(list(map(lambda x: x[3], transfers_in)) + list(map(lambda x: x[4], transfers_out))))
    corp_lookup = get_corp_dict(db)
    start_date_string = db.execute("SELECT MIN(date) FROM transfers WHERE destination=?", (corp_id,)).fetchall()[0][0]
    start = datetime.datetime.fromisoformat(start_date_string.replace("T", " ").replace("Z", ""))
    end = datetime.datetime.now()
    date_range = pd.Series(pd.period_range(start=start, end=end, freq="W"))
    data_in = {}
    data_out = {}
    # looking for dict of corp ids with series of weekly in and out
    for key in all_corps:
        data_in[key] = pd.Series(dtype=int)
        data_out[key] = pd.Series(dtype=int)
    for interval in date_range:
        for key in all_corps:
            data_in[key][interval.start_time] = 0
            data_out[key][interval.start_time] = 0
        for transfer in transfers_in:
            ts = datetime.datetime.fromisoformat(transfer[1].replace("T", " ").replace("Z", ""))
            if interval.start_time < ts < interval.end_time:
                target_id = transfer[3]
                data_in[target_id][interval.start_time] += 1
        for transfer in transfers_out:
            ts = datetime.datetime.fromisoformat(transfer[1].replace("T", " ").replace("Z", ""))
            if interval.start_time < ts < interval.end_time:
                target_id = transfer[4]
                data_out[target_id][interval.start_time] += 1
    output_in = {}
    output_out = {}
    for key in data_in:
        if key > 2000000:
            output_in[corp_lookup[key]] = data_in[key].rolling(window=8).mean()
    data_in = pd.DataFrame(output_in)
    e_data = get_eviction_dict()
    plt.close("all")
    plot_in = data_in.plot.area()
    plot_in.set_title(corp_name)
    for entry in e_data:
        if entry["ts"] > start:
            plot_in.axvline(entry["ts"])
    plot_in = plot_in.get_figure()
    plot_in.set_size_inches(20, 7.5)

    plot_in.savefig("./graphs/" + corp_name + "_stacked_minus_npc.png")
    print("./graphs/" + corp_name + "_stacked_direct.png")

    # data_in = data_in.rolling(window=8).mean()
    # data_out = data_out.rolling(window=8).mean()


def main():
    db = sqlite3.connect('WHHistory2.sqlite3')
    set_up_tables(db)
    corps = ["All Consuming Darkness",
                 "All-Out",
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
                 "Adhocracy Incorporated"]
    for corp in corps:
        graph_corp_to_corp_char_movement(db, corp)

main()
