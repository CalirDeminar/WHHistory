import os, json
from multiprocessing import Pool


def run(filename):
    if filename not in os.listdir("./no_npc_char_histories"):
        output = []
        with open("./char_histories/" + filename) as file:
            data = json.loads(file.read())
            for change in data:
                if 'corporation_id' in change and change['corporation_id'] > 2000000:
                    output.append(data)
            output = json.dumps(output)
        file.close()
        file = open("./no_npc_char_histories/" + filename, "w")
        file.write(output)
        file.close()
    else:
        print("Skipping " + filename)


def main():
    with Pool(25) as p:
        p.map(run, os.listdir("./char_histories"))


if __name__ == '__main__':
    main()
