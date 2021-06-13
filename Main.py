import Character
import DB
import Esi
import Evewho
import Transfer
import Graphing

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
                 "Mouth Trumpet Cavalry.",
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


def main():
    # Transfer.Transfer.populate_db_from_evewho_skipping_npc()
    db = DB.DB.connect()
    for corp_name in corps:
        print(corp_name)
        Graphing.graph_corp_member_velocity(db, corp_name)


main()
