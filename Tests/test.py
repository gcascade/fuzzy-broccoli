import main.py

biggs_id = 1
wedge_id = 2
goblin_id = 3
biggs_stat = CharacterStats(biggs_id, 10, 10, 10, 10, 500,50)
wedge_stat = CharacterStats(wedge_id, 10, 10, 10, 10, 500,50)
squire = Wizard(biggs_id)
knight = Knight(wedge_id)
biggs = Character(biggs_id, "Biggs", biggs_stat, squire)
biggs.changeCharacterClass(knight)
biggs.displayCharacter()
wedge = Character(wedge_id, "Wedge", wedge_stat, squire)
wedge.displayCharacter()
character_list = list()
character_list.append(biggs)
character_list.append(wedge)
with Level(1) as level:
    level.progress(character_list)

# turn = 0
# while(any(c.stats.hp > 0 for c in character_list)):
#     turn += 1
#     print("Battle {}".format(turn))
#     foe_list = list()
#     foe_number = random.randint(1,4)
#     for n in range(0, foe_number):
#         foe_stats = FoeStats(n, 5, 5, 5, 5, 100, 10)
#         foe_name = "Goblin"
#         if(n > 0):
#             foe_name +=" {}".format(n+1)
#         goblin = Foe(n, foe_name, foe_stats)
#         foe_list.append(goblin)
#     with Indenter() as indent:
#         indent.print("Your party encounters:")
#         with indent:
#             for foe in foe_list:
#                 indent.print(foe.name)
#     with BattleEngine(character_list, foe_list) as battle:
#         battle.fight()
# print("Wedge and Biggs died at Battle {}".format(turn))