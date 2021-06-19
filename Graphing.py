import numpy
import matplotlib.pyplot as plt
from matplotlib import cm
import pandas as pd
import datetime
import DB
import operator


def get_corp_id(db, corp_name):
    return db.execute("SELECT id FROM corps WHERE name=?", (corp_name,)).fetchall()[0][0]


def get_eviction_dict():
    data = []
    file = open("./evictions.dat", "r")
    for line in file:
        split = line.split(": ")
        target = split[0]
        date_string = split[1]
        target = target.strip()
        date_string = date_string.strip()
        ts = datetime.datetime.fromisoformat(date_string.replace("Z", "").replace("T", " ").replace("/", "-"))
        data += [{"ts": ts, "corp_name": target}]
    file.close
    data.sort(key=lambda i: i["ts"].timestamp())
    return data


def iso_to_datetime(iso):
    return datetime.datetime.fromisoformat(iso.replace("T", " ").replace("Z", ""))


def graph_data(data, start_date, corp_name):
    plt.close("all")
    plt.figure(figsize=(20, 7.5))
    plt.xlabel("Date")
    plt.ylabel("Membership Velocity")
    plt.plot(data["In"], color="green")
    plt.plot(data["Out"], color="red")
    plt.plot(data["Net"], color="grey")
    plt.axhline(y=0, color='k')
    plt.legend(["In", "Out", "Net"])
    plt.title(label=corp_name)
    i = data["Out"].min()
    j = data["In"].max()
    for entry in get_eviction_dict():
        if entry["ts"] > start_date:
            plt.axvline(entry["ts"])
            if i >= (j - (j / 6)):
                i = data["Out"].min()
            else:
                i += j / 6
    plt.savefig("./graphs/" + corp_name + "_velocity.png")


def graph_corp_member_velocity(db, corp_name):
    corp_id = get_corp_id(db, corp_name)
    members_in = pd.Series(dtype=int)
    members_out = pd.Series(dtype=int)
    members_net = pd.Series(dtype=int)
    transfer_data_in = DB.DB.get_transfers_into_corp(db, corp_id)
    transfer_data_out = DB.DB.get_transfers_out_of_corp(db, corp_id)
    start_date = DB.DB.get_corp_starting_date(db, corp_id)
    end_date = datetime.datetime.now()
    date_range = pd.Series(pd.period_range(start=start_date, end=end_date, freq="W"))
    for interval in date_range:
        count_in = 0
        count_out = 0
        for transfer in transfer_data_in:
            ts = iso_to_datetime(transfer["date"])
            if interval.start_time < ts < interval.end_time:
                count_in += 1
        for transfer in transfer_data_out:
            ts = iso_to_datetime(transfer["date"])
            if interval.start_time < ts < interval.end_time:
                count_out -= 1
        members_in[interval.start_time] = count_in
        members_out[interval.start_time] = count_out
        members_net[interval.start_time] = count_in + count_out
    members_in = members_in.rolling(window=8).mean()
    members_out = members_out.rolling(window=8).mean()
    members_net = members_net.rolling(window=8).mean()
    d = {"In": members_in, "Out": members_out, "Net": members_net}
    data = pd.DataFrame(d)
    graph_data(data, start_date, corp_name)


def graph_corp_member_composition_velocity(db, corp_name):
    corp_id = get_corp_id(db, corp_name)
    members_in = {}
    transfer_data_in = DB.DB.get_transfers_into_corp(db, corp_id)
    start_date = DB.DB.get_corp_starting_date(db, corp_id)
    end_date = datetime.datetime.now()
    date_range = pd.Series(pd.period_range(start=start_date, end=end_date, freq="W"))
    corp_lookup = DB.DB.get_corp_dict(db)
    for interval in date_range:
        corps_in = {}
        for transfer in transfer_data_in:
            ts = iso_to_datetime(transfer.date)
            if interval.start_time < ts < interval.end_time:
                source_name = corp_lookup[transfer.source]
                if source_name in corps_in:
                    corps_in[source_name] += 1
                else:
                    corps_in[source_name] = 1
        members_in[interval.start_time] = corps_in
    rolling = pd.DataFrame(rolling_corp_composition_mean(members_in, 8)).transpose()
    total = 0
    for key in rolling:
        total += rolling[key].sum()
    print(len(rolling.keys()))
    # get total impact of each corp
    corp_totals = {}
    for key in rolling:
        corp_totals[key] = rolling[key].sum()
    # get top 10 corps by impact
    top_corps = []
    for i in range(10):
        top_key = max(corp_totals.items(), key=operator.itemgetter(1))[0]
        top_corps.append(top_key)
        corp_totals[top_key] = 0
    # set NAN to 0 and remove non-top-10 corps from the DF
    for key in rolling:
        rolling[key] = rolling[key].fillna(0)
        if key not in top_corps:
            rolling = rolling.drop(columns=[key])
    print(len(rolling.keys()))
    plt.close("all")
    rolling = rolling.plot.area()
    rolling = rolling.get_figure()
    rolling.set_size_inches(20, 7.5)
    plt.xlabel("Date")
    plt.ylabel("Membership Composition")
    plt.title(label=corp_name)
    for entry in get_eviction_dict():
        if entry["ts"] > start_date:
            plt.axvline(entry["ts"], c='black')
    plt.savefig("./graphs/" + corp_name + "_composition_velocity.png")


def rolling_corp_composition_mean(data, window):
    length = len(data) - window
    keys = list(data.keys())
    output = {}
    for o in range(0, length):
        segment = {}
        for i in range(o, o + window):
            val = data[keys[i]]
            for key in val:
                if key in segment:
                    segment[key] += val[key]
                else:
                    segment[key] = val[key]
        output[keys[o]] = segment
    return output
