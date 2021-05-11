import os


def combine_ids():
    ids = []
    for filename in os.listdir("./char_id_dumps"):
        file = open("./char_id_dumps/" + filename, "r")
        for row in file:
            ids.append(row)
        file.close()
    ids = list(set(ids))
    output = ""
    for id in ids:
        output += id
    file = open("./combined_ids.dat", "w")
    file.write(output)
    file.close()
    print(len(ids))


combine_ids()
