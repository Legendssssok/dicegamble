import os
import sys
from glob import glob
from typing import Any, Dict, List, Union

from database.all_db import legend_db
from database.languages import *
from loggers import LOGS

from .translate import translate

try:
    from yaml import safe_load
except ModuleNotFoundError:
    LOGS.error("Please install PyYAML: pip install PyYAML")
    sys.exit(1)


class ULTConfig:
    lang = "en"
    thumb = "resources/extras/ultroid.jpg"


ULTConfig.lang = legend_db.get_key("language") or os.getenv("LANGUAGE", "en")

languages = {}
PATH = "strings/strings/{}.yml"


def load(file):
    if not file.endswith(".yml"):
        return
    elif not os.path.exists(file):
        file = PATH.format("en")
    code = file.split("/")[-1].split("\\")[-1][:-4]
    try:
        with open(file, encoding="UTF-8") as f:
            languages[code] = safe_load(f)
    except Exception as er:
        LOGS.info(f"Error in {file[:-4]} language file")
        LOGS.exception(er)


def load_all_languages():
    for file in glob("strings/strings/*.yml"):
        load(file)


load(PATH.format(ULTConfig.lang))
load_all_languages()


def get_string(key: str, user_id: int, _res: bool = True) -> Any:
    lang = get_user_lang(user_id) or "en"
    try:
        return languages[lang][key]
    except KeyError:
        print("Hello")
        try:
            en_ = languages["en"][key]
            tr = translate(en_, lang_tgt=lang).replace("\ N", "\n")
            if en_.count("{}") != tr.count("{}"):
                tr = en_
            if languages.get(lang):
                languages[lang][key] = tr
            else:
                languages.update({lang: {key: tr}})
            return tr
        except KeyError:
            if not _res:
                return
            return f"Warning: could not load any string with the key `{key}`"
        except TypeError:
            pass
        except Exception as er:
            LOGS.exception(er)
        if not _res:
            return None
        print("lol")
        return languages["en"].get(key) or f"Failed to load language string '{key}'"


def get_help(key, user_id):
    doc = get_string(f"help_{key}", user_id, _res=False)
    if doc:
        return get_string("cmda", user_id) + doc


def get_languages() -> Dict[str, Union[str, List[str]]]:
    load_all_languages()
    return {
        code: {
            "name": languages[code]["name"],
            "natively": languages[code]["natively"],
            "authors": languages[code]["authors"],
        }
        for code in languages
    }
