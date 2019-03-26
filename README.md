# Newsfeed-ner

Aгрегатор новостных лент за текущие сутки c распознаванием именованных сущностей в заголовках по следующим категориям:

* персоны
* локации
* организации

![Главная страница](../readme_images/main_page.png?raw=true)

![Облака слов](../readme_images/wordclouds.png?raw=true)

## Локальная установка

* первоначальная установка (с помощью `venv` в `python3`)
  
```bash
git clone https://github.com/ashatilov/newsfeed-ner
cd newsfeed-ner
python3 -m venv env
source ./env/bin/activate
pip install -U pip
pip install -r requirements.txt
```

* Установить PostgreSQL, далее создать базу данных PostgreSQL, указать ее в `settings.py`, ниже пример создания базы по умолчанию

```bash
sudo -u postgres psql
CREATE DATABASE newsfeed_db;
CREATE USER newsfeeduser WITH PASSWORD 'password';

ALTER ROLE newsfeeduser SET client_encoding TO 'utf8';
ALTER ROLE newsfeeduser SET default_transaction_isolation TO 'read committed';
ALTER ROLE newsfeeduser SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE newsfeed_db TO newsfeeduser;
\q
```

* скачать NER модель для `deeppavlov`

```bash
python -m deeppavlov install ner_rus
```

* применить migrations для django

```bash
python manage.py migrate
```

* с помощью этой команды можно обновить ленты, базу данных и облака слов

```bash
python manage.py populate_db
```

* запуск сервера локально, сайт будет доступен по адресу http://127.0.0.1:8000

```bash
python manage.py runserver
```
---
* добавить в `crontab` периодическое обновление базы данных (по умолчанию раз в 2 минуты - значение задается в `settings.py` в `CRONJOBS`) можно с помощью данной команды: 

```bash
python manage.py crontab add
```

* убрать из `crontab` периодическое обновление можно с помощью данной команды:

```bash
python manage.py crontab remove
```