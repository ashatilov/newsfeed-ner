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
pip install -U pip
pip install -r requirements.txt
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