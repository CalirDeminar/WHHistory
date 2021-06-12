import os
import re


class EveWhoParser:
    @staticmethod
    def get_evewho_dumps():
        return os.listdir("./evewho_dumps")

    @staticmethod
    def parse_evewho_file(filename):
        if filename in os.listdir("./evewho_dumps"):
            names = []
            with open("./evewho_dumps/" + filename, "r") as file:
                for row in file:
                    reduced = re.sub('\d\d\d\d\/\d\d\/\d\d \d\d\:\d\d', '', row).strip()
                    if len(reduced) > 0:
                        names.append(reduced)
            file.close()
            return names
        else:
            raise Exception("File Not Found")

    @staticmethod
    def get_full_character_list():
        corps = list(
            map(
                lambda r: EveWhoParser.parse_evewho_file(r), EveWhoParser.get_evewho_dumps()
            )
        )
        characters = []
        for corp in corps:
            characters = characters + corp
        return list(set(characters))
