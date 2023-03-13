"""
Модуль древообразного виджета
"""

import sys
from collections import deque
from PySide6.QtWidgets import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from inspect import get_annotations
from bookkeeper.repository.sqlite_repository import SQLiteRepository
from bookkeeper.models.category import Category
from bookkeeper.models.expense import Expense
from bookkeeper.utils import read_tree


class TreeView(QWidget):
    """
    Виджет для представления дерева данных
    """
    tree: QTreeView
    layout: QVBoxLayout
    model: QStandardItemModel
    fields: list[str]

    def __init__(self, data):
        """
        Создает виджет дерева из списка словарей вида:
        [
        {'unique_id': int, 'parent_id': int, 'other_field': Any, ...},
        ]
        """
        super(TreeView, self).__init__()
        self.tree = QTreeView(self)
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.tree)
        self.model = QStandardItemModel()
        names = get_annotations(Expense)
        names.pop('pk')
        self.fields = ['Name'] + list(names.keys())
        self.model.setHorizontalHeaderLabels(self.fields)
        self.tree.header().setDefaultSectionSize(90)
        self.tree.setModel(self.model)
        self.import_data(data)
        self.tree.expandAll()
        self.print_tree()

    def import_data(self, data) -> None:
        """
        Обновляет содержание. Принимает список словарей вида:
        [
        {'unique_id': int, 'parent_id': int | None, 'other_field': Any, ...},
        ]
        :param data: список словарей
        """
        self.model.setRowCount(0)
        root = self.model.invisibleRootItem()
        seen = {}  # List of  QStandardItem
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
            unique_id = value['unique_id']
            parent.appendRow([
                QStandardItem(value['short_name']),
                # QStandardItem(value['height']),
                # StandardItem(value['weight'])
            ])
            seen[unique_id] = parent.child(parent.rowCount() - 1)

    def get_children(self, item: QStandardItem, tree_list: list, level: int = 0) -> None:
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
                            row['level'] = lvl
                            tree_list.append(row)
                        self.get_children(child, tree_list, lvl)

    def print_tree(self, item: QStandardItem = 0, level: int = 0):
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
                            row = '\t'*(lvl-1) + row
                            print(row)
                        self.print_tree(child, lvl)


if __name__ == '__main__':
    cat_repo = SQLiteRepository[Category]('test.db', Category)
    cats = '''
    продукты
        мясо
            сырое мясо
            мясные продукты
        сладости
    книги
    одежда
    '''.splitlines()
    Category.create_from_tree(read_tree(cats), cat_repo)

    tree_data = [
        {'unique_id': cat.pk,
         'parent_id': cat.parent if cat.parent is not None else 0,
         'short_name': cat.name}
        for cat in cat_repo.get_all()
    ]
    app = QApplication(sys.argv)
    view = TreeView(tree_data)
    view.setGeometry(300, 100, 600, 300)
    view.setWindowTitle('QTreeview Example')
    view.show()
    sys.exit(app.exec())
