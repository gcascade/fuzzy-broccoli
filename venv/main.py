from enum import Enum
import random
import time


class Indenter:
    def __init__(self):
        self.level = -1

    def __enter__(self):
        self.level += 1
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.level -= 1

    def print(self, text):
        print('\t' * self.level + text)

    def indent_text(self, text):
        return '\t' * self.level + text


class ManagedFile:
    def __init__(self, name, mode):
        self.name = name
        self.mode = mode

    def __enter__(self):
        self.file = open(self.name, self.mode)
        return self.file

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.file:
            self.file.close()


class Stats:

    def __init__(self, id, phy_str, mag_pow, phy_res, mag_res, max_hp, max_ap):
        self.id = id
        self.phy_str = phy_str
        self.mag_pow = mag_pow
        self.phy_res = phy_res
        self.mag_res = mag_res
        self.hp = max_hp
        self.max_hp = max_hp
        self.ap = max_ap
        self.max_ap = max_ap


class CharacterStats(Stats):

    unspent_points = 0

    def __str__(self):
        return ("Character stats: \n\t"
                "Physical Strength: {}\n\t"
                "Magic Power: {}\n\t"
                "Physical Resistance: {}\n\t"
                "Magic Resistance: {}\n\t"
                "Health Points: {}/{}\n\t"
                "Ability Points: {}/{}\n"
                .format(self.phy_str, self.mag_pow, self.phy_res, self.mag_res, self.hp, self.max_hp, self.ap,
                        self.max_ap))

    def display_stats(self, indent):
        indent.print("Character Stats:")
        with indent:
            indent.print("Physical Strength: {}".format(self.phy_str))
            indent.print("Magic Power: {}".format(self.mag_pow))
            indent.print("Physical Resistance: {}".format(self.phy_res))
            indent.print("Magic Resistance: {}".format(self.mag_res))
            indent.print("Health Points: {}/{}".format(self.hp, self.max_hp))
            indent.print("Ability Points: {}/{}".format(self.ap, self.max_ap))


class CharacterClass:
    class_name = "Classless"
    class_xp = 0
    phy_str_mult = 0
    mag_pow_mult = 0
    phy_res_mult = 0
    mag_res_mult = 0
    hp_mult = 0
    ap_mult = 0

    def __init__(self, id):
        self.id = id

    def __str__(self):
        return ("{}\n\t"
                "Physical Strength Multiplier: {}\n\t"
                "Magical Power Multiplier: {}\n\t"
                "Physical Resistance Multiplier: {}\n\t"
                "Magical Resistance Multiplier: {}\n\t"
                "Health Points Multiplier: {}\n\t"
                "Ability Points Multiplier: {}\n"
                .format(self.class_name, self.phy_str_mult, self.mag_pow_mult, self.phy_res_mult, self.mag_res_mult,
                        self.hp_mult, self.ap_mult))

    def displayXp(self):
        print(self.class_xp)

    def initClass(self, character_stats):
        character_stats.phy_str *= self.phy_str_mult
        character_stats.mag_pow *= self.mag_pow_mult
        character_stats.phy_res *= self.phy_res_mult
        character_stats.mag_res *= self.mag_res_mult
        character_stats.max_hp *= self.hp_mult
        character_stats.max_ap *= self.ap_mult
        character_stats.hp *= self.hp_mult
        character_stats.ap *= self.ap_mult

    def exitClass(self, character_stats):
        character_stats.phy_str /= self.phy_str_mult
        character_stats.mag_pow /= self.mag_pow_mult
        character_stats.phy_res /= self.phy_res_mult
        character_stats.mag_res /= self.mag_res_mult
        character_stats.hp /= self.hp_mult
        character_stats.max_hp /= self.hp_mult
        character_stats.ap /= self.ap_mult
        character_stats.max_ap /= self.ap_mult

    def displayClass(self, indent):
        indent.print(self.class_name)
        with indent:
            indent.print("Physical Strength Multiplier: {}".format(self.phy_str_mult))
            indent.print("Magic Power Multiplier: {}".format(self.mag_pow_mult))
            indent.print("Physical Resistance Multiplier: {}".format(self.phy_res_mult))
            indent.print("Magic Resistance Multiplier: {}".format(self.mag_res_mult))
            indent.print("Health Points Multiplier: {}".format(self.hp_mult))
            indent.print("Ability Points Multiplier: {}".format(self.ap_mult))


class Squire(CharacterClass):
    class_name = "Squire"
    phy_str_mult = .8
    mag_pow_mult = .8
    phy_res_mult = .8
    mag_res_mult = .8
    hp_mult = .8
    ap_mult = .8


class Knight(CharacterClass):
    class_name = "Knight"
    phy_str_mult = 1.2
    mag_pow_mult = .8
    phy_res_mult = 1.2
    mag_res_mult = .8
    hp_mult = 1.2
    ap_mult = 1


class Wizard(CharacterClass):
    class_name = "Wizard"
    phy_str_mult = .8
    mag_pow_mult = 1.2
    phy_res_mult = .8
    mag_res_mult = 1.2
    hp_mult = .8
    ap_mult = 1.3


class Rogue(CharacterClass):
    class_name = "Rogue"
    phy_str_mult = 1.1
    mag_pow_mult = 1
    phy_res_mult = 1
    mag_res_mult = .8
    hp_mult = 1.1
    ap_mult = 1.1


class Archer(CharacterClass):
    class_name = "Archer"
    phy_str_mult = 1.2
    mag_pow_mult = 1
    phy_res_mult = .8
    mag_res_mult = .8
    hp_mult = .9
    ap_mult = 1


class Monk(CharacterClass):
    class_name = "Monk"
    phy_str_mult = 1.3
    mag_pow_mult = 1.3
    phy_res_mult = 1.3
    mag_res_mult = 1.3
    hp_mult = 1.3
    ap_mult = 1


class HolyKnight(CharacterClass):
    class_name = "Holy Knight"
    phy_str_mult = 1.5
    mag_pow_mult = 1.2
    phy_res_mult = 1.5
    mag_res_mult = 1.2
    hp_mult = 1.1
    ap_mult = 1


class DarkKnight(CharacterClass):
    class_name = "Dark Knight"
    phy_str_mult = 1.5
    mag_pow_mult = 1.2
    phy_res_mult = 1.5
    mag_res_mult = 1.2
    hp_mult = 1.1
    ap_mult = 1


class Barbarian(CharacterClass):
    class_name = "Barbarian"
    phy_str_mult = 1.7
    mag_pow_mult = 0.5
    phy_res_mult = 0.7
    mag_res_mult = 0.7
    hp_mult = 1.6
    ap_mult = .9


class Scholar(CharacterClass):
    class_name = "Scholar"
    phy_str_mult = .8
    mag_pow_mult = 1.6
    phy_res_mult = .9
    mag_res_mult = 1.4
    hp_mult = 1
    ap_mult = 2


class Character:
    xp = 0
    level = 0

    def __init__(self, id, name, stats, character_class):
        self.id = id
        self.name = name
        self.stats = stats
        self.character_class = character_class
        self.experience_helper = ExperienceHelper()
        character_class.initClass(self.stats)

    def changeCharacterClass(self, new_class):
        self.character_class.exitClass(self.stats)
        self.character_class = new_class
        new_class.initClass(self.stats)

    def display_character(self):
        with Indenter() as indent:
            indent.print('Name: {}'.format(self.name))
            indent.print("Level: {}".format(self.level))
            indent.print(
                "Experience points: {}/{}".format(self.xp, self.experience_helper.get_xp_needed_for_next_level(self.level)))
            self.stats.display_stats(indent)
            self.character_class.displayClass(indent)


class Foe:
    # Probability in percentage
    probability = 100

    # XP gained when foe dies
    xp = 0

    def __init__(self, id, name, stats):
        self.id = id
        self.name = name
        self.stats = stats

    def displayFoe(self):
        with Indenter() as indent:
            indent.print('Name: {}'.format(self.name))
            self.stats.display_stats(indent)

    def clone(self):
        cloned_stats = FoeStats(self.id,
                                self.stats.phy_str,
                                self.stats.mag_pow,
                                self.stats.phy_res,
                                self.stats.mag_res,
                                self.stats.max_hp,
                                self.stats.max_ap)
        cloned_name = self.name
        foe = Foe(self.id, cloned_name, cloned_stats)
        foe.xp = self.xp
        foe.probability = self.probability
        return foe


class FoeStats(Stats):
    def __str__(self):
        return ("Foe stats: \n\t"
                "Physical Strength: {}\n\t"
                "Magic Power: {}\n\t"
                "Physical Resistance: {}\n\t"
                "Magic Resistance: {}\n\t"
                "Health Points: {}/{}\n\t"
                "Ability Points: {}/{}\n"
                .format(self.phy_str, self.mag_pow, self.phy_res, self.mag_res, self.hp, self.max_hp, self.ap,
                        self.max_ap))

    def display_stats(self, indent):
        indent.print("Foe Stats:")
        with indent:
            indent.print("Physical Strength: {}".format(self.phy_str))
            indent.print("Magic Power: {}".format(self.mag_pow))
            indent.print("Physical Resistance: {}".format(self.phy_res))
            indent.print("Magic Resistance: {}".format(self.mag_res))
            indent.print("Health Points: {}/{}".format(self.hp, self.max_hp))
            indent.print("Ability Points: {}/{}".format(self.ap, self.max_ap))


class DamageType(Enum):
    PHY_DMG = 1
    MAG_DMG = 2
    PURE_DMG = 3


class BattleEngine:

    def __init__(self, character_list, foe_list):
        self.character_list = character_list
        self.foe_list = foe_list

    def __enter__(self):
        print('Battle start.')
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        print('Battle end.')

    def attack(self, attacker, defender, attack_power, damage_type):
        if damage_type == DamageType.PHY_DMG:
            damage = attack_power * (attacker.stats.phy_str / defender.stats.phy_res)
        elif damage_type == DamageType.MAG_DMG:
            damage = attack_power * (attacker.stats.mag_pow / defender.stats.mag_res)
        else:
            damage = attack_power
        damage = round(damage)
        defender.stats.hp = defender.stats.hp - damage if defender.stats.hp - damage > 0 else 0
        with Indenter() as indent:
            with indent:
                indent.print('{} inflicted {} damage to {} ({}/{})'.format(attacker.name, damage, defender.name,
                                                                           defender.stats.hp, defender.stats.max_hp))
        self.check_if_foe_ko(defender, indent)

    def check_if_foe_ko(self, character, indent):
        if character.stats.hp == 0:
            indent.print('{} is KO !'.format(character.name))

    def checkIfBattleOver(self):
        return all(c.stats.hp == 0 for c in self.character_list) or all(f.stats.hp == 0 for f in self.foe_list)

    def handle_victory(self):
        if any(c.stats.hp > 0 for c in self.character_list):
            xp_value = sum(map(lambda f: f.xp, self.foe_list))
            xp_gained_per_character = xp_value / len(self.character_list)
            character_alive = list(filter(lambda c: c.stats.hp > 0, self.character_list))
            for c in character_alive:
                print("{} gained {} experience points.".format(c.name, xp_gained_per_character))
            xp_helper = ExperienceHelper()
            xp_helper.applyXp(xp_gained_per_character, character_alive)

    def handle_defeat(self):
        if all(c.stats.hp == 0 for c in self.character_list):
            print("Defeat")

    def fight(self):
        turn = 1
        while not self.checkIfBattleOver():
            if turn % 2 == 1:
                attacker = self.chooseFighter(self.character_list)
                defender = self.chooseFighter(self.foe_list)
                self.attack(attacker, defender, 10, DamageType.PHY_DMG)
            else:
                attacker = self.chooseFighter(self.foe_list)
                defender = self.chooseFighter(self.character_list)
                self.attack(attacker, defender, 10, DamageType.PHY_DMG)
            turn += 1
            time.sleep(0.25)
        self.handle_victory()
        self.handle_defeat()

    # Precondition : One of fighter_list is not dead.
    def chooseFighter(self, fighter_list):
        if all(f.stats.hp == 0 for f in fighter_list):
            return
        while "Fighter is dead":
            attacker = random.choice(fighter_list)
            if attacker.stats.hp != 0:
                return attacker


class Level:

    def __init__(self, id, level_number):
        self.id = id
        self.level_number = level_number

    def __enter__(self):
        print("Level {}. Start".format(self.level_number))
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        print("Level {}. End".format(self.level_number))

    # do not use
    def writeFile(self, foe_list):
        with ManagedFile('Level_{}.txt'.format(self.level_number), 'w') as f:
            f.write('Level_{}\n'.format(self.level_number))
            for foe in foe_list:
                f.write('{}\n{}\n{}\n{}\n{}\n{}\n{}\n'
                        .format(foe.name,
                                foe.stats.phy_str,
                                foe.stats.mag_pow,
                                foe.stats.phy_res,
                                foe.stats.mag_res,
                                foe.stats.max_hp,
                                foe.stats.max_ap))

    def loadCreaturesFromFile(self):
        foe_list = list()
        with ManagedFile('Levels\Level_{}.txt'.format(self.level_number), 'r') as f:
            line = f.readline()
            if line != 'Level_{}\n'.format(self.level_number):
                print('An error occured opening file.')
            else:
                foe_number = 1
                while line:
                    line = f.readline()
                    if line == '':
                        break
                    creature_name = line.strip()
                    line = f.readline()
                    creature_phy_str = float(line.strip())
                    line = f.readline()
                    creature_mag_pow = float(line.strip())
                    line = f.readline()
                    creature_phy_res = float(line.strip())
                    line = f.readline()
                    creature_mag_res = float(line.strip())
                    line = f.readline()
                    creature_max_hp = float(line.strip())
                    line = f.readline()
                    creature_max_ap = float(line.strip())
                    line = f.readline()
                    creature_probability = int(line.strip())
                    line = f.readline()
                    creature_xp = int(line.strip())
                    creature_stats = FoeStats(1, creature_phy_str, creature_mag_pow, creature_phy_res, creature_mag_res,
                                              creature_max_hp, creature_max_ap)
                    foe = Foe(foe_number, creature_name, creature_stats)
                    foe.probability = creature_probability
                    foe.xp = creature_xp
                    foe_number += 1
                    foe_list.append(foe)
        return foe_list

    def generate_foe(self, foe_number, foe_list):
        return_list = list()
        p = list()
        for f in foe_list:
            for i in range(0, f.probability):
                p.append(f.clone())
        for n in range(0, foe_number):
            foe = random.choice(p)
            if any(f.name.strip() == foe.name.strip() for f in return_list):
                # TO DO correct foe number
                foe.name += " {}".format(n + 1)
            return_list.append(foe)
        return return_list

    def progress(self, character_list):
        battle_number = 0
        while any(c.stats.hp > 0 for c in character_list):
            battle_number += 1
            print("Battle {}".format(battle_number))
            foe_number = random.randint(1, 4)
            generable_foe_list = self.loadCreaturesFromFile()
            foe_list = self.generate_foe(foe_number, generable_foe_list)
            # for n in range(0, foe_number):
            #     foe_stats = FoeStats(n, 5, 5, 5, 5, 100, 10)
            #     foe_name = "Goblin"
            #     if (n > 0):
            #         foe_name += " {}".format(n + 1)
            #     goblin = Foe(n, foe_name, foe_stats)
            #     foe_list.append(goblin)
            with Indenter() as indent:
                indent.print("Your party encounters:")
                with indent:
                    for foe in foe_list:
                        indent.print(foe.name)
            self.loadCreaturesFromFile()
            with BattleEngine(character_list, foe_list) as battle:
                battle.fight()
        print("Wedge and Biggs died at Battle {}".format(battle_number))


class ExperienceHelper:

    def __init__(self):
        self.xp_values = self.load_level_threshold()

    def applyXp(self, xp_gained, character_list):
        for c in character_list:
            c.xp += xp_gained
            current_level = c.level
            xp_needed_for_next_level = self.get_xp_needed_for_next_level(current_level)
            while c.xp >= xp_needed_for_next_level > 0:
                self.apply_level_up(c)
                current_level = c.level
                xp_needed_for_next_level = self.get_xp_needed_for_next_level(current_level)

    def apply_level_up(self, character):
        character.level = int(character.level + 1)
        character.stats.unspent_points += 10
        with Indenter() as indent:
            indent.print("Level up! {} is now level {}.".format(character.name, character.level))

    def load_level_threshold(self):
        with ManagedFile('Utilities\level_threshold.txt', 'r') as f:
            xp_values = f.readlines()
            return list(map(lambda x: x.strip(), xp_values))

    def get_xp_needed_for_next_level(self, current_level):
        if not self.xp_values[current_level + 1].isdigit() or not self.xp_values[-1].isdigit():
            return -1
        if len(self.xp_values) > current_level + 1:
            return int(self.xp_values[current_level + 1])
        else:
            return int(self.xp_values[-1])


class PartyManager:
    def __init__(self, party):
        self.party = party

    def heal_party(self):
        for c in self.party:
            c.stats.hp = c.stats.max_hp

    def view_party(self):
        for c in self.party:
            c.display_character()

    def select_party_member(self):
        with Indenter() as indent:
            pm_number = 0
            for pm in self.party:
                indent.print("{} the {} [{}]".format(pm.name, pm.character_class.class_name,pm_number))
                pm_number += 1
            while "A party member is not picked.":
                choice = input('Choose a party member.')
                if choice.isdigit() and 0 <= int(choice) < pm_number:
                    break
            party_member = self.party[int(choice)]
            return party_member

    def change_class(self):
        party_member = self.select_party_member()
        with Indenter() as indent:
            indent.print("{} the {}.".format(party_member.name, party_member.character_class.class_name))
        print('Not implemented yet.')

    def spend_stat_points(self):
        party_member = self.select_party_member()
        with Indenter() as indent:
            indent.print("{} the {}.".format(party_member.name, party_member.character_class.class_name))
            with indent:
                indent.print(str(party_member.stats))
                indent.print("Points to spend: {}".format(party_member.stats.unspent_points))
                indent.print("Not implemented yet.")


class Menu:

    def __init__(self, character_list):
        self.character_list = character_list
        self.party_manager = PartyManager(character_list)

    def start_level(self, level_number):
        with Level(1, level_number) as level:
            level.progress(self.character_list)

    def ask_level(self):
        while "Input is wrong":
            level_number = input("Enter level(1-2):")
            if level_number.isdigit() and int(level_number) <= 2:
                break
        return level_number

    def manage_party(self, indent):
        indent.print("Party Manager.")
        with indent:
            prompt_text = indent.indent_text("Press v to view your party.\n")
            prompt_text += indent.indent_text("Press c to change the class of a party member.\n")
            prompt_text += indent.indent_text("Press l to spend stat points on a party member.\n")
            prompt_text += indent.indent_text("Press a to equip abilities and talents.\n")
            choice = ''
            choice_accepted = list({'V', 'C', 'L', 'A'})
            while choice not in choice_accepted:
                choice = input(prompt_text).strip().upper()
            if choice == 'V':
                self.party_manager.view_party()
            elif choice == 'C':
                self.party_manager.change_class()
            elif choice == 'L':
                self.party_manager.spend_stat_points()
            elif choice == 'A':
                print("Not implemented yet.")

    def quit_game(self):
        exit()

    def display_menu(self):
        with Indenter() as indent:
            indent.print("Main menu.")
            with indent:
                prompt_text = indent.indent_text("Press p to start playing.\n")
                prompt_text += indent.indent_text("Press m to manage your party.\n")
                prompt_text += indent.indent_text("Press h to heal your party.\n")
                prompt_text += indent.indent_text('Press q to quit.\n')
                choice = ''
                choice_accepted = list({'P', 'M', 'H', 'Q'})
                while choice not in choice_accepted:
                    choice = input(prompt_text).strip().upper()
                if choice == 'P':
                    self.start_level(self.ask_level())
                elif choice == 'M':
                    self.manage_party(indent)
                elif choice == 'H':
                    self.party_manager.heal_party()
                    indent.print("*Healing sound*")
                    indent.print("Your party is healed.")
                elif choice == 'Q':
                    self.quit_game()


# -------------------------- main function -------------------------- #
biggs_id = 1
wedge_id = 2
goblin_id = 3
biggs_stat = CharacterStats(biggs_id, 20, 20, 20, 20, 1000, 50)
wedge_stat = CharacterStats(wedge_id, 20, 20, 20, 20, 1000, 50)
scholar = Scholar(biggs_id)
holyknight = HolyKnight(wedge_id)
biggs = Character(biggs_id, "Biggs", biggs_stat, scholar)
biggs.display_character()
wedge = Character(wedge_id, "Wedge", wedge_stat, holyknight)
wedge.display_character()
my_party = list()
my_party.append(biggs)
my_party.append(wedge)

menu = Menu(my_party)
while "User has not quit":
    menu.display_menu()

