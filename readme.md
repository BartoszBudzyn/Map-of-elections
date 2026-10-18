# Map of Elections - Lite
A simplified version (interface) of the [mapof-elections library](https://pypi.org/project/mapof-elections/).
## Authors:
- Bartosz Budzyn
- Krzysztof Kopel
## Functionalities:
- Conducting experiments on a vast range of elections (both approval and ordinal)
- Generating elections from a number of statistical models
- Measuring distances between elections
- Visualizing: 
  - elections on a compass map (as described in [this paper](https://arxiv.org/abs/2504.03809))
  - votes in an individual election (using a "microscope")
- Allowing users to save and load the results of their work in an efficient, JSON-based way

## Konwersja wyników ze starego formatu

Stara biblioteka zapisuje obliczone wyniki w katalogu
`experiments/<id>/` (`distances/*.csv`, `features/*.csv` i
`coordinates/*.csv`). Można je przekonwertować bez ponownego liczenia:

```powershell
PATH: "\Map-of-elections\"
python -m src.map_of_elections_lite.exports.legacy_converter experiments\legacy_map_check  --json my_experiment.json --proto my_experiment.pb
```

Konwerter używa importerów `mapof` dla odległości i współrzędnych oraz
kopiuje wszystkie kolumny cech. Plik JSON zawiera także czasy obliczeń,
Protobuf używa wyłącznie dotychczasowego schematu. Pełny zestaw wyników,
w tym czasy, dodatkowe kolumny cech i współrzędna `z`, znajduje się w JSON.