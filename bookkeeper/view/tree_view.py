"""
Модуль древообразного виджета
"""

from typing import Any
from collections import deque
from functools import partial
from inspect import get_annotations
from PySide6.QtWidgets import QWidget, QTreeView, QVBoxLayout, QMenu
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtCore import QModelIndex, Qt, QPoint, Signal
from bookkeeper.models.expense import Expense


class TreeView(QWidget):
    """
    Виджет для представления дерева данных
    """
    tree: QTreeView
    layout: QVBoxLayout
    model: QStandardItemModel
    fields: list[str]

    add_pressed: Signal = Signal()
    insert_up_pressed: Signal = Signal()
    insert_down_pressed: Signal = Signal()
    delete_pressed: Signal = Signal()

    def __init__(self, data: list[dict[str, Any]] | None = None) -> None:
        """
        Создает виджет дерева из списка словарей вида:
        [
        {'unique_id': int, 'parent_id': int, 'other_field': Any, ...},
        ]
        """
        super(TreeView, self).__init__()
        self.tree = QTreeView(self)
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.open_menu)
        self.model = QStandardItemModel()
        layout = QVBoxLayout(self)
        layout.addWidget(self.tree)
        self.setLayout(layout)
        names = get_annotations(Expense)
        names.pop('pk')
        self.fields = ['Name'] + list(names.keys())
        self.model.setHorizontalHeaderLabels(self.fields)
        self.tree.header().setDefaultSectionSize(90)
        self.tree.setModel(self.model)
        if data is not None:
            self.import_data(data)
        self.tree.expandAll()

    def import_data(self, data: list[dict[str, Any]]) -> None:
        """
        Обновляет содержание. Принимает список словарей вида:
        [
        {'unique_id': int, 'parent_id': int | None, 'other_field': Any, ...},
        ]
        :param data: список словарей
        """
        self.model.setRowCount(0)
        root = self.model.invisibleRootItem()
        seen = dict()
        values = deque(data)
        while values:
            value = values.popleft()
            if value['parent_id'] == 0:
                parent = root
            else:
                pid = value['parent_id']
                if pid not in seen:
                    values.append(value)
                    continue
                parent = seen[pid]
            names = [str(k) for k in list(value.keys())[2:]]
            row = [QStandardItem(str(value[name])) for name in names]
            parent.appendRow(row)
            seen[value['unique_id']] = parent.child(parent.rowCount() - 1)

    def get_children(self, item: QStandardItem, tree_list: list[dict[str, Any]], level: int = 0) -> None:
        """
        Добавляет все принадлежащие item элементы в виде словарей в tree_list.
        Формат элементов {'Name': str, }
        :param item: родительский элемент
        :param tree_list: список, куда сохранять
        :param level: уровень вложенности
        """
        if item is not None:
            if item.hasChildren():
                lvl = level + 1
                for i in range(item.rowCount()):
                    row = {field: ' ' for field in self.fields}
                    for j in reversed(range(item.columnCount())):
                        child = item.child(i, j)
                        if child is not None:
                            row[self.fields[j]] = child.data(0)
                        if j == 0:
                            row['level'] = str(lvl)
                            tree_list.append(row)
                        self.get_children(child, tree_list, lvl)

    def print_tree(self, item: QStandardItem = 0, level: int = 0) -> None:
        """
        Распечатать дерево с отступами, начиная с заданного элемента.
        :param item: корневой элемент, с которого начать печать
        :param level: глубина вложенности
        """
        if level == 0:
            if item == 0:
                item = self.model.invisibleRootItem()
                print('Tree structure from root:')
            else:
                print(f'Tree structure from {item.data(0)}')
        if item is not None:
            if item.hasChildren():
                lvl = level + 1
                for i in range(item.rowCount()):
                    row = ''
                    for j in reversed(range(item.columnCount())):
                        child = item.child(i, j)
                        if child is not None:
                            row = str(child.data(0)) + row
                        if j == 0:
                            row = '\t' * (lvl - 1) + row
                            print(row)
                        self.print_tree(child, lvl)

    def open_menu(self, position: QPoint) -> None:
        """
        Меню, вызываемое нажатием ПКМ. Подписать на сигнал выхова менб
        :param position: позиция курсора
        """
        indexes = self.sender().selectedIndexes()
        index_at = self.tree.indexAt(position)
        if not index_at.isValid():
            return
        item = self.model.itemFromIndex(index_at)
        if len(indexes) > 0:
            level = 0
            index = indexes[0]
            while index.parent().isValid():
                index = index.parent()
                level += 1
        else:
            level = 0
        right_click_menu = QMenu()
        act_add = right_click_menu.addAction(self.tr("Add Child Item"))
        act_add.triggered.connect(partial(self.add, level, index_at))
        if item.parent() is not None:
            insert_up = right_click_menu.addAction(self.tr("Insert Item Above"))
            insert_up.triggered.connect(partial(self.insert_up, level, index_at))
            insert_down = right_click_menu.addAction(self.tr("Insert Item Below"))
            insert_down.triggered.connect(partial(self.insert_down, level, index_at))
            act_del = right_click_menu.addAction(self.tr("Delete Item"))
            act_del.triggered.connect(partial(self.delete, item))
        right_click_menu.exec(self.sender().viewport().mapToGlobal(position))

    def add(self, level: int, index_at: QModelIndex, approved: bool = True) -> None:
        """
        Добавить по нажатию
        :param level:
        :param index_at:
        :param approved:
        """
        if approved:
            temp_data = [QStandardItem('xxx') for field in self.fields]
            self.model.itemFromIndex(index_at).appendRow(temp_data)
            self.tree.expandAll()
        else:
            print('add!')
            self.add_pressed.emit()

    def insert_up(self, level: int, index_at: QModelIndex, approved: bool = True) -> None:
        """
        Вставить сверху по нажатию
        :param level:
        :param index_at:
        :param approved:
        """
        if approved:
            level = level - 1
            current_row = self.model.itemFromIndex(index_at).row()
            temp_data = [QStandardItem('xxx') for field in self.fields]
            self.model.itemFromIndex(index_at).parent().insertRow(current_row, temp_data)
            self.tree.expandToDepth(1 + level)
        else:
            print('insert_up!')
            self.insert_up_pressed.emit()

    def insert_down(self, level: int, index_at: QModelIndex, approved: bool = True) -> None:
        """
        Вставить снизу по нажатию
        :param level:
        :param index_at:
        :param approved:
        """
        if approved:
            level = level - 1
            temp_data = [QStandardItem('xxx') for field in self.fields]
            current_row = self.model.itemFromIndex(index_at).row()
            self.model.itemFromIndex(index_at)\
                .parent().insertRow(current_row + 1, temp_data)
            self.tree.expandToDepth(1 + level)
        else:
            print('insert_down!')
            self.insert_down_pressed.emit()

    def delete(self, item: QStandardItem, approved: bool = True) -> None:
        """
        Удалить по нажатию
        :param item:
        :param approved:
        """
        if approved:
            item.parent().removeRow(item.row())
        else:
            print('delete!')
            self.delete_pressed.emit()
