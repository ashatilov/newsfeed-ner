# Newsfeed-ner

Aгрегатор новостных лент за текущие сутки c распознаванием именованных сущностей в заголовках по следующим категориям:

* персоны
* локации
* организации

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

* создать базу данных PostgreSQL, указать ее в `settings.py`, ниже база по умолчанию

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

```python
python -m deeppavlov install ner_rus
```

* с помощью этой команды можно обновить ленты, базу данных и облака слов

```python
python manage.py populate_db
```

* добавить в `crontab` периодическое обновление базы данных (по умолчанию раз в 2 минуты - можно изменить в `settings.py` с помощью CRONJOBS)

```python
python manage.py crontab add
```

* убрать из crontab периодическое обновление

```python
python manage.py crontab remove
```

* запуск сервера локально, сайт доступен по адресу http://127.0.0.1:8000

```python
python manage.py runserver
```