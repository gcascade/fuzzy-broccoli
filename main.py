from enum import Enum
from abc import ABCMeta
import random
import time
import copy

max_level = 3
combat_text_speed = .25 # in seconds

# For debug only
def trace(func):
    def wrapper(*args, **kwargs):
        print(f'TRACE: calling {func.__name__}() ' f'with {args}, {kwargs}')
        original_result = func(*args, **kwargs)
        print(f'TRACE: {func.__name__}() ' f'returned {original_result!r}')
        return original_result
    return wrapper


class Indenter:
    def __init__(self):
        self.level = -1

    def __enter__(self):
        self.level += 1
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.level -= 1

    def print_(self, text):
        new_text = text.splitlines()
        for line in new_text:
            print('\t' * self.level + line)

    def indent_text(self, text):
        new_text = text.splitlines()
        ret = ''
        for line in new_text:
            ret += '\t' * self.level + line + "\n"
        return ret


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


class FileContentException(Exception):
    pass


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
        indent.print_("Character Stats:")
        with indent:
            indent.print_("Physical Strength: {}".format(self.phy_str))
            indent.print_("Magic Power: {}".format(self.mag_pow))
            indent.print_("Physical Resistance: {}".format(self.phy_res))
            indent.print_("Magic Resistance: {}".format(self.mag_res))
            indent.print_("Health Points: {}/{}".format(self.hp, self.max_hp))
            indent.print_("Ability Points: {}/{}".format(self.ap, self.max_ap))

    def add_stats_points(self, phy_str, mag_pow, phy_res, mag_res, max_hp, max_ap):
        """Add stats points"""
        self.phy_str += phy_str
        self.mag_pow += mag_pow
        self.phy_res += phy_res
        self.mag_res += mag_res
        self.hp += round(max_hp * (self.hp / self.max_hp))
        self.max_hp += max_hp
        if self.hp > self.max_hp:
            self.hp = self.max_hp
        self.ap += round(max_ap * (self.ap / self.max_ap))
        self.max_ap += max_ap
        if self.ap > self.max_ap:
            self.ap = self.max_ap

    def spend_points(self, points):
        """Remove the spent points from the character's points pool."""
        if points > self.unspent_points:
            self.unspent_points = 0
        else:
            self.unspent_points -= points


class CharacterClass(metaclass=ABCMeta):
    class_name = "Classless"
    class_xp = 0
    class_level = 0
    phy_str_mult = 0
    mag_pow_mult = 0
    phy_res_mult = 0
    mag_res_mult = 0
    hp_mult = 0
    ap_mult = 0
    ability_list = list()

    def __init__(self):
        self.experience_helper = ExperienceHelper()
        try:
            self.ability_list = self.get_class_abilities_from_file()
        except FileContentException:
            print("An error occurred loading abilities, please check the content of the Abilities directory.")

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

    def display_xp(self):
        print(self.class_xp)

    def init_class(self, character_stats):
        character_stats.phy_str *= self.phy_str_mult
        character_stats.mag_pow *= self.mag_pow_mult
        character_stats.phy_res *= self.phy_res_mult
        character_stats.mag_res *= self.mag_res_mult
        character_stats.max_hp *= self.hp_mult
        character_stats.max_ap *= self.ap_mult
        character_stats.hp *= self.hp_mult
        character_stats.ap *= self.ap_mult

    def exit_class(self, character_stats):
        character_stats.phy_str /= self.phy_str_mult
        character_stats.mag_pow /= self.mag_pow_mult
        character_stats.phy_res /= self.phy_res_mult
        character_stats.mag_res /= self.mag_res_mult
        character_stats.hp /= self.hp_mult
        character_stats.max_hp /= self.hp_mult
        character_stats.ap /= self.ap_mult
        character_stats.max_ap /= self.ap_mult

    def display_class(self, indent):
        indent.print_("Class: {}".format(self.class_name))
        with indent:
            indent.print_("Level: {}".format(self.class_level))
            indent.print_(
                "Class Experience points: {}/{}".format(self.class_xp, self.experience_helper.get_xp_needed_for_next_level(self.class_level)))
            indent.print_("Physical Strength Multiplier: {}".format(self.phy_str_mult))
            indent.print_("Magic Power Multiplier: {}".format(self.mag_pow_mult))
            indent.print_("Physical Resistance Multiplier: {}".format(self.phy_res_mult))
            indent.print_("Magic Resistance Multiplier: {}".format(self.mag_res_mult))
            indent.print_("Health Points Multiplier: {}".format(self.hp_mult))
            indent.print_("Ability Points Multiplier: {}".format(self.ap_mult))

    def get_class_abilities_from_file(self):
        filename = f"Abilities/{self.class_name}.txt"
        return_list = list()
        with ManagedFile(filename,'r') as file:
            class_name = file.readline().strip()
            if class_name != self.class_name:
                raise FileContentException
            else:
                while "All abilities not loaded.":
                    # 1 - Ability Name
                    ability_name = file.readline().strip()
                    if ability_name == '':
                        break
                    # 2 - Ability Damage
                    ability_damage = file.readline().strip()
                    if not ability_damage.isdigit():
                        raise FileContentException
                    else:
                        ability_damage = int(ability_damage)
                    # 3 - Ability Damage Type
                    ability_damage_type = file.readline().strip()
                    if (not ability_damage_type.isdigit()) and (not 0 <= int(ability_damage_type) < 3):
                        raise FileContentException
                    else:
                        ability_damage_type = DamageType(int(ability_damage_type))
                    # 4 - Ability Description
                    ability_description = file.readline().strip()
                    # 5 - Ability AP Cost
                    ability_ap_cost = file.readline().strip()
                    if not ability_ap_cost.isdigit():
                        raise FileContentException
                    else:
                        ability_ap_cost = int(ability_ap_cost)
                    # 6 - Ability Is Default Ability ?
                    ability_is_default = file.readline().strip()
                    if not ability_is_default.isdigit():
                        raise FileContentException
                    else:
                        ability_is_default = bool(int(ability_is_default))
                    # 7 - Ability Level Acquired
                    ability_level_acquired = file.readline().strip()
                    if not ability_level_acquired.isdigit():
                        raise FileContentException
                    else:
                        ability_level_acquired = int(ability_level_acquired)
                    # 8 - Ability CP Cost
                    ability_cp_cost = file.readline().strip()
                    if not ability_cp_cost.isdigit():
                        raise FileContentException
                    ability_cp_cost = int(ability_cp_cost)
                    ability = Ability(ability_name, ability_damage, ability_damage_type, ability_description, ability_ap_cost, ability_is_default, ability_level_acquired, ability_cp_cost)
                    return_list.append(ability)
        return return_list

    @staticmethod
    def get_dict_of_class():
        class_dictionary = {
            Squire.class_name: Squire(),
            Knight.class_name: Knight(),
            Wizard.class_name: Wizard(),
            Rogue.class_name: Rogue(),
            Archer.class_name: Archer(),
            Monk.class_name: Monk(),
            Cleric.class_name: Cleric(),
            Necromancer.class_name: Necromancer(),
            HolyKnight.class_name: HolyKnight(),
            DarkKnight.class_name: DarkKnight(),
            Barbarian.class_name: Barbarian(),
            Scholar.class_name: Scholar(),
            Ninja.class_name: Ninja(),
            Beastmaster.class_name: Beastmaster(),
        }
        return class_dictionary


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


class Cleric(CharacterClass):
    class_name = "Cleric"
    phy_str_mult = .8
    mag_pow_mult = 1.2
    phy_res_mult = .8
    mag_res_mult = 1
    hp_mult = .9
    ap_mult = 1.2


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


class Ninja(CharacterClass):
    class_name = "Ninja"
    phy_str_mult = 1.4
    mag_pow_mult = 1.4
    phy_res_mult = 1
    mag_res_mult = 1.4
    hp_mult = 1
    ap_mult = 1.2


class Beastmaster(CharacterClass):
    class_name = "Beastmaster"
    phy_str_mult = 1.5
    mag_pow_mult = 1
    phy_res_mult = 1.5
    mag_res_mult = 1.5
    hp_mult = 2
    ap_mult = 1


class Necromancer(CharacterClass):
    class_name = "Necromancer"
    phy_str_mult = 1.4
    mag_pow_mult = 1.4
    phy_res_mult = 1
    mag_res_mult = 1.4
    hp_mult = 1
    ap_mult = 1.2

# class ClassBehavior():
#
# class SquireBehavior(ClassBehavior):


class Ability:
    def __init__(self, ability_name, ability_dmg, ability_dmg_type, ability_description, ap_cost, is_default, level_acquired, cp_cost):
        self.ability_name = ability_name
        self.ability_dmg = ability_dmg
        self.ability_dmg_type = ability_dmg_type
        self.ability_description = ability_description
        self.ap_cost = ap_cost
        self.ability_acquired = is_default
        self.level_acquired = level_acquired
        self.cp_cost = cp_cost

    @staticmethod
    def default_ability():
        return Ability("Normal Attack", 10, DamageType.PHY_DMG, "A normal attack", 0, 0, 0, 0)

    def __str__(self):
        acquired_text = {
            True: "Yes",
            False : "No",
        }
        damage_type_text = {
            DamageType.PHY_DMG: 'Physical Damage',
            DamageType.MAG_DMG: 'Magic Damage',
            DamageType.PURE_DMG: 'Pure Damage',
        }
        with Indenter() as indent:
            ret = indent.indent_text("Name: {}\n".format(self.ability_name))
            with indent:
                ret += indent.indent_text("Damage: {}\n".format(self.ability_dmg))
                ret += indent.indent_text("Damage Type: {}\n".format(damage_type_text[self.ability_dmg_type]))
                ret += indent.indent_text("Description: {}\n".format(self.ability_description))
                ret += indent.indent_text("AP Cost: {} AP\n".format(self.ap_cost))
                ret += indent.indent_text("Acquired: {}\n".format(acquired_text[self.ability_acquired]))
                if not self.ability_acquired:
                    ret += indent.indent_text("Available at : {}".format(self.level_acquired))
                    ret += indent.indent_text("CP Cost: {}".format(self.cp_cost))
        return ret


class Passive:
    def __init__(self, passive_type, passive_name, passive_description):
        self.passive_type = passive_type
        self.passive_name = passive_name
        self.passive_description = passive_description


class Character:
    xp = 0
    level = 0
    class_points = 0

    def __init__(self, id, name, stats, character_class):
        self.id = id
        self.name = name
        self.stats = stats
        self.class_dict = CharacterClass.get_dict_of_class()
        self.character_class = self.class_dict.get(character_class.class_name)
        self.experience_helper = ExperienceHelper()
        self.character_class.init_class(self.stats)

    def change_character_class(self, new_class):
        self.character_class.exit_class(self.stats)
        self.class_dict[self.character_class.class_name] = copy.deepcopy(self.character_class)
        self.character_class = self.class_dict.get(new_class.class_name)
        new_class.init_class(self.stats)

    def display_character(self):
        with Indenter() as indent:
            indent.print_('Name: {}'.format(self.name))
            indent.print_("Level: {}".format(self.level))
            indent.print_(
                "Experience points: {}/{}".format(self.xp, self.experience_helper.get_xp_needed_for_next_level(self.level)))
            indent.print_("CP: {}".format(self.class_points))
            self.stats.display_stats(indent)
            self.character_class.display_class(indent)

    def add_stats_points(self, phy_str, mag_pow, phy_res, mag_res, max_hp, max_ap):
        self.character_class.exit_class(self.stats)
        self.stats.add_stats_points(phy_str, mag_pow, phy_res, mag_res, max_hp, max_ap)
        self.character_class.init_class(self.stats)

    def spend_ap(self, ap):
        self.stats.ap -= ap


class Foe:
    # Probability in percentage
    probability = 100

    # XP gained when foe dies
    xp = 0

    def __init__(self, id, name, stats):
        self.id = id
        self.name = name
        self.stats = stats

    def display_foe(self):
        with Indenter() as indent:
            indent.print_('Name: {}'.format(self.name))
            self.stats.display_stats(indent)

    def clone(self):
        return copy.deepcopy(self)

    def spend_ap(self, ap):
        self.stats.ap -= ap


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
        indent.print_("Foe Stats:")
        with indent:
            indent.print_("Physical Strength: {}".format(self.phy_str))
            indent.print_("Magic Power: {}".format(self.mag_pow))
            indent.print_("Physical Resistance: {}".format(self.phy_res))
            indent.print_("Magic Resistance: {}".format(self.mag_res))
            indent.print_("Health Points: {}/{}".format(self.hp, self.max_hp))
            indent.print_("Ability Points: {}/{}".format(self.ap, self.max_ap))


class DamageType(Enum):
    PHY_DMG = 0
    MAG_DMG = 1
    PURE_DMG = 2


class AbilityTarget(Enum):
    SINGLE = 0
    AOE = 1


class BattleEngine:

    def __init__(self, character_list, foe_list):
        self.character_list = character_list
        self.foe_list = foe_list

    def __enter__(self):
        print('Battle start.')
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        print('Battle end.')

    def attack(self, attacker, defender, ability):
        attack_power = ability.ability_dmg
        damage_type = ability.ability_dmg_type
        if damage_type == DamageType.PHY_DMG:
            damage = attack_power * (attacker.stats.phy_str / defender.stats.phy_res)
        elif damage_type == DamageType.MAG_DMG:
            damage = attack_power * (attacker.stats.mag_pow / defender.stats.mag_res)
        else:
            damage = attack_power
        damage = round(damage)
        attacker.spend_ap(ability.ap_cost)
        defender.stats.hp = defender.stats.hp - damage if defender.stats.hp - damage > 0 else 0
        with Indenter() as indent:
            with indent:
                indent.print_(f'{ability.ability_name}! {attacker.name} ({round(attacker.stats.ap)}/{round(attacker.stats.max_ap)}AP) inflicted {damage}'
                              f' damage to {defender.name} ({round(defender.stats.hp)}/{round(defender.stats.max_hp)}HP)')
        self.check_if_foe_ko(defender, indent)

    def choose_ability(self, attacker):
        """Choose an ability for the attacker. Return a default ability if the attacker is a Foe or if no abilities are found."""
        if isinstance(attacker, Foe):
            return Ability.default_ability()
        else:
            ability_learnt_and_available = list(filter(lambda a : a.ability_acquired and a.ap_cost <= attacker.stats.ap, attacker.character_class.ability_list))
            if not ability_learnt_and_available:
                return Ability.default_ability()
            else:
                ability = random.choice(ability_learnt_and_available)
                return ability

    # Precondition : One of fighter_list is not dead.
    def choose_fighter(self, fighter_list):
        if all(f.stats.hp == 0 for f in fighter_list):
            return
        while "Fighter is dead":
            attacker = random.choice(fighter_list)
            if attacker.stats.hp != 0:
                return attacker


    def check_if_foe_ko(self, character, indent):
        if character.stats.hp == 0:
            indent.print_('{} is KO !'.format(character.name))

    def check_if_battle_over(self):
        return all(c.stats.hp == 0 for c in self.character_list) or all(f.stats.hp == 0 for f in self.foe_list)

    def handle_victory(self):
        if any(c.stats.hp > 0 for c in self.character_list):
            xp_value = sum(map(lambda f: f.xp, self.foe_list))
            xp_gained_per_character = xp_value / len(self.character_list)
            character_alive = list(filter(lambda c: c.stats.hp > 0, self.character_list))
            for c in character_alive:
                print("{} gained {} experience points.".format(c.name, xp_gained_per_character))
            xp_helper = ExperienceHelper()
            xp_helper.apply_xp(xp_gained_per_character, character_alive)
            xp_helper.apply_class_xp(xp_gained_per_character, character_alive)

    def handle_defeat(self):
        if all(c.stats.hp == 0 for c in self.character_list):
            print("Defeat")

    def refresh_ap(self):
        for c in self.character_list:
            c.stats.ap = c.stats.max_ap

    def fight(self):
        turn = 1
        while not self.check_if_battle_over():
            if turn % 2 == 1:
                attacker = self.choose_fighter(self.character_list)
                defender = self.choose_fighter(self.foe_list)
                ability = self.choose_ability(attacker)
                self.attack(attacker, defender, ability)
            else:
                attacker = self.choose_fighter(self.foe_list)
                defender = self.choose_fighter(self.character_list)
                ability = self.choose_ability(attacker)
                self.attack(attacker, defender, ability)
            turn += 1
            time.sleep(combat_text_speed)
        self.handle_victory()
        self.handle_defeat()
        self.refresh_ap()


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
    def write_file(self, foe_list):
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

    # File Format :
    # Foe_Name
    # Physical Strength
    # Magic Power
    # Physical Resistance
    # Magic Resistance
    # Max HP
    # Max AP
    # Probability
    # XP awarded
    def load_creatures_from_file(self):
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
            for _ in range(0, f.probability):
                p.append(f.clone())
        for n in range(0, foe_number):
            foe = random.choice(p)
            if any(f.name.strip() == foe.name.strip() for f in return_list):
                # TODO  correct foe number
                foe.name += " {}".format(n + 1)
            return_list.append(foe)
        return return_list

    def progress(self, character_list):
        battle_number = 0
        while any(c.stats.hp > 0 for c in character_list):
            battle_number += 1
            print("Battle {}".format(battle_number))
            foe_number = random.randint(1, 4)
            generable_foe_list = self.load_creatures_from_file()
            foe_list = self.generate_foe(foe_number, generable_foe_list)
            # for n in range(0, foe_number):
            #     foe_stats = FoeStats(n, 5, 5, 5, 5, 100, 10)
            #     foe_name = "Goblin"
            #     if (n > 0):
            #         foe_name += " {}".format(n + 1)
            #     goblin = Foe(n, foe_name, foe_stats)
            #     foe_list.append(goblin)
            with Indenter() as indent:
                indent.print_("Your party encounters:")
                with indent:
                    for foe in foe_list:
                        indent.print_(foe.name)
            with BattleEngine(character_list, foe_list) as battle:
                battle.fight()
        print("Your party died at Battle {}".format(battle_number))


class ExperienceHelper:

    def __init__(self):
        self.xp_values = self.load_level_threshold()

    def apply_xp(self, xp_gained, character_list):
        """Add xp to the whole party. Level up a party member if necessary."""
        for c in character_list:
            c.xp += xp_gained
            current_level = c.level
            xp_needed_for_next_level = self.get_xp_needed_for_next_level(current_level)
            while c.xp >= xp_needed_for_next_level > 0:
                self.apply_level_up(c)
                current_level = c.level
                xp_needed_for_next_level = self.get_xp_needed_for_next_level(current_level)

    def apply_class_xp(self, xp_gained, character_list):
        """Add class xp to the whole party. Level up a class if necessary."""
        for c in character_list:
            c.character_class.class_xp += round(xp_gained)
            class_current_level = c.character_class.class_level
            c.class_points += round(xp_gained/10) #TODO Better system.
            xp_needed_for_next_class_level = self.get_xp_needed_for_next_level(class_current_level)
            while c.character_class.class_xp >= xp_needed_for_next_class_level > 0:
                self.apply_class_level_up(c)
                class_current_level = c.character_class.class_level
                xp_needed_for_next_class_level = self.get_xp_needed_for_next_level(class_current_level)

    def apply_level_up(self, character):
        """Add a level and stat points to the selected character."""
        character.level = int(character.level + 1)
        character.stats.unspent_points += 10
        with Indenter() as indent:
            indent.print_("Level up! {} is now level {}.".format(character.name, character.level))

    def apply_class_level_up(self, character):
        """Add a level to the character class."""
        character.character_class.class_level += 1
        with Indenter() as indent:
            indent.print_(f"Level up! {character.name} is now a level {character.character_class.class_level} {character.character_class.class_name}.")

    def load_level_threshold(self):
        """Load the xp needed for a level up from the file Utilities\level_threshold.txt"""
        with ManagedFile('Utilities\level_threshold.txt', 'r') as f:
            xp_values = f.readlines()
            return list(map(lambda x: x.strip(), xp_values))

    def get_xp_needed_for_next_level(self, current_level):
        """Return the xp needed to reach the next level (current_level + 1)"""
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
        """Set the current hp of each party member to its maximum."""
        for c in self.party:
            c.stats.hp = c.stats.max_hp
            c.stats.ap = c.stats.max_ap

    def view_party(self):
        """Display each member of the party."""
        for c in self.party:
            c.display_character()

    def select_party_member(self):
        """Ask the user to select a party member and returns it."""
        with Indenter() as indent:
            pm_number = 0
            for pm in self.party:
                indent.print_("{} the {} [{}]".format(pm.name, pm.character_class.class_name, pm_number))
                pm_number += 1
            while "A party member is not picked.":
                choice = input('Choose a party member.')
                if choice.isdigit() and 0 <= int(choice) < pm_number:
                    break
            party_member = self.party[int(choice)]
            return party_member

    def change_class(self):
        """Change the class of a party member."""
        party_member = self.select_party_member()
        with Indenter() as indent:
            indent.print_("{} the {}.".format(party_member.name, party_member.character_class.class_name))
            i = 0
            class_available = dict()
            indent.print_("Available classes:")
            for k, v in party_member.class_dict.items():
                print(f"{k},".ljust(20) + f"level {v.class_level}".ljust(30) + f"[{i}]")
                class_available[i] = k
                i += 1
            choice_accepted = range(i + 1)
            choice = ''
            while not choice.isdigit() or int(choice) not in choice_accepted:
                choice = input("Choose class [0-{}]".format(i - 1))
            key_chosen = class_available[int(choice)]
            class_chosen = party_member.class_dict[key_chosen]
            party_member.change_character_class(class_chosen)
            indent.print_("{}'s class was changed.".format(party_member.name))


    def change_name(self):
        """"Choose a party member. Change it's name."""
        party_member = self.select_party_member()
        with Indenter() as indent:
            indent.print_("{} the {}.".format(party_member.name, party_member.character_class.class_name))
            new_name_confirmed = False
            while not new_name_confirmed:
                new_name = input(indent.indent_text("What shall be {} new name ?".format(party_member.name))).strip()
                confirmation = input("Do you confirm {} as {}'s new name ?"
                                     "(Press Y or N or press Q to stop changing name)"
                                     .format(new_name, party_member.name)).strip().upper()
                if confirmation == 'Y':
                    new_name_confirmed = True
                if confirmation == 'Q':
                    indent.print_("You have not changed {}'s name".format(party_member.name))
                    return
            party_member.name = new_name

    def spend_stat_points(self):
        """Select a party member. Choose the points to spend on which attributes if there are any."""
        party_member = self.select_party_member()
        with Indenter() as indent:
            indent.print_("{} the {}.".format(party_member.name, party_member.character_class.class_name))
            if party_member.stats.unspent_points == 0:
                indent.print_("No points to spend.")
                return
            else:
                with indent:
                    indent.print_(str(party_member.stats))
                    indent.print_("Points to spend: {}".format(party_member.stats.unspent_points))
                    points_spent = False
                    while not points_spent:
                        points_to_spend = party_member.stats.unspent_points

                        # Phy_str
                        input_phy_str = indent.indent_text("Physical Strength:\n")
                        with indent:
                            input_phy_str += indent.indent_text("Current: {}\n".format(party_member.stats.phy_str))
                            input_phy_str += indent.indent_text("Points available: {}\n".format(points_to_spend))
                            phy_str_points = -1
                            while not -1 < int(phy_str_points) < points_to_spend + 1:
                                phy_str_points = input(input_phy_str).strip()
                                if phy_str_points == '':
                                    phy_str_points = 0
                                elif not phy_str_points.isdigit():
                                    phy_str_points = -1
                                    indent.print_("Enter a valid integer.")
                                elif phy_str_points.isdigit() and int(phy_str_points) > points_to_spend:
                                    indent.print_("Enter a valid integer.")
                        phy_str_points = int(phy_str_points)
                        points_to_spend -= phy_str_points

                        # Mag_pow
                        input_mag_pow = indent.indent_text("Magic Power:\n")
                        with indent:
                            input_mag_pow += indent.indent_text("Current: {}\n".format(party_member.stats.mag_pow))
                            input_mag_pow += indent.indent_text("Points available: {}\n".format(points_to_spend))
                            mag_pow_points = -1
                            while not -1 < int(mag_pow_points) < points_to_spend + 1:
                                mag_pow_points = input(input_mag_pow).strip()
                                if mag_pow_points == '':
                                    mag_pow_points = 0
                                elif not mag_pow_points.isdigit():
                                    mag_pow_points = -1
                                    indent.print_("Enter a valid integer.")
                                elif mag_pow_points.isdigit() and int(mag_pow_points) > points_to_spend:
                                    indent.print_("Enter a valid integer.")
                        mag_pow_points = int(mag_pow_points)
                        points_to_spend -= mag_pow_points

                        # Phy_res
                        input_phy_res = indent.indent_text("Physical Resistance:\n")
                        with indent:
                            input_phy_res += indent.indent_text("Current: {}\n".format(party_member.stats.phy_res))
                            input_phy_res += indent.indent_text("Points available: {}\n".format(points_to_spend))
                            phy_res_points = -1
                            while not -1 < int(phy_res_points) < points_to_spend + 1:
                                phy_res_points = input(input_phy_res).strip()
                                if phy_res_points == '':
                                    phy_res_points = 0
                                elif not phy_res_points.isdigit():
                                    phy_res_points = -1
                                    indent.print_("Enter a valid integer.")
                                elif phy_res_points.isdigit() and int(phy_res_points) > points_to_spend:
                                    indent.print_("Enter a valid integer.")
                        phy_res_points = int(phy_res_points)
                        points_to_spend -= phy_res_points

                        # Mag_res
                        input_mag_res = indent.indent_text("Magic Resistance:\n")
                        with indent:
                            input_mag_res += indent.indent_text("Current: {}\n".format(party_member.stats.mag_res))
                            input_mag_res += indent.indent_text("Points available: {}\n".format(points_to_spend))
                            mag_res_points = -1
                            while not -1 < int(mag_res_points) < points_to_spend + 1:
                                mag_res_points = input(input_mag_res).strip()
                                if mag_res_points == '':
                                    mag_res_points = 0
                                elif not mag_res_points.isdigit():
                                    mag_res_points = -1
                                    indent.print_("Enter a valid integer.")
                                elif mag_res_points.isdigit() and int(mag_res_points) > points_to_spend:
                                    indent.print_("Enter a valid integer.")
                        mag_res_points = int(mag_res_points)
                        points_to_spend -= mag_res_points

                        # HP (1 point = 10 HP)
                        input_max_hp = indent.indent_text("Health Points:\n")
                        with indent:
                            input_max_hp += indent.indent_text("Current: {}\n".format(party_member.stats.max_hp))
                            input_max_hp += indent.indent_text("Points available(1 point = 10 HP): {}\n".format(points_to_spend))
                            max_hp_points = -1
                            while not -1 < int(max_hp_points) < points_to_spend + 1:
                                max_hp_points = input(input_max_hp).strip()
                                if max_hp_points == '':
                                    max_hp_points = 0
                                elif not max_hp_points.isdigit():
                                    max_hp_points = -1
                                    indent.print_("Enter a valid integer.")
                                elif max_hp_points.isdigit() and int(max_hp_points) > points_to_spend:
                                    indent.print_("Enter a valid integer.")
                        max_hp_points = int(max_hp_points)
                        points_to_spend -= max_hp_points
                        max_hp_points *= 10

                        # AP
                        input_max_ap = indent.indent_text("Ability Points:\n")
                        with indent:
                            input_max_ap += indent.indent_text("Current: {}\n".format(party_member.stats.max_ap))
                            input_max_ap += indent.indent_text("Points available: {}\n".format(points_to_spend))
                            max_ap_points = -1
                            while not -1 < int(max_ap_points) < points_to_spend + 1:
                                max_ap_points = input(input_max_ap).strip()
                                if max_ap_points == '':
                                    max_ap_points = 0
                                elif not max_ap_points.isdigit():
                                    max_ap_points = -1
                                    indent.print_("Enter a valid integer.")
                                elif max_ap_points.isdigit() and int(max_ap_points) > points_to_spend:
                                    indent.print_("Enter a valid integer.")
                        max_ap_points = int(max_ap_points)
                        points_to_spend -= max_ap_points

                        # End of loop
                        if not points_to_spend < 0:
                            points_spent = True
                        else:
                            indent.print_("Invalid operation.")
                    party_member.add_stats_points(phy_str_points, mag_pow_points, phy_res_points, mag_res_points, max_hp_points, max_ap_points)
                    party_member.stats.spend_points(phy_str_points + mag_pow_points + phy_res_points + mag_res_points + max_hp_points/10 + max_ap_points)
                    indent.print_("New stats.\n")
                    indent.print_(str(party_member.stats))

    def view_and_learn_abilities(self):
        """Select a party member. View his current abilities and spend CP on"""
        party_member = self.select_party_member()
        with Indenter() as indent:
            indent.print_("{} the {}".format(party_member.name, party_member.character_class.class_name))
            with indent:
                indent.print_("List of {} abilities:".format(party_member.character_class.class_name))
                with indent:
                    for ability in party_member.character_class.ability_list:
                        indent.print_(str(ability))
            if any(a.ability_acquired == False for a in party_member.character_class.ability_list):
                input_text = indent.indent_text("Acquire new abilities ? (Y/N)")
                choice = ''
                while choice != 'N':
                    choice = input(input_text).strip().upper()
                    if choice == 'Y':
                        ability_input_text = ''
                        learnable_abilities = list(filter(lambda a : a.ability_acquired == False, party_member.character_class.ability_list))
                        for i in range(len(learnable_abilities)):
                            ability_input_text += f"{learnable_abilities[i].ability_name}[{i}]: {learnable_abilities[i].cp_cost} CP\n"
                        ability_input_text += "Choose an ability to learn. Press Q to go back."
                        acceptable_choice = list(map(lambda n : str(n), range(len(learnable_abilities))))
                        acceptable_choice.append("Q")
                        ability_chosen = input(ability_input_text).strip().upper()
                        if ability_chosen in acceptable_choice and ability_chosen != 'Q':
                            self.acquire_abilities(party_member, learnable_abilities[int(ability_chosen)])
            else:
                indent.print_("You have learned all {} abilities.".format(party_member.character_class.class_name))

    def acquire_abilities(self, party_member, ability):
        "Learn said ability for the selected party member."
        if party_member.class_points < ability.cp_cost:
            print("You don't have enough CP to learn this ability. (Current CP: {}. Required: {}.)".format(party_member.class_points, ability.cp_cost))
        elif party_member.character_class.class_level < ability.level_acquired:
            print("Your class is not high enough to learn this ability. (Current level: {}. Required: {}.".format(party_member.character_class.class_level, ability.level_acquired))
        else:
            ability.ability_acquired = True
            party_member.class_points -= ability.cp_cost
            print("{} learned {}".format(party_member.name, ability.ability_name))


class Menu:

    def __init__(self, character_list):
        self.character_list = character_list
        self.party_manager = PartyManager(character_list)

    def start_level(self, level_number):
        """Start the level defined by its number."""
        with Level(1, level_number) as level:
            level.progress(self.character_list)

    def ask_level(self):
        """"Ask the user which level to start."""
        while "Input is wrong":
            level_number = input("Enter level(1-{}):".format(max_level))
            if level_number.isdigit() and 0 < int(level_number) <= max_level:
                break
        return level_number

    def manage_party(self):
        """Display a menu to manage the player's party:
            - View Party
            - Change Class
            - Spend stat points
            - Equip abilities and talents
            - Change the name"""
        with Indenter() as indent:
            indent.print_("Party Manager.")
            with indent:
                prompt_text = indent.indent_text("Press 0 to view your party.\n")
                prompt_text += indent.indent_text("Press 1 to change the class of a party member.\n")
                prompt_text += indent.indent_text("Press 2 to spend stat points on a party member.\n")
                prompt_text += indent.indent_text("Press 3 to acquire abilities and equip talents.\n")
                prompt_text += indent.indent_text("Press 4 to change the name of a party member.\n")
                choice = ''
                choice_accepted = range(5)
                while not choice.isdigit() or int(choice) not in choice_accepted:
                    choice = input(prompt_text).strip().upper()
                if choice == '0':
                    self.party_manager.view_party()
                elif choice == '1':
                    self.party_manager.change_class()
                elif choice == '2':
                    self.party_manager.spend_stat_points()
                elif choice == '3':
                    self.party_manager.view_and_learn_abilities()
                elif choice == '4':
                    self.party_manager.change_name()

    def display_menu(self):
        """Display the main menu of the game."""
        with Indenter() as indent:
            indent.print_("Main menu.")
            with indent:
                prompt_text = indent.indent_text("Press 0 to start playing.\n")
                prompt_text += indent.indent_text("Press 1 to manage your party.\n")
                prompt_text += indent.indent_text("Press 2 to heal your party.\n")
                prompt_text += indent.indent_text('Press 3 to quit.\n')
                choice = ''
                choice_accepted = range(4)
                while not choice.isdigit() or int(choice) not in choice_accepted:
                    choice = input(prompt_text).strip()
                if choice == '0':
                    self.start_level(self.ask_level())
                elif choice == '1':
                    self.manage_party()
                elif choice == '2':
                    self.party_manager.heal_party()
                    indent.print_("*Healing sound*")
                    indent.print_("Your party is healed.")
                elif choice == '3':
                    self.quit_game()

    @staticmethod
    def quit_game():
        """Exit the game."""
        with Indenter() as indent:
            indent.print_("Save game? (Y/N)")
            user_choice = input().strip().upper()
            while user_choice not in ("Y","N"):
                user_choice = input().strip().upper()
            if user_choice == 'Y':
                print("Saving is not implemented yet.")
        exit()


# -------------------------- main function -------------------------- #
biggs_id = 1
wedge_id = 2
elaine_id = 3
viviane_id = 4
elaine_stat = CharacterStats(elaine_id, 20, 20, 20, 20, 1000, 50)
biggs_stat = CharacterStats(biggs_id, 20, 20, 20, 20, 1000, 50)
wedge_stat = CharacterStats(wedge_id, 20, 20, 20, 20, 1000, 50)
viviane_stat = CharacterStats(viviane_id, 20, 20, 20 ,20 ,1000, 50)
elaine_job = Wizard()
biggs_job = Knight()
wedge_job = Knight()
viviane_job = Squire()
elaine = Character(elaine_id, "Elaine", elaine_stat, elaine_job)
biggs = Character(biggs_id, "Biggs", biggs_stat, biggs_job)
wedge = Character(wedge_id, "Wedge", wedge_stat, wedge_job)
viviane = Character(viviane_id, "Viviane", viviane_stat, viviane_job)
my_party = list()
my_party.append(biggs)
my_party.append(wedge)
my_party.append(elaine)
my_party.append(viviane)

menu = Menu(my_party)
while "User has not quit":
    menu.display_menu()