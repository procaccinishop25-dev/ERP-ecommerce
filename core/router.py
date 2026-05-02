import importlib

def parse_file(file, marketplace):

    try:
        module = importlib.import_module(f"core.parsers.{marketplace}")
    except ModuleNotFoundError:
        raise Exception(f"Parser per {marketplace} non esiste")

    return module.parse(file)
