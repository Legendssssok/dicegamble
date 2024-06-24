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
    from .translate import safe_load


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
        languages[code] = safe_load(
            open(file, encoding="UTF-8"),
        )
    except Exception as er:
        LOGS.info(f"Error in {file[:-4]} language file")
        LOGS.exception(er)


load(PATH.format(ULTConfig.lang))


def get_string(key: str, user_id: int, _res: bool = True) -> Any:
    lang = get_user_lang(user_id) or "en"
    try:
        return languages[lang][key]
    except KeyError:
        try:
            en_ = languages["en"][key]
            tr = translate(en_, lang_tgt=lang).replace("\\ N", "\n")
            print(f"Lang {en_}, {tr}")
            if en_.count("{}") != tr.count("{}"):
                tr = en_
            f_ok = languages.get(lang)
            print(f_ok)
            if f_ok:
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
        return languages["en"].get(key) or f"Failed to load language string '{key}'"


def get_help(key):
    doc = get_string(f"help_{key}", _res=False)
    if doc:
        return get_string("cmda") + doc


def get_languages() -> Dict[str, Union[str, List[str]]]:
    for file in glob("strings/strings/*yml"):
        load(file)
    return {
        code: {
            "name": languages[code]["name"],
            "natively": languages[code]["natively"],
            "authors": languages[code]["authors"],
        }
        for code in languages
    }
