"""
Модуль описывает репозиторий, использующий базу данных, с использованием sqlite3
"""

from typing import Any
import sqlite3
from inspect import get_annotations
from bookkeeper.repository.abstract_repository import AbstractRepository, T


class SQLiteRepository(AbstractRepository[T]):
    """
    Репозиторий, работающий в sqlite. Для корректной работы классы моделей
    ДОЛЖНЫ иметь конструктор по умолчанию.
    """

    db_file: str
    cls: type
    table_name: str
    fields: dict[str, Any]

    def __init__(self, db_file: str, cls: type) -> None:
        """
        Создает репозиторий в файле с указанным названием для хранения
        данных указанного типа.
        Рекомендуется использовать один файл для одного проекта.
        :param db_file: название файла репозитория
        :param cls: класс данных для хранения (необходим конструктор по умолчанию!!!)
        """
        self.db_file = db_file
        self.cls = cls
        self.table_name = self.cls.__name__
        self.fields = get_annotations(cls, eval_str=True)
        self.fields.pop('pk')

        keys = [str(k) for k in list(self.fields.keys())]
        vals = [str(v) for v in list(self.fields.values())]

        def type_check(val: str) -> str:
            if val.find('int') != -1:
                return 'INTEGER'
            else:
                return 'TEXT'

        vals = [type_check(v) for v in vals]
        names = [str(k) + ' ' + str(v) for (k, v) in zip(keys, vals)]
        names = names + ['pk INTEGER PRIMARY KEY']
        names = ', '.join(names)
        with sqlite3.connect(self.db_file) as con:
            cur = con.cursor()
            cur.execute(f'DROP TABLE IF EXISTS {self.table_name}')
            cur.execute(f'CREATE TABLE IF NOT EXISTS {self.table_name} ({names})')
        con.close()

    def add(self, obj: T) -> int:
        """
        Добавить объект в репозиторий. Возвращает его уникальный номер.
        :param obj: добавляемый объект
        :return: уникальный номер объекта в репозитории
        """
        if getattr(obj, 'pk', None) != 0:
            raise ValueError(f'trying to add object {obj} with filled `pk` attribute')
        names = ', '.join(self.fields.keys())
        placeholders = ', '.join("?" * len(self.fields))
        values = tuple(getattr(obj, x) for x in self.fields.keys())
        with sqlite3.connect(self.db_file) as con:
            cur = con.cursor()
            cur.execute(
                f'INSERT INTO {self.table_name} ({names}) VALUES ({placeholders})', values
            )
            obj.pk = cur.lastrowid
        con.close()
        return obj.pk

    def get(self, pk: int) -> T | None:
        """
        Получить объект из репозитория по его уникальному номеру.
        :param pk: номер объекта в репозитории
        :return: объект из репозитория
        """
        with sqlite3.connect(self.db_file) as con:
            cur = con.cursor()
            cur.execute('PRAGMA foreign_keys = ON')
            cur.execute(
                f'SELECT * FROM {self.table_name} WHERE pk = {pk}'
            )
            tuple_obj = cur.fetchone()
        con.close()
        if tuple_obj is None:
            return None
        tuple_obj = tuple(t if t is not None else None for t in tuple_obj)
        names = (*[str(k) for k in self.fields.keys()], 'pk')
        obj = self.cls()
        for i in range(len(names)):
            setattr(obj, names[i], tuple_obj[i])
        return obj

    def get_all(self, where: dict[str, Any] | None = None) -> list[T]:
        """
        Получить все объекты из таблицы репозитория с определенными значениями полей.
        :return:
        :param where: словарь вида {'название атрибута': значение}
        :return: список объектов
        """
        with sqlite3.connect(self.db_file) as con:
            cur = con.cursor()
            cur.execute('PRAGMA foreign_keys = ON')
            cur.execute(
                f'SELECT * FROM {self.table_name}'
            )
            tuple_objs = cur.fetchall()
        con.close()
        objs = []
        names = (*[str(k) for k in self.fields.keys()], 'pk')
        for tuple_obj in tuple_objs:
            obj = self.cls()
            for i in range(len(names)):
                setattr(obj, names[i], tuple_obj[i])
            objs.append(obj)
        if where is None:
            return objs
        objs = [
            obj for obj in objs if all(
                getattr(obj, attr) == where[attr] for attr in where.keys()
            )
        ]
        return objs

    def update(self, obj: T) -> None:
        """
        Изменить объект в репозитории.
        :param obj: измененный объект (необходимо указать pk)
        """
        if obj.pk == 0:
            raise ValueError('attempt to update object with unknown primary key')
        names = list(self.fields.keys())
        sets = ', '.join(f'{name} = \'{getattr(obj, name)}\'' for name in names)
        with sqlite3.connect(self.db_file) as con:
            cur = con.cursor()
            cur.execute('PRAGMA foreign_keys = ON')
            cur.execute(
                f'UPDATE {self.table_name} SET {sets} WHERE pk = {obj.pk}'
            )
        con.close()

    def delete(self, pk: int) -> None:
        """
        Удалить объект из репозитория по его уникальному номеру.
        :param pk: уникальный номер объекта в репозитории
        """
        if self.get(pk) is None:
            raise KeyError
        with sqlite3.connect(self.db_file) as con:
            cur = con.cursor()
            cur.execute('PRAGMA foreign_keys = ON')
            cur.execute(
                f'DELETE FROM {self.table_name} WHERE pk = {pk}'
            )
        con.close()
