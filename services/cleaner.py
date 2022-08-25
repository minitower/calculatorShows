from pathlib import Path
import os


def envCleaner(value: str):
    """
    value - one of ['bin', 'plot', 'table']
    """
    if value.lower() == 'bin':
        path = Path(os.environ.get('PROJECTPATH')) / Path('resultsBin')

    elif value.lower() == 'plot':
        path = Path(os.environ.get('PROJECTPATH')) / Path('templates/plots')

    elif value.lower() == 'table':
        path = Path(os.environ.get('PROJECTPATH')) / Path('templates/tables')

    else:
        raise ValueError(f"Can't indentify value {value}"
                         "(must be table, plot or bin)")
    tmpFilesList = [i for i in os.walk(path)][-1][-1]
    for i in tmpFilesList:
        os.remove(path / Path(i))
