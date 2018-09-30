from enum import Enum
from abc import ABCMeta
from lxml import etree
from pathlib import Path
import random
import time
import copy
import pygame
import sys

max_level = 3
combat_text_speed = .75  # in seconds
text_speed = 1


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


class XmlFileContentException(FileContentException):
    pass


class ListTooLongException(Exception):
    pass


class XmlHelper:
    @staticmethod
    def export_party_to_xml(party):
        characters = etree.Element("Characters")
        for character in party:
            characters.append(character.to_xml())
        return characters

    @staticmethod
    def write_xml_to_file(xml, filename):
        tree = etree.ElementTree(xml)
        tree.write(filename, pretty_print=True)

    @staticmethod
    def load_xml(filename):
        tree = etree.parse(filename)
        return tree

    @staticmethod
    def load_party_from_xml(party_xml):
        party = list()
        for party_member in party_xml.xpath("/Characters/Character"):
           party.append(Character.create_from_xml(party_member))
        return party

    @staticmethod
    def fetch_first_text_from_xml_and_value(xml, value):
        value_xml = xml.xpath(value)
        if len(value_xml) == 0:
            return None
        else:
            return value_xml[0].text


class Stats:

    def __init__(self, phy_str, mag_pow, phy_res, mag_res, max_hp, max_ap):
        self.base_phy_str = phy_str
        self.base_mag_pow = mag_pow
        self.base_phy_res = phy_res
        self.base_mag_res = mag_res
        self.base_max_hp = max_hp
        self.base_max_ap = max_ap
        self.phy_str = phy_str
        self.mag_pow = mag_pow
        self.phy_res = phy_res
        self.mag_res = mag_res
        self.hp = max_hp
        self.max_hp = max_hp
        self.ap = max_ap
        self.max_ap = max_ap

    def to_xml(self):
        stats_xml = etree.Element("Stats")
        etree.SubElement(stats_xml, "Phy_str").text = str(self.base_phy_str)
        etree.SubElement(stats_xml, "Mag_pow").text = str(self.base_mag_pow)
        etree.SubElement(stats_xml, "Phy_res").text = str(self.base_phy_res)
        etree.SubElement(stats_xml, "Mag_res").text = str(self.base_mag_res)
        etree.SubElement(stats_xml, "HP").text = str(self.base_max_hp)
        etree.SubElement(stats_xml, "AP").text = str(self.base_max_ap)
        if isinstance(self, CharacterStats):
            stats_xml.set("type", "CharacterStats")
            etree.SubElement(stats_xml, "UnspentPoints").text = str(self.unspent_points)
        elif isinstance(self, FoeStats):
            stats_xml.set("type", "FoeStats")
        return stats_xml

    @staticmethod
    def create_from_xml(xml):
        phy_str_text = XmlHelper.fetch_first_text_from_xml_and_value(xml, "Phy_str")
        mag_pow_text = XmlHelper.fetch_first_text_from_xml_and_value(xml, "Mag_pow")
        phy_res_text = XmlHelper.fetch_first_text_from_xml_and_value(xml, "Phy_res")
        mag_res_text = XmlHelper.fetch_first_text_from_xml_and_value(xml, "Mag_res")
        max_hp_text = XmlHelper.fetch_first_text_from_xml_and_value(xml, "HP")
        max_ap_text = XmlHelper.fetch_first_text_from_xml_and_value(xml, "AP")
        if None in [phy_str_text, mag_pow_text, phy_res_text, mag_res_text, max_hp_text, max_ap_text]:
            raise XmlFileContentException
        if any(x.isdigit() is False for x in [phy_str_text, mag_pow_text, phy_res_text, mag_res_text, max_hp_text, max_ap_text]):
            raise XmlFileContentException
        phy_str = int(phy_str_text)
        mag_pow = int(mag_pow_text)
        phy_res = int(phy_res_text)
        mag_res = int(mag_res_text)
        max_hp = int(max_hp_text)
        max_ap = int(max_ap_text)
        stats_type = xml.get("type")
        if stats_type == "CharacterStats":
            stats = CharacterStats(phy_str, mag_pow, phy_res, mag_res, max_hp, max_ap)
            unspent_points_text = XmlHelper.fetch_first_text_from_xml_and_value(xml, "UnspentPoints")
            if unspent_points_text is None or not unspent_points_text.isdigit():
                raise XmlFileContentException
            stats.unspent_points = int(unspent_points_text)
        elif stats_type == "FoeStats":
            stats = FoeStats(phy_str, mag_pow, phy_res, mag_res, max_hp, max_ap)
        else:
            raise XmlFileContentException
        return stats


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
        self.base_phy_str += phy_str
        self.base_mag_pow += mag_pow
        self.base_phy_res += phy_res
        self.base_mag_res += mag_res
        self.base_max_hp += max_hp
        self.base_max_ap += max_ap
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
            self.unspent_points = round(self.unspent_points)


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

    def get_xp_needed_for_next_class_level(self):
        return self.experience_helper.get_xp_needed_for_next_level(self.class_level)

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
                "Class Experience points: {}/{}".format(self.class_xp,
                                                        self.get_xp_needed_for_next_class_level()))
            indent.print_("Physical Strength Multiplier: {}".format(self.phy_str_mult))
            indent.print_("Magic Power Multiplier: {}".format(self.mag_pow_mult))
            indent.print_("Physical Resistance Multiplier: {}".format(self.phy_res_mult))
            indent.print_("Magic Resistance Multiplier: {}".format(self.mag_res_mult))
            indent.print_("Health Points Multiplier: {}".format(self.hp_mult))
            indent.print_("Ability Points Multiplier: {}".format(self.ap_mult))

    def get_class_abilities_from_file(self):
        filename = f"Abilities/{self.class_name}.txt"
        return_list = list()
        with ManagedFile(filename, 'r') as file:
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
                    # 9 - Ability Type
                    ability_type = file.readline().strip()
                    if (not ability_type.isdigit()) and (not 0 <= int(ability_type) < 4):
                        raise FileContentException
                    else:
                        ability_type = AbilityType(int(ability_type))
                    # 10 - Ability Target
                    ability_target = file.readline().strip()
                    if (not ability_target.isdigit()) and (not 0 <= int(ability_target) < 2):
                        raise FileContentException
                    else:
                        ability_target = AbilityTarget(int(ability_target))
                    # Create Ability
                    ability = Ability(ability_name,
                                      ability_damage,
                                      ability_damage_type,
                                      ability_description,
                                      ability_ap_cost,
                                      ability_is_default,
                                      ability_level_acquired,
                                      ability_cp_cost,
                                      ability_type,
                                      ability_target)
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

    def to_xml(self):
        class_ = etree.Element("Class")
        etree.SubElement(class_, "Name").text = self.class_name
        etree.SubElement(class_, "Level").text = str(self.class_level)
        etree.SubElement(class_, "XP").text = str(self.class_xp)
        abilities = etree.SubElement(class_, "Abilities")
        for ability in self.ability_list:
            abilities.append(ability.to_xml())
        return class_

    @staticmethod
    def create_from_xml(xml):
        name = XmlHelper.fetch_first_text_from_xml_and_value(xml, "Name")
        level_text = XmlHelper.fetch_first_text_from_xml_and_value(xml, "Level")
        xp_text = XmlHelper.fetch_first_text_from_xml_and_value(xml, "XP")
        if None in [name, level_text, xp_text]:
            raise XmlFileContentException
        if any(not x.isdigit() for x in [level_text, xp_text]):
            raise XmlFileContentException
        level = int(level_text)
        xp = int(xp_text)
        character_class_dict = CharacterClass.get_dict_of_class()
        if character_class_dict.get(name) is None:
            raise XmlFileContentException
        character_class = character_class_dict[name]
        character_class.class_level = level
        character_class.class_xp = xp
        ability_list = list()
        for ability_xml in xml.xpath("Abilities/Ability"):
            ability = Ability.create_from_xml(ability_xml)
            ability_list.append(ability)
        character_class.ability_list = ability_list
        return character_class


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
    def __init__(self, ability_name, ability_dmg, ability_dmg_type, ability_description, ap_cost, is_default, level_acquired, cp_cost, ability_type, ability_target):
        self.ability_name = ability_name
        self.ability_dmg = ability_dmg
        self.ability_dmg_type = ability_dmg_type
        self.ability_description = ability_description
        self.ap_cost = ap_cost
        self.ability_acquired = is_default
        self.level_acquired = level_acquired
        self.cp_cost = cp_cost
        self.ability_type = ability_type
        self.ability_target = ability_target

    @staticmethod
    def default_ability():
        return Ability("Normal Attack",
                       10,
                       DamageType.PHY_DMG,
                       "A normal attack",
                       0,
                       0,
                       0,
                       0,
                       AbilityType.ATTACK,
                       AbilityTarget.SINGLE)

    def __str__(self):
        acquired_text = {
            True: "Yes",
            False: "No",
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

    def to_xml(self):
        ability = etree.Element("Ability")
        etree.SubElement(ability, "Name").text = self.ability_name
        etree.SubElement(ability, "Damage").text = str(self.ability_dmg)
        etree.SubElement(ability, "DamageType").text = str(self.ability_dmg_type.value)
        etree.SubElement(ability, "Description").text = self.ability_description
        etree.SubElement(ability, "AP").text = str(self.ap_cost)
        etree.SubElement(ability, "Acquired").text = str(self.ability_acquired)
        etree.SubElement(ability, "Level").text = str(self.level_acquired)
        etree.SubElement(ability, "CP").text = str(self.cp_cost)
        etree.SubElement(ability, "Type").text = str(self.ability_type.value)
        etree.SubElement(ability, "Target").text = str(self.ability_target.value)
        return ability

    @staticmethod
    def create_from_xml(xml):
        name = XmlHelper.fetch_first_text_from_xml_and_value(xml, "Name")
        damage_text = XmlHelper.fetch_first_text_from_xml_and_value(xml, "Damage")
        damage_type_text = XmlHelper.fetch_first_text_from_xml_and_value(xml, "DamageType")
        description = XmlHelper.fetch_first_text_from_xml_and_value(xml, "Description")
        ap_text = XmlHelper.fetch_first_text_from_xml_and_value(xml, "AP")
        acquired_text = XmlHelper.fetch_first_text_from_xml_and_value(xml, "Acquired")
        level_text = XmlHelper.fetch_first_text_from_xml_and_value(xml, "Level")
        cp_text = XmlHelper.fetch_first_text_from_xml_and_value(xml, "CP")
        ability_type_text = XmlHelper.fetch_first_text_from_xml_and_value(xml, "Type")
        ability_target_text = XmlHelper.fetch_first_text_from_xml_and_value(xml, "Target")
        if None in [name,
                    damage_text,
                    damage_type_text,
                    description,
                    ap_text,
                    acquired_text,
                    level_text,
                    cp_text,
                    ability_type_text,
                    ability_target_text]:
            raise XmlFileContentException
        if any(x.isdigit is False for x in [damage_text,
                                            damage_type_text,
                                            ap_text,
                                            level_text,
                                            cp_text,
                                            ability_type_text,
                                            ability_target_text]):
            raise XmlFileContentException
        if acquired_text not in ["True", "False"]:
            raise XmlFileContentException
        if int(damage_type_text) not in DamageType.list():
            raise XmlFileContentException
        if int(ability_type_text) not in AbilityType.list():
            raise XmlFileContentException
        if int(ability_target_text) not in AbilityTarget.list():
            raise XmlFileContentException
        damage = int(damage_text)
        ap = int(ap_text)
        acquired = True if acquired_text == 'True' else False
        level = int(level_text)
        cp = int(cp_text)
        damage_type_int = int(damage_type_text)
        ability_type_int = int(ability_type_text)
        ability_target_int = int(ability_target_text)
        damage_type = DamageType(damage_type_int)
        ability_type = AbilityType(ability_type_int)
        ability_target = AbilityTarget(ability_target_int)
        ability = Ability(name, damage, damage_type, description, ap, acquired, level, cp, ability_type, ability_target)
        return ability


class Passive:
    def __init__(self, passive_type, passive_name, passive_description):
        self.passive_type = passive_type
        self.passive_name = passive_name
        self.passive_description = passive_description


class Character:
    xp = 0
    level = 0
    class_points = 0

    def __init__(self, name, stats, character_class):
        self.name = name
        self.stats = stats
        self.class_dict = CharacterClass.get_dict_of_class()
        self.character_class = self.class_dict.get(character_class.class_name)
        self.experience_helper = ExperienceHelper()
        self.character_class.init_class(self.stats)

    def clone(self):
            return copy.deepcopy(self)

    def change_character_class(self, new_class):
        self.character_class.exit_class(self.stats)
        self.class_dict[self.character_class.class_name] = copy.deepcopy(self.character_class)
        self.character_class = self.class_dict.get(new_class.class_name)
        new_class.init_class(self.stats)

    def get_xp_needed_for_next_level(self):
        return self.experience_helper.get_xp_needed_for_next_level(self.level)

    def display_character(self):
        with Indenter() as indent:
            indent.print_('Name: {}'.format(self.name))
            indent.print_("Level: {}".format(self.level))
            indent.print_(
                "Experience points: {}/{}".format(self.xp,
                                                  self.get_xp_needed_for_next_level))
            indent.print_("CP: {}".format(self.class_points))
            self.stats.display_stats(indent)
            self.character_class.display_class(indent)

    def add_stats_points(self, phy_str, mag_pow, phy_res, mag_res, max_hp, max_ap):
        self.character_class.exit_class(self.stats)
        self.stats.add_stats_points(phy_str, mag_pow, phy_res, mag_res, max_hp, max_ap)
        self.character_class.init_class(self.stats)

    def spend_ap(self, ap):
        self.stats.ap -= ap

    def to_xml(self):
        character = etree.Element("Character")
        etree.SubElement(character, "Name").text = self.name
        etree.SubElement(character, "XP").text = str(self.xp)
        etree.SubElement(character, "Level").text = str(self.level)
        etree.SubElement(character, "CP").text = str(self.class_points)
        etree.SubElement(character, "CurrentClass").text = self.character_class.class_name
        character.append(self.stats.to_xml())
        classes = etree.SubElement(character, "Classes")
        for key in self.class_dict:
            classes.append(self.class_dict[key].to_xml())
        return character

    @staticmethod
    def create_from_xml(character_xml):
        name = XmlHelper.fetch_first_text_from_xml_and_value(character_xml, "Name")
        xp_text = XmlHelper.fetch_first_text_from_xml_and_value(character_xml, "XP")
        level_text = XmlHelper.fetch_first_text_from_xml_and_value(character_xml, "Level")
        cp_text = XmlHelper.fetch_first_text_from_xml_and_value(character_xml, "CP")
        current_class = XmlHelper.fetch_first_text_from_xml_and_value(character_xml, "CurrentClass")
        if None in [name, xp_text, level_text, cp_text, current_class]:
            raise XmlFileContentException
        if any(x.isdigit() is False for x in [xp_text, level_text, cp_text]):
            raise XmlFileContentException
        stats_xml = character_xml.xpath("Stats")
        if len(stats_xml) != 1:
            raise XmlFileContentException
        stats = Stats.create_from_xml(stats_xml[0])
        class_dictionary = CharacterClass.get_dict_of_class()
        for class_xml in character_xml.xpath("Classes/Class"):
            my_class = CharacterClass.create_from_xml(class_xml)
            if class_dictionary.get(my_class.class_name) is not None:
                class_dictionary[my_class.class_name] = my_class
        if class_dictionary.get(current_class) is None:
            raise XmlFileContentException
        my_current_class = class_dictionary[current_class]
        character = Character(name, stats, my_current_class)
        character.class_dict = class_dictionary
        character.character_class = my_current_class
        character.xp = int(xp_text)
        character.level = int(level_text)
        character.class_points = int(cp_text)
        return character


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

    def to_xml(self):
        foe = etree.Element("Foe")
        etree.SubElement(foe, "Name").text = self.name
        foe.append(self.stats.to_xml())
        etree.SubElement(foe, "XP").text = str(self.xp)
        return foe

    def export_foe_to_xml(self):
        foe_xml = self.to_xml()
        XmlHelper.write_xml_to_file(foe_xml, "Data/Foe/{}.xml".format(self.name))


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

    @staticmethod
    def list():
        return list(map(lambda dt: dt.value, DamageType))


class AbilityTarget(Enum):
    SINGLE = 0
    AOE = 1

    @staticmethod
    def list():
        return list(map(lambda at: at.value, AbilityTarget))


class AbilityType(Enum):
    ATTACK = 0
    HEAL = 1
    BUFF = 2
    OTHER = 3

    @staticmethod
    def list():
        return list(map(lambda at: at.value, AbilityTarget))


class BattleEngine:

    def __init__(self, character_list, foe_list, ui):
        self.character_list = character_list
        self.foe_list = foe_list
        self.ui = ui

    def __enter__(self):
        print('Battle start.')
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        print('Battle end.')

    def attack(self, attacker, defenders, ability):
        """Attack the target(s) with the ability."""
        attack_power = ability.ability_dmg
        damage_type = ability.ability_dmg_type
        attacker.spend_ap(ability.ap_cost)
        for defender in defenders:
            if damage_type == DamageType.PHY_DMG:
                damage = attack_power * (attacker.stats.phy_str / defender.stats.phy_res)
            elif damage_type == DamageType.MAG_DMG:
                damage = attack_power * (attacker.stats.mag_pow / defender.stats.mag_res)
            else:
                damage = attack_power
            damage = round(damage)
            defender.stats.hp = defender.stats.hp - damage if defender.stats.hp - damage > 0 else 0
            text_to_display = f'{ability.ability_name}! ' \
                              f'{attacker.name} ({round(attacker.stats.ap)}/{round(attacker.stats.max_ap)}AP)' \
                              f' inflicted {damage}' \
                              f' damage to {defender.name}' \
                              f' ({round(defender.stats.hp)}/{round(defender.stats.max_hp)}HP)'
            # with Indenter() as indent:
            #     with indent:
            #         indent.print_(f'{ability.ability_name}! '
            #                       f'{attacker.name} ({round(attacker.stats.ap)}/{round(attacker.stats.max_ap)}AP)'
            #                       f' inflicted {damage}'
            #                       f' damage to {defender.name}'
            #                       f' ({round(defender.stats.hp)}/{round(defender.stats.max_hp)}HP)')
            ko_text = self.check_if_foe_ko(defender)
            if ko_text is not None:
                text_to_display += ko_text
        self.ui.battle_ui(self.character_list, self.foe_list, text_to_display)

    def heal(self, caster, targets, ability):
        """Heal the target(s) with the ability.
        A heal is amplified by the caster's power and the target's resistance."""
        attack_power = ability.ability_dmg
        damage_type = ability.ability_dmg_type
        caster.spend_ap(ability.ap_cost)
        for target in targets:
            if damage_type == DamageType.PHY_DMG:
                heal = attack_power * caster.stats.phy_str * target.stats.phy_res / caster.stats.max_hp
            elif damage_type == DamageType.MAG_DMG:
                heal = attack_power * caster.stats.mag_pow * target.stats.mag_res / caster.stats.max_hp
            elif damage_type == DamageType.PURE_DMG:
                heal = attack_power * caster.stats.phy_str * caster.stats.mag_pow * target.stats.phy_res * target.stats.mag_res / caster.stats.max_hp
            else:
                heal = attack_power
            heal = round(heal)
            target.stats.hp = target.stats.max_hp if target.stats.hp + heal > target.stats.max_hp else target.stats.hp + heal
            text_to_display = f'{ability.ability_name}! {caster.name} ({caster.stats.ap}/{caster.stats.max_ap}AP)' \
                                  f' healed {target.name} for ' \
                                  f'{heal} HP. ({round(target.stats.hp)}/{round(target.stats.max_hp)}HP)'
            # with Indenter() as indent:
            #     with indent:
            #         indent.print_(f'{ability.ability_name}! {caster.name} ({caster.stats.ap}/{caster.stats.max_ap}AP)'
            #                       f' healed {target.name} for '
            #                       f'{heal} HP. ({round(target.stats.hp)}/{round(target.stats.max_hp)}HP)')

        self.ui.battle_ui(self.character_list, self.foe_list, text_to_display)

    def choose_ability(self, attacker):
        """Choose an ability for the attacker.
         Return a default ability if the attacker is a Foe or if no abilities are found."""
        if isinstance(attacker, Foe):
            return Ability.default_ability()
        else:
            ability_learnt_and_available = list(filter(lambda a: a.ability_acquired and a.ap_cost <= attacker.stats.ap, attacker.character_class.ability_list))
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

    def check_if_foe_ko(self, character):
        if character.stats.hp == 0:
            return '{} is KO !'.format(character.name)

    def check_if_battle_over(self):
        return all(c.stats.hp == 0 for c in self.character_list) or all(f.stats.hp == 0 for f in self.foe_list)

    def handle_victory(self):
        if any(c.stats.hp > 0 for c in self.character_list):
            xp_value = sum(map(lambda f: f.xp, self.foe_list))
            xp_gained_per_character = xp_value / len(self.character_list)
            character_alive = list(filter(lambda c: c.stats.hp > 0, self.character_list))
            for c in character_alive:
                level_up_text = "{} gained {} experience points.".format(c.name, xp_gained_per_character)
                self.ui.battle_ui(self.character_list, self.foe_list, level_up_text)
                # print("{} gained {} experience points.".format(c.name, xp_gained_per_character))
            xp_helper = ExperienceHelper()
            xp_helper.apply_xp(xp_gained_per_character, character_alive)
            xp_helper.apply_class_xp(xp_gained_per_character, character_alive)

    def handle_defeat(self):
        if all(c.stats.hp == 0 for c in self.character_list):
            self.ui.battle_ui(self.character_list, self.foe_list, "Defeat", True)

    def refresh_ap(self):
        for c in self.character_list:
            c.stats.ap = c.stats.max_ap

    def fight(self):
        turn = 1
        while not self.check_if_battle_over():
            is_party_turn = turn % 2 == 1
            if is_party_turn:
                attacker = self.choose_fighter(self.character_list)
            else:
                attacker = self.choose_fighter(self.foe_list)
            ability = self.choose_ability(attacker)
            if ability.ability_type == AbilityType.ATTACK:
                if ability.ability_target == AbilityTarget.SINGLE:
                    defender = list()
                    if is_party_turn:
                        defender.append(self.choose_fighter(self.foe_list))
                    else:
                        defender.append(self.choose_fighter(self.character_list))
                    self.attack(attacker, defender, ability)
                elif ability.ability_target == AbilityTarget.AOE:
                    if is_party_turn:
                        self.attack(attacker, self.foe_list, ability)
                    else:
                        self.attack(attacker, self.character_list, ability)
            elif ability.ability_type == AbilityType.HEAL:
                if ability.ability_target == AbilityTarget.SINGLE:
                    target = list()
                    if is_party_turn:
                        target.append(self.choose_fighter(self.character_list))
                    else:
                        target.append(self.choose_fighter(self.foe_list))
                    self.heal(attacker, target, ability)
                elif ability.ability_target == AbilityTarget.AOE:
                    if is_party_turn:
                        self.heal(attacker, self.character_list, ability)
                    else:
                        self.heal(attacker, self.foe_list, ability)
            turn += 1
            time.sleep(combat_text_speed)
        self.handle_victory()
        self.handle_defeat()
        self.refresh_ap()


class Level:
    end_level = 100

    def __init__(self, level_number, ui):
        self.level_number = level_number
        self.ui = ui

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
                print('An error occurred opening file.')
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
                    creature_stats = FoeStats(creature_phy_str, creature_mag_pow, creature_phy_res, creature_mag_res,
                                              creature_max_hp, creature_max_ap)
                    foe = Foe(foe_number, creature_name, creature_stats)
                    foe.probability = creature_probability
                    foe.xp = creature_xp
                    foe_number += 1
                    foe.export_foe_to_xml() #TODO remove line
                    foe_list.append(foe)
        return foe_list

    def generate_foe(self, foe_number, foe_list):
        """Generate {foe_number) foe(s) from the list."""
        return_list = list()
        prob_list = list()
        foe_number_by_name = dict()
        for f in foe_list:
            for _ in range(0, f.probability):
                prob_list.append(f.clone())
        for n in range(0, foe_number):
            foe = random.choice(prob_list)
            if foe_number_by_name.get(foe.name) is None:
                foe_number_by_name[foe.name] = 1
            else:
                foe_number_by_name[foe.name] += 1
            if foe_number_by_name.get(foe.name) is not None and foe_number_by_name[foe.name] != 1:
                foe.name += f" {foe_number_by_name[foe.name]}"
            return_list.append(foe)
        sorted(return_list, key=lambda x: x.name)
        return return_list

    def progress(self, character_list):
        """Starts a series of battles until the 100th battle or until the party dies."""
        battle_number = 0
        while any(c.stats.hp > 0 for c in character_list):
            battle_number += 1
            print("Battle {}".format(battle_number))
            foe_number = random.randint(1, 4)
            generable_foe_list = self.load_creatures_from_file()
            foe_list = self.generate_foe(foe_number, generable_foe_list)
            text = "Your party encounters:"
            for foe in foe_list:
                text +="\n{}".format(foe.name)
            self.ui.battle_ui(character_list, foe_list, text)
            time.sleep(text_speed)
            # with Indenter() as indent:
            #     indent.print_("Your party encounters:")
            #     with indent:
            #         for foe in foe_list:
            #             indent.print_(foe.name)
            with BattleEngine(character_list, foe_list, self.ui) as battle:
                battle.fight()
            if battle_number == self.end_level:
                break
        if battle_number == self.end_level:
            self.ui.battle_ui(character_list, foe_list, "Your party completed level {}.".format(self.level_number), True)
        else:
            self.ui.battle_ui(character_list, foe_list, "Your party died at Battle {}".format(battle_number), True)


class ExperienceHelper:

    def __init__(self):
        self.xp_values = self.load_level_threshold()

    def apply_xp(self, xp_gained, character_list):
        """Add xp to the whole party. Level up a party member if necessary."""
        for c in character_list:
            c.xp += round(xp_gained)
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
            c.class_points += round(xp_gained/10)  #TODO Better system.
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
    def __init__(self, party, ui):
        self.party = party
        self.ui = ui

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

    # def change_name(self):
    #     """"Choose a party member. Change it's name."""
    #     party_member = self.select_party_member()
    #     with Indenter() as indent:
    #         indent.print_("{} the {}.".format(party_member.name, party_member.character_class.class_name))
    #         new_name_confirmed = False
    #         new_name = ''
    #         while not new_name_confirmed:
    #             new_name = input(indent.indent_text("What shall be {} new name ?".format(party_member.name))).strip()
    #             confirmation = input("Do you confirm {} as {}'s new name ?"
    #                                  "(Press Y or N or press Q to stop changing name)"
    #                                  .format(new_name, party_member.name)).strip().upper()
    #             if confirmation == 'Y':
    #                 new_name_confirmed = True
    #             if confirmation == 'Q':
    #                 indent.print_("You have not changed {}'s name".format(party_member.name))
    #                 return
    #         party_member.name = new_name

    def change_name(self, character, name):
        character.name = name

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
                    phy_str_points = -1
                    mag_pow_points = -1
                    phy_res_points = -1
                    mag_res_points = -1
                    max_hp_points = -1
                    max_ap_points = -1
                    while not points_spent:
                        points_to_spend = party_member.stats.unspent_points

                        # Phy_str
                        input_phy_str = indent.indent_text("Physical Strength:\n")
                        with indent:
                            input_phy_str += indent.indent_text("Current: {}\n".format(party_member.stats.phy_str))
                            input_phy_str += indent.indent_text("Points available: {}\n".format(points_to_spend))
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
            if any(a.ability_acquired is False for a in party_member.character_class.ability_list):
                input_text = indent.indent_text("Acquire new abilities ? (Y/N)")
                choice = ''
                while choice != 'N':
                    choice = input(input_text).strip().upper()
                    if choice == 'Y':
                        ability_input_text = ''
                        learnable_abilities = list(filter(lambda a: a.ability_acquired is False, party_member.character_class.ability_list))
                        for i in range(len(learnable_abilities)):
                            ability_input_text += f"{learnable_abilities[i].ability_name}[{i}]: {learnable_abilities[i].cp_cost} CP\n"
                        ability_input_text += "Choose an ability to learn. Press Q to go back."
                        acceptable_choice = list(map(lambda n: str(n), range(len(learnable_abilities))))
                        acceptable_choice.append("Q")
                        ability_chosen = input(ability_input_text).strip().upper()
                        if ability_chosen in acceptable_choice and ability_chosen != 'Q':
                            self.acquire_abilities(party_member, learnable_abilities[int(ability_chosen)])
            else:
                indent.print_("You have learned all {} abilities.".format(party_member.character_class.class_name))

    def learn_abilities(self, party_member, abilities):
        abilities_name = list(map(lambda a: a.ability_name, abilities))
        abilities_to_learn = list(filter(lambda a: a.ability_name in abilities_name, party_member.character_class.ability_list))
        for ability in abilities_to_learn:
            self.acquire_abilities(party_member, ability)

    def acquire_abilities(self, party_member, ability):
        """"Learn said ability for the selected party member."""
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
        self.ui = UserInterface()
        self.party_manager = PartyManager(character_list, self.ui)
        self.ui = UserInterface()

    def start_level(self, level_number):
        """Start the level defined by its number."""
        with Level(level_number, self.ui) as level:
            level.progress(self.character_list)

    def ask_level(self):
        """"Ask the user which level to start."""
        while "Input is wrong":
            level_number = self.ui.input_text("Enter level(1-{}):".format(max_level))
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
        option_list = list()
        option_list.append("View your party")
        option_list.append("Change the class of a party member")
        option_list.append("Spend stat points on a party member")
        option_list.append("Acquire abilities and equip talents")
        option_list.append("Change the name of a party member")
        choice = self.ui.display_menu(option_list)
        if choice == 1:
            # View Party
            character = self.ui.choose_character(self.character_list, None)
            if character is not None:
                print(character.name)
        elif choice == 2:
            # Change Class
            i = 1
        elif choice == 3:
            # Spend points
            i = 1
        elif choice == 4:
            # Acquire abilities
            character = self.ui.choose_character(self.character_list, "Choose a character.")
            if character is not None:
                char_cloned = character.clone()
                ability_to_upgrade = self.ui.list_ability(char_cloned, """Hover on an ability to view its description.
                Spend Skills Points to unlock new abilities and talents.""")
                if ability_to_upgrade is not None:
                    self.party_manager.learn_abilities(character, ability_to_upgrade)
        elif choice == 5:
            character = self.ui.choose_character(self.character_list, "Choose a character.")
            if character is not None:
                new_name = self.ui.input_text("Choose the new name.")
                self.party_manager.change_name(character, new_name)
        # with Indenter() as indent:
        #     indent.print_("Party Manager.")
        #     with indent:
        #         prompt_text = indent.indent_text("Press 0 to view your party.\n")
        #         prompt_text += indent.indent_text("Press 1 to change the class of a party member.\n")
        #         prompt_text += indent.indent_text("Press 2 to spend stat points on a party member.\n")
        #         prompt_text += indent.indent_text("Press 3 to acquire abilities and equip talents.\n")
        #         prompt_text += indent.indent_text("Press 4 to change the name of a party member.\n")
        #         choice = ''
        #         choice_accepted = range(5)
        #         while not choice.isdigit() or int(choice) not in choice_accepted:
        #             choice = input(prompt_text).strip().upper()
        #         if choice == '0':
        #             self.party_manager.view_party()
        #         elif choice == '1':
        #             self.party_manager.change_class()
        #         elif choice == '2':
        #             self.party_manager.spend_stat_points()
        #         elif choice == '3':
        #             self.party_manager.view_and_learn_abilities()
        #         elif choice == '4':
        #             self.party_manager.change_name()

    def display_menu(self):
        """Display the main menu of the game."""
        self.ui.display_start_screen()
        option_list = list()
        option_list.append("Start a level")
        option_list.append("Manage the party")
        option_list.append("Heal party")
        option_list.append("Quit")
        while 1:
            choice = self.ui.display_menu(option_list)
            print("Choice = {}".format(choice))
            if choice == 1:
                self.start_level(self.ask_level())
            elif choice == 2:
                self.manage_party()
            elif choice == 3:
                self.party_manager.heal_party()
                self.ui.display_text("*Healing sound*")
                self.ui.display_text("Your party is healed.")
            elif choice == 4:
                self.quit_game()
        # with Indenter() as indent:
        #     indent.print_("Main menu.")
        #     with indent:
        #         prompt_text = indent.indent_text("Press 0 to start playing.\n")
        #         prompt_text += indent.indent_text("Press 1 to manage your party.\n")
        #         prompt_text += indent.indent_text("Press 2 to heal your party.\n")
        #         prompt_text += indent.indent_text('Press 3 to quit.\n')
        #         choice = ''
        #         choice_accepted = range(4)
        #         while not choice.isdigit() or int(choice) not in choice_accepted:
        #             choice = input(prompt_text).strip()
        #         if choice == '0':
        #             self.start_level(self.ask_level())
        #         elif choice == '1':
        #             self.manage_party()
        #         elif choice == '2':
        #             self.party_manager.heal_party()
        #             indent.print_("*Healing sound*")
        #             indent.print_("Your party is healed.")
        #         elif choice == '3':
        #             self.quit_game()

    def quit_game(self):
        """Exit the game."""
        option_list = list()
        option_list.append("Yes")
        option_list.append("No")
        choice = self.ui.display_menu(option_list)
        if choice == 1:
            filename = "Data/Save.xml"
            party_xml = XmlHelper.export_party_to_xml(self.character_list)
            XmlHelper.write_xml_to_file(party_xml, filename)
            exit()
        # with Indenter() as indent:
        #     indent.print_("Save game? (Y/N)")
        #     user_choice = input().strip().upper()
        #     while user_choice not in ("Y", "N"):
        #         user_choice = input().strip().upper()
        #     if user_choice == 'Y':
        #         filename = "Data/Save.xml"
        #         party_xml = XmlHelper.export_party_to_xml(self.character_list)
        #         XmlHelper.write_xml_to_file(party_xml, filename)


class UserInterface:
    length = 1000
    height = 800
    start_button_length = 50
    start_button_height = 30
    start_button_x_position = 500 - start_button_length / 2
    start_button_y_position = 700 - start_button_height / 2
    white_color = (224, 224, 224)
    black_color = (32, 32, 32)
    red_color = (224, 0, 0)
    gray_color = (128, 128, 128)
    yellow_color = (255, 255, 0)
    green_color = (0, 128, 0)
    max_option_nb = 8

    def __init__(self):
        pygame.init()
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.button_font = pygame.font.Font(None, 28)
        self.small_font = pygame.font.Font(None, 24)
        self.surf = pygame.display.set_mode((self.length, self.height), pygame.SRCALPHA)

    def display_start_screen(self):
        """Display the start screen. The user must click on the play game link to start the game."""
        self.reset_screen()
        welcome_text = self.font.render("Welcome to the Fuzzy-broccoli game !", 1, self.white_color)
        start_game = False
        while True:
            self.clock.tick(30)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONUP:
                    p = pygame.mouse.get_pos()
                    if self.start_button_x_position <= p[0] <= self.start_button_x_position + self.start_button_length \
                            and self.start_button_y_position <= p[1] <= self.start_button_y_position + self.start_button_height:
                        welcome_text = self.font.render("Starting game...", 1, self.white_color)
                        start_game = True
            self.surf.fill((32, 32, 32))
            play_text = self.button_font.render("Start", 1, self.white_color)
            self.surf.blit(welcome_text, (300, 400))
            self.surf.blit(play_text, (self.start_button_x_position, self.start_button_y_position))
            pygame.display.update()
            if start_game:
                break

    def display_menu(self, option_list):
        """
        Display a menu with options that the user can click on
        :param option_list: A list of string to be displayed as options
        :return: A number from 1 to max_option_nb that references the user's choice from option_list
        """
        if len(option_list) > self.max_option_nb:
            raise ListTooLongException
        self.reset_screen()
        number = 1
        for option in option_list:
            text = self.button_font.render(option, 1, self.white_color)
            if number <= 4:
                self.surf.blit(text, (.055 * self.length, (.74 + .04 * number) * self.height))
            else:
                self.surf.blit(text, (.555 * self.length, (.74 + .04 * (number - 4)) * self.height))
            number += 1
        pygame.draw.rect(self.surf,
                         self.white_color,
                         (.05 * self.length, .75 * self.height, 0.90 * self.length, .20 * self.height), 1)
        while True:
            self.clock.tick(30)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONUP:
                    p = pygame.mouse.get_pos()
                    for i in range(1, len(option_list) + 1):
                        if i <= 4 \
                                and .055 * self.length <= p[0] <= .5 * self.length \
                                and (.74 + .04 * i) * self.height <= p[1] <= (.74 + .04 * (i + 1)) * self.height:
                            return i
                        if i > 4 \
                                and .555 * self.length <= p[0] <= .9 * self.length \
                                and (.74 + .04 * (i - 4)) * self.height <= p[1] <= (.74 + .04 * (i - 3)) * self.height:
                            return i
            pygame.display.update()

    def display_text(self, text):
        """
        Display a text, the user must click to reach the function's end.
        :param text: Text to display
        """
        self.reset_screen()
        pygame.draw.rect(self.surf,
                         self.white_color,
                         (.05 * self.length, .75 * self.height, 0.90 * self.length, .20 * self.height), 1)
        displayed_text = self.button_font.render(text, 1, self.white_color)
        self.surf.blit(displayed_text, (.055 * self.length, .78 * self.height))
        while True:
            self.clock.tick(30)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONUP:
                    return
            pygame.display.update()

    def battle_ui(self, party, enemy_party, text_to_display=None, wait_for_input=False):
        """
        Display the ui used in battle with a text
        :param party: the player's party
        :param enemy_party: the enemy's party
        :param text_to_display: The text to display
        :param wait_for_input: if the user must click after the data are displayed
        """
        self.reset_screen()
        pygame.draw.rect(self.surf,
                         self.white_color,
                         (.05 * self.length, .75 * self.height, 0.90 * self.length, .20 * self.height), 1)
        self.clock.tick(30)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
        for n in range(0, len(party)):
            pm_name = party[n].name
            pm_name_text = self.small_font.render(pm_name, 1, self.white_color)
            pm_hp_text = self.small_font.render(f"{party[n].stats.hp}/{party[n].stats.max_hp}", 1, self.white_color, self.black_color)
            pm_ap_text = self.small_font.render(f"{party[n].stats.ap}/{party[n].stats.max_ap}", 1, self.white_color, self.black_color)
            self.surf.blit(pm_name_text, (.2 * (n + 1) * self.length, .5 * self.height))
            self.surf.blit(pm_hp_text, (.2 * (n + 1) * self.length, .55 * self.height))
            self.surf.blit(pm_ap_text, (.2 * (n + 1) * self.length, .6 * self.height))
        for n in range(0, len(enemy_party)):
            foe_name = enemy_party[n].name
            foe_name_text = self.small_font.render(foe_name, 1, self.white_color)
            foe_hp_text = self.small_font.render(f"{enemy_party[n].stats.hp}/{enemy_party[n].stats.max_hp}", 1, self.white_color, self.black_color)
            foe_ap_text = self.small_font.render(f"{enemy_party[n].stats.ap}/{enemy_party[n].stats.max_ap}", 1, self.white_color, self.black_color)
            self.surf.blit(foe_name_text, (self.length - (.2 * (n + 1) * self.length), .1 * self.height))
            self.surf.blit(foe_hp_text, (self.length - (.2 * (n + 1) * self.length), .15 * self.height))
            self.surf.blit(foe_ap_text, (self.length - (.2 * (n + 1) * self.length), .2 * self.height))
        if text_to_display is not None:
            displayed_text = self.small_font.render(text_to_display, 1, self.white_color, self.black_color)
            self.surf.blit(displayed_text, (.055 * self.length, .78 * self.height))
        pygame.display.update()
        if wait_for_input:
            while True:
                self.clock.tick(30)
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        sys.exit()
                    if event.type == pygame.MOUSEBUTTONUP:
                        return

    def input_text(self, text):
        """
        Ask for the user to enter a text, then returns it
        :param text: A string to be displayed
        :return: Text the user entered
        """
        active = False
        input_box = pygame.Rect(.45 * self.length, .45 * self.height, 140, 32)
        color_inactive = self.gray_color
        color_active = self.white_color
        color = color_inactive
        return_text = ''
        done = False
        self.reset_screen()
        pygame.draw.rect(self.surf,
                         self.white_color,
                         (.05 * self.length, .75 * self.height, 0.90 * self.length, .20 * self.height), 1)
        displayed_text = self.button_font.render(text, 1, self.white_color)
        self.surf.blit(displayed_text, (.055 * self.length, .78 * self.height))
        pygame.draw.rect(self.surf,
                         self.white_color,
                         input_box, 1)
        while not done:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if input_box.collidepoint(event.pos):
                        active = not active
                    else:
                        active = False
                    color = color_active if active else color_inactive
                if event.type == pygame.KEYDOWN:
                    if active:
                        if event.key == pygame.K_RETURN:
                            done = True
                        elif event.key == pygame.K_BACKSPACE:
                            return_text = return_text[:-1]
                        else:
                            return_text += event.unicode
            txt_surface = self.button_font.render(return_text, True, color)
            width = max(200, txt_surface.get_width()+10)
            input_box.w = width
            self.surf.fill(self.black_color)
            pygame.draw.rect(self.surf,
                             self.white_color,
                             (.05 * self.length, .75 * self.height, 0.90 * self.length, .20 * self.height), 1)
            displayed_text = self.button_font.render(text, 1, self.white_color)
            self.surf.blit(displayed_text, (.055 * self.length, .78 * self.height))
            pygame.draw.rect(self.surf,
                             self.white_color,
                             input_box,
                             1)
            self.surf.blit(txt_surface, (input_box.x+5, input_box.y+5))
            self.clock.tick(30)
            pygame.display.update()
        return return_text

    def choose_character(self, character_list, text):
        """
        User interface to display the party, and to select a character from the party.
        :param character_list: The list of characters
        :param text: An optional text to be displayed.
        :return: None if clicked on the return button, or a character from character_list
        """
        if len(character_list) > 4:
            return
        done = False
        self.reset_screen()

        # Note: 2 * offset + 4 * length + 3 * gap = 100%
        offset = .05
        length = 0.1875
        gap = .05
        rect_list = list()
        return_button = pygame.Rect(.95 * self.length,
                                    .01 * self.height,
                                    .04 * self.length,
                                    .03 * self.height)
        pygame.draw.rect(self.surf,
                         self.red_color,
                         return_button)
        if text is not None:
            displayed_text = self.button_font.render(text, 1, self.white_color)
            self.surf.blit(displayed_text, (.055 * self.length, .78 * self.height))
            pygame.draw.rect(self.surf,
                             self.white_color,
                             (.05 * self.length, .75 * self.height, 0.90 * self.length, .20 * self.height), 1)
        for i in range(len(character_list)):
            x = (offset + (length + gap) * i) * self.length
            y = .2 * self.height
            rect_list.append(pygame.Rect(x,
                                         y,
                                         length * self.length,
                                         .4 * self.height))
            character_name = character_list[i].name
            character_job = f"{character_list[i].character_class.class_name} " \
                            f"lv. {character_list[i].character_class.class_level}" \
                            f" ({character_list[i].character_class.class_xp}" \
                            f"/{character_list[i].character_class.get_xp_needed_for_next_class_level()})"
            character_level = f"Lv. {character_list[i].level} " \
                              f"({character_list[i].xp}/{character_list[i].get_xp_needed_for_next_level()})"
            character_phy_str = f"Phy. Str.: {round(character_list[i].stats.phy_str)}"
            character_mag_pow = f"Mag. Pow.: {round(character_list[i].stats.mag_pow)}"
            character_phy_res = f"Phy. Res.: {round(character_list[i].stats.phy_res)}"
            character_mag_res = f"Mag. Res.: {round(character_list[i].stats.mag_res)}"
            character_hp = f"{round(character_list[i].stats.hp)}/{round(character_list[i].stats.max_hp)} HP"
            character_ap = f"{round(character_list[i].stats.ap)}/{round(character_list[i].stats.max_ap)} AP"
            displayed_name = self.button_font.render(character_name, 1, self.white_color)
            displayed_job = self.small_font.render(character_job, 1, self.white_color)
            displayed_level = self.small_font.render(character_level, 1, self.white_color)
            displayed_phy_str = self.small_font.render(character_phy_str, 1, self.white_color)
            displayed_mag_pow = self.small_font.render(character_mag_pow, 1, self.white_color)
            displayed_phy_res = self.small_font.render(character_phy_res, 1, self.white_color)
            displayed_mag_res = self.small_font.render(character_mag_res, 1, self.white_color)
            displayed_hp = self.small_font.render(character_hp, 1, self.white_color)
            displayed_ap = self.small_font.render(character_ap, 1, self.white_color)
            self.surf.blit(displayed_name, (x + 15, y + 20))
            self.surf.blit(displayed_level, (x + 15, y + 60))
            self.surf.blit(displayed_job, (x + 15, y + 80))
            self.surf.blit(displayed_hp, (x + 15, y + 100))
            self.surf.blit(displayed_ap, (x + 15, y + 120))
            self.surf.blit(displayed_phy_str, (x + 15, y + 140))
            self.surf.blit(displayed_mag_pow, (x + 15, y + 160))
            self.surf.blit(displayed_phy_res, (x + 15, y + 180))
            self.surf.blit(displayed_mag_res, (x + 15, y + 200))
        for rect in rect_list:
            pygame.draw.rect(self.surf,
                             self.white_color,
                             rect,
                             1)
        while not done:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if return_button.collidepoint(event.pos):
                        return
                    for i in range(len(rect_list)):
                        if rect_list[i].collidepoint(event.pos):
                            return character_list[i]
            pygame.display.update()

    def list_ability(self, character, text=None):
        """
        List the ability of the party member's job. Abilities can be learned by clicking them.
        :param character: The party member
        :param text: An optional text to display
        :return: The list of ability to learn
        """
        self.reset_screen()
        done = False
        ability_x_pos = .25 * self.length
        ability_y_pos = .1 * self.height
        text_offset = 15
        small_text_size = 20
        text_box = pygame.Rect(.05 * self.length, .75 * self.height, 0.90 * self.length, .20 * self.height)
        ability_box = pygame.Rect(ability_x_pos, ability_y_pos, .7 * self.length, .6 * self.height)
        ability_to_upgrade = list()
        ability_rect = list()
        ability_title = self.button_font.render("Abilities:", 1, self.white_color)
        ability_description = None
        for i in range(len(character.character_class.ability_list)):
            ability_rect.append(pygame.Rect(ability_x_pos + text_offset,
                                            ability_y_pos + small_text_size * (i + 2),
                                            .7 * self.length,
                                            small_text_size))
        # Draw return button.
        return_button = pygame.Rect(.95 * self.length,
                                    .01 * self.height,
                                    .04 * self.length,
                                    .03 * self.height)
        pygame.draw.rect(self.surf,
                         self.red_color,
                         return_button)
        # Draw confirm button.
        confirm_button = pygame.Rect(.9 * self.length,
                                     .01 * self.height,
                                     .04 * self.length,
                                     .03 * self.height)
        pygame.draw.rect(self.surf,
                         self.green_color,
                         confirm_button)
        while not done:
            self.clock.tick(30)
            self.display_character_box(character, True)

            # Refresh the text box and ability list
            pygame.draw.rect(self.surf,
                             self.black_color,
                             ability_box)
            pygame.draw.rect(self.surf,
                             self.black_color,
                             text_box)
            # Draw ability box
            pygame.draw.rect(self.surf,
                             self.white_color,
                             ability_box,
                             1)
            self.surf.blit(ability_title, (ability_x_pos + text_offset, ability_y_pos + small_text_size))

            # Iterate the abilities, draw them
            for i in range(len(character.character_class.ability_list)):
                ability = character.character_class.ability_list[i]
                color = self.gray_color
                if ability.ability_acquired or ability in ability_to_upgrade:
                    color = self.white_color
                elif character.class_points >= ability.cp_cost:
                    color = self.green_color
                ability_text = f"{ability.ability_name}"
                if not color == self.white_color:
                    ability_text += f" {ability.cp_cost}CP"
                ability_name = self.small_font.render(ability_text, 1, color)
                self.surf.blit(ability_name,
                               (ability_x_pos + text_offset, ability_y_pos + small_text_size * (i + 2)))
            # Handle the events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if return_button.collidepoint(event.pos):
                        return None
                    if confirm_button.collidepoint(event.pos):
                        return ability_to_upgrade
                    for i in range(len(ability_rect)):
                        if ability_rect[i].collidepoint(event.pos):
                            ability = character.character_class.ability_list[i]
                            if not ability.ability_acquired and character.class_points >= ability.cp_cost:
                                ability_to_upgrade.append(character.character_class.ability_list[i])
                                character.class_points -= ability.cp_cost
                if event.type == pygame.MOUSEMOTION:
                    for i in range(len(ability_rect)):
                        if ability_rect[i].collidepoint(event.pos):
                            ability = character.character_class.ability_list[i]
                            ability_description = f"{ability.ability_name}\n" \
                                                  f"{ability.ability_description}\n" \
                                                  f"{ability.ability_dmg} " \
                                                  f"{'single' if ability.ability_target is AbilityTarget.SINGLE else 'AOE'} " \
                                                  f"{'physical' if ability.ability_dmg_type is DamageType.PHY_DMG else 'magic' if ability.ability_dmg_type is DamageType.MAG_DMG else 'pure'} " \
                                                  f"{'damage' if ability.ability_type is AbilityType.ATTACK else 'heal'}\n" \
                                                  f"{ability.ap_cost} AP"

            # Draw text box
            if text is not None or ability_description is not None:
                if ability_description is not None:
                    displayed_text = self.button_font.render(ability_description, 1, self.white_color)
                else:
                    displayed_text = self.button_font.render(text, 1, self.white_color)
                self.surf.blit(displayed_text, (.055 * self.length, .78 * self.height))
                pygame.draw.rect(self.surf,
                                 self.white_color,
                                 text_box,
                                 1)
            pygame.display.update()

    def display_character_box(self, character, display_details=False):
        x = .05 * self.length
        y = .1 * self.height
        small_text_size = 20
        text_offset = 15
        character_box = pygame.Rect(x, y, .1875 * self.length, .6 * self.height)

        # First refresh the box, then draw it
        pygame.draw.rect(self.surf, self.black_color, character_box)
        pygame.draw.rect(self.surf, self.white_color, character_box, 1)
        character_name = character.name
        character_job = f"{character.character_class.class_name} " \
                        f"lv. {character.character_class.class_level}" \
                        f" ({character.character_class.class_xp}" \
                        f"/{character.character_class.get_xp_needed_for_next_class_level()})"
        character_level = f"Lv. {character.level} " \
                          f"({character.xp}/{character.get_xp_needed_for_next_level()})"
        character_phy_str = f"Phy. Str.: {round(character.stats.phy_str)}"
        character_mag_pow = f"Mag. Pow.: {round(character.stats.mag_pow)}"
        character_phy_res = f"Phy. Res.: {round(character.stats.phy_res)}"
        character_mag_res = f"Mag. Res.: {round(character.stats.mag_res)}"
        character_hp = f"{round(character.stats.hp)}/{round(character.stats.max_hp)} HP"
        character_ap = f"{round(character.stats.ap)}/{round(character.stats.max_ap)} AP"
        displayed_name = self.button_font.render(character_name, 1, self.white_color)
        displayed_job = self.small_font.render(character_job, 1, self.white_color)
        displayed_level = self.small_font.render(character_level, 1, self.white_color)
        displayed_phy_str = self.small_font.render(character_phy_str, 1, self.white_color)
        displayed_mag_pow = self.small_font.render(character_mag_pow, 1, self.white_color)
        displayed_phy_res = self.small_font.render(character_phy_res, 1, self.white_color)
        displayed_mag_res = self.small_font.render(character_mag_res, 1, self.white_color)
        displayed_hp = self.small_font.render(character_hp, 1, self.white_color)
        displayed_ap = self.small_font.render(character_ap, 1, self.white_color)
        self.surf.blit(displayed_name, (x + text_offset, y + small_text_size))
        self.surf.blit(displayed_level, (x + text_offset, y + small_text_size * 3))
        self.surf.blit(displayed_job, (x + text_offset, y + small_text_size * 4))
        self.surf.blit(displayed_hp, (x + text_offset, y + small_text_size * 5))
        self.surf.blit(displayed_ap, (x + text_offset, y + small_text_size * 6))
        self.surf.blit(displayed_phy_str, (x + text_offset, y + small_text_size * 7))
        self.surf.blit(displayed_mag_pow, (x + text_offset, y + small_text_size * 8))
        self.surf.blit(displayed_phy_res, (x + text_offset, y + small_text_size * 9))
        self.surf.blit(displayed_mag_res, (x + text_offset, y + small_text_size * 10))
        if display_details:
            character_class_points = f"Class points: {character.class_points}"
            displayed_cp = self.small_font.render(character_class_points, 1, self.white_color)
            self.surf.blit(displayed_cp, (x + text_offset, y + small_text_size * 11))

    def reset_screen(self):
        """Reset the screen to a black surface. Refresh the display."""
        self.surf.fill(self.black_color)
        pygame.display.update()

# -------------------------- main function -------------------------- #
biggs_id = 1
wedge_id = 2
elaine_id = 3
viviane_id = 4
elaine_stat = CharacterStats(20, 20, 20, 20, 1000, 50)
biggs_stat = CharacterStats(20, 20, 20, 20, 1000, 50)
wedge_stat = CharacterStats(20, 20, 20, 20, 1000, 50)
viviane_stat = CharacterStats(20, 20, 20, 20, 1000, 50)
elaine_job = Wizard()
biggs_job = Knight()
wedge_job = Knight()
viviane_job = Squire()
elaine = Character("Elaine", elaine_stat, elaine_job)
biggs = Character("Owen", biggs_stat, biggs_job)
wedge = Character("Gawain", wedge_stat, wedge_job)
viviane = Character("Vivienne", viviane_stat, viviane_job)
my_party = list()
my_party.append(biggs)
my_party.append(wedge)
my_party.append(elaine)
my_party.append(viviane)
save = Path("Data/Save.xml")
if save.exists():
    tree = XmlHelper.load_xml("Data/Save.xml")
    my_party = XmlHelper.load_party_from_xml(tree)

menu = Menu(my_party)
while "User has not quit":
    menu.display_menu()


# ui = UserInterface()
# ui.display_start_screen()

# pygame.init()
# clock = pygame.time.Clock()
# red = 255
# surf = pygame.display.set_mode((1000, 800), pygame.SRCALPHA)
# button_x_length = 60
# button_x_start = 500 - button_x_length / 2
# button_y_length = 30
# button_y_start = 700 - button_y_length / 2
# font = pygame.font.Font(None, 36)
# button_font = pygame.font.Font(None, 28)
# welcome_text = font.render("Welcome to the Fuzzy-broccoli game !", 1, (224, 224, 224))
# while True:
#     clock.tick(30)
#     for event in pygame.event.get():
#         if event.type == pygame.QUIT:
#             sys.exit()
#         if event.type == pygame.MOUSEBUTTONUP:
#             p = pygame.mouse.get_pos()
#             if button_x_start <= p[0] <= button_x_start + button_x_length and button_y_start <= p[1] <= button_y_start + button_y_length:
#                 welcome_text = font.render("Starting game...", 1, (224, 224, 224))
#                 save = Path("Data/Save.xml")
#                 if save.exists():
#                     tree = XmlHelper.load_xml("Data/Save.xml")
#                     my_party = XmlHelper.load_party_from_xml(tree)
#             else:
#                 welcome_text = font.render("Click the start button, you idiot...", 1, (224, 224, 224))
#     surf.fill((32, 32, 32))
#     # pygame.draw.rect(surf, (0, 255, 0), (button_x_start, button_y_start, button_x_length, button_y_length))
#     play_text = button_font.render("Start", 1, (224, 224, 224))
#     surf.blit(welcome_text, (300, 400))
#     surf.blit(play_text, (button_x_start, button_y_start))
#     pygame.display.update()
