# charId, corpId, joined date
# get corp relevant IDs from corp ID dump
# for each character, get the next 5 corps they joined after leaving the corp of interest
# sum the no. characters heading into each corp for each corp after leaving
import json, requests, os


def get_corp_id(name):
    corp_name = name.replace("_", " ")
    url = "https://esi.evetech.net/latest/universe/ids/?datasource=tranquility&language=en"
    resp = requests.post(
        "https://esi.evetech.net/latest/universe/ids/?datasource=tranquility&language=en",
        data=json.dumps([corp_name]),
        headers={'Accept': 'application/json', 'Accept-Language': 'en', 'Content-Type': 'application/json'}
    ).json()
    return resp["corporations"][0]["id"]


def get_corp_name(id):
    if id != "npc":
        url = "https://esi.evetech.net/latest/corporations/" + str(id) + "/?datasource=tranquility"
        resp = requests.get(url).json()
        return resp["name"]
    else:
        return "npc"


def find_joined_index(data, target_corp_id):
    i = 0
    for entry in data:
        if "corporation_id" in entry and entry["corporation_id"] == target_corp_id:
            return i
        else:
            i += 1
    return -1


def update_frequency_table(table, data, base, offset):
    if ((base - offset) > 0) and (len(data) > (base - offset)) and isinstance(data, list):
        corp_id = data[base - offset]["corporation_id"]
        output = table
        if corp_id in table:
            output[corp_id] += 1
        else:
            output[corp_id] = 1
        return output
    else:
        return table


def print_frequency_table(table, lower_limit):
    print("--------")
    out = {}
    for k,v in sorted(table.items(), key=lambda kv:(kv[1], kv[0])):
        if v > lower_limit:
            out[get_corp_name(k)] = v
            print(get_corp_name(k) + ": " + str(v))
    return out


def get_next_corps(corp_name):
    output = {}
    target_corp_id = get_corp_id(corp_name)
    with open("./char_id_dumps/" + corp_name + "_charids.txt", "r") as file:
        for line in file:
            char_id = line.replace("\n", "").strip()
            history_file = open("./char_histories/" + char_id + "-history.json", "r")
            data = json.loads(history_file.read())
            history_file.close()
            joined_index = find_joined_index(data, target_corp_id)
            for i in range(-3, 6):
                if i not in output:
                    output[i] = {}
                output[i] = update_frequency_table(output[i], data, joined_index, i)
    file.close()
    out = {}
    for k in output.keys():
        print("\n" + str(k))
        out[k] = print_frequency_table(output[k], 4)
    return out


def run():
    save_data = {}
    for corpname in os.listdir("../evewho_dumps"):
        corp_name = corpname.replace(".dat", "")
        save_data[corp_name] = get_next_corps(corp_name)
    output_file = open("../corp_sourcing.json", "w")
    output_file.write(json.dumps(save_data))


run()
