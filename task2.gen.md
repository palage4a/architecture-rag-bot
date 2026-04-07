# План выполнения Задания 2: Подготовка базы знаний

## Этап 1: Выбор предметной области
- **Вселенная**: Star Wars (starwars.fandom.com)
- **Количество**: 30+ страниц (персонажи, планеты, технологии, корабли, события)

## Этап 2: Сбор и очистка текстов
- Написать Python-скрипт для скачивания страниц через requests + BeautifulSoup
- Удалить HTML-теги, навигацию, рекламу
- Сохранить чистый текст в отдельные файлы (1 файл = 1 сущность)

## Этап 3: Создание словаря замен
```json
{
  "Darth Vader": "Xarn Velgor",
  "Death Star": "Void Core",
  "The Force": "Synth Flux",
  "Luke Skywalker": "Lyris Talon",
  "Yoda": "Vorn",
  "Jedi": "Synth Wardens",
  "Sith": "Void Lords",
  "Empire": "Dominion of Kern",
  "Rebels": "Free Worlds Alliance",
  "Millennium Falcon": "Stellar Drift",
  "Lightsaber": "Flux Blade",
  "Stormtrooper": "Void Guard",
  "Han Solo": "Kael Stroem",
  "Leia Organa": "Aira Neth",
  "Chewbacca": "Chuura",
  "Galactic Empire": "Kern Dominion",
  "TIE Fighter": "Ion Wing",
  "X-Wing": "Solar Crest",
  "Hoth": "Kael-7",
  "Tatooine": "Dune Prime",
  "Alderaan": "Verath-4",
  "Coruscant": "Nexus Prime",
  "Jedi Order": "Synth Warden Order",
  "Sith Empire": "Void Lords Dominion",
  "Jedi Temple": "Nexus Hall",
  "Senate": "Council of Spheres",
  "Grand Moff Tarkin": "Director Valrok",
  "Boba Fett": "Kael Vorn",
  "Jabba the Hutt": "Graxul",
  "Clone Wars": "Synthesis Conflict"
}
```

## Этап 4: Замена терминов в текстах
- Python-скрипт для批量 замены по словарю
- Регистронезависимый поиск
- Сохранение логики и читаемости текстов

## Этап 5: Сохранение результатов
- Папка `knowledge_base/` - 30+ .md файлов
- Файл `terms_map.json` - словарь замен
- Краткое пояснение к базе

## Структура файлов после выполнения
```
knowledge_base/
  ├── xarn_velgor.md
  ├── void_core.md
  ├── synth_flux.md
  ├── lyris_talon.md
  └── ... (30+ файлов)
terms_map.json
```