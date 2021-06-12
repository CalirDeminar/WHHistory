import Esi
import Transfer


def split_array(array, n):
    return [array[i * n:(i + 1) * n] for i in range((len(array) + n - 1) // n)]


class Character:
    id = ""
    name = ""

    def __init__(self, char_id, name):
        self.id = char_id
        self.name = name

    @staticmethod
    def get_characters_from_names(name_array):
        names = list(set(name_array))
        characters = []
        for sub in split_array(names, 100):
            resp = Esi.get_ids(sub)
            characters += map(lambda c: Character(c["id"], c["name"]), resp["characters"])
            print(".")
        return characters

    @staticmethod
    def insert_characters(db, characters):
        for char in characters:
            db.execute("INSERT INTO characters VALUES (?, ?);", (char.id, char.name))
        db.commit()

    @staticmethod
    def all_characters(db):
        return db.execute("SELECT DISTINCT character FROM transfers").fetchall()

    @staticmethod
    def get_corp_transfers(character):
        history = list(filter(
            lambda t: "corporation_id" in t and "record_id" in t and "start_date" in t,
            Esi.get_raw_corp_history(character.id)
        ))
        history.reverse()
        current_corp = 0
        output = []
        for line in history:
            if current_corp != 0:
                transfer = Transfer.Transfer(
                    line["record_id"],
                    line["start_date"],
                    character.id,
                    int(current_corp),
                    int(line["corporation_id"])
                )
                output.append(transfer)
            current_corp = line["corporation_id"]
        return output

    @staticmethod
    def get_corp_transfers_skipping_npc(character):
        history = list(filter(
            lambda t: "corporation_id" in t and "record_id" in t and "start_date" in t,
            Esi.get_raw_corp_history(character.id)
        ))
        history.reverse()
        current_corp = 0
        output = []
        for line in history:
            if line["corporation_id"] > 2000000:
                if current_corp != 0:
                    transfer = Transfer.Transfer(
                        line["record_id"],
                        line["start_date"],
                        character.id,
                        int(current_corp),
                        int(line["corporation_id"])
                    )
                    output.append(transfer)
                current_corp = line["corporation_id"]
        return output
