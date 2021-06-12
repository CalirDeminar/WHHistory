import DB
import Esi
import Character
import Evewho
from multiprocessing import Pool


class Transfer:
    id = ""
    date = ""
    character = -1
    source = -1
    destination = -1

    def __init__(self, transfer_id, date, character, source, destination):
        self.id = transfer_id
        self.date = date
        self.character = character
        self.source = source
        self.destination = destination

    @staticmethod
    def get_all_transfer_ids(db):
        return map(lambda t: t[0], db.execute("SELECT id FROM transfers").fetchall())

    @staticmethod
    def insert_transfers(db, transfers):
        existing_ids = Transfer.get_all_transfer_ids(db)
        for transfer in transfers:
            if transfer.id not in existing_ids:
                db.execute(
                    "INSERT INTO transfers VALUES(?, ?, ?, ?, ?);",
                    (transfer.id, transfer.date, transfer.character, transfer.source, transfer.destination)
                )
        db.commit()

    @staticmethod
    def populate_db_from_evewho():
        db = DB.DB.connect()
        DB.DB.set_up_tables(db)
        character_names = Evewho.EveWhoParser.get_full_character_list()
        print(len(character_names))
        character_list = Character.Character.get_characters_from_names(character_names)
        print("Character List Gotten")
        Character.Character.insert_characters(db, character_list)
        i = 0
        for character in character_list:
            i += 1
            try:
                transfers = Character.Character.get_corp_transfers(character)
                print(str(i) + " of " + str(len(character_list)))
                Transfer.insert_transfers(db, transfers)
            except:
                print("Crash")

    @staticmethod
    def populate_db_from_evewho_skipping_npc():
        db = DB.DB.connect()
        DB.DB.set_up_tables(db)
        character_names = Evewho.EveWhoParser.get_full_character_list()
        print(len(character_names))
        character_list = Character.Character.get_characters_from_names(character_names)
        print("Character List Gotten")
        Character.Character.insert_characters(db, character_list)
        i = 0
        for character in character_list:
            i += 1
            try:
                transfers = Character.Character.get_corp_transfers_skipping_npc(character)
                print(str(i) + " of " + str(len(character_list)))
                Transfer.insert_transfers(db, transfers)
            except:
                print("Crash")
