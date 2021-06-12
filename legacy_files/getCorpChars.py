import re, requests, json, os


def split_to_five_hundred(array):
    n = 100
    return [array[i * n:(i + 1) * n] for i in range((len(array) + n - 1) // n)]


def parse_evewho(filename):
    names = []
    corp_name = filename.replace("/", "").replace("evewho_dumps", "").replace(".dat", "")
    output_filename = corp_name + "_charids.txt"
    if output_filename not in os.listdir("../char_id_dumps"):
        print(corp_name)
        with open("./evewho_dumps/" + filename, "r") as file:
            for row in file:
                reduced = re.sub('\d\d\d\d\/\d\d\/\d\d \d\d\:\d\d', '', row).strip()
                if len(reduced) > 0:
                    names.append(reduced)
        file.close()
        names = list(set(names))
        characters = []
        for sub in split_to_five_hundred(names):
            resp = requests.post(
                    "https://esi.evetech.net/latest/universe/ids/?datasource=tranquility&language=en",
                    data=json.dumps(sub),
                    headers={'Accept': 'application/json', 'Accept-Language': 'en', 'Content-Type': 'application/json'}
                ).json()
            characters += resp['characters']
        output_characters = ""
        for character in characters:
            output_characters += (str(character['id']) + "\n")
        out = open("./char_id_dumps/" + output_filename, "w")
        out.write(output_characters)
        out.close()
    else:
        print(corp_name + " Already Processed")


def run():
    for file in os.listdir("../evewho_dumps"):
        parse_evewho(file)


run()
