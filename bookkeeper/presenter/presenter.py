import sys
from functools import partial
from bookkeeper.models.category import Category
from bookkeeper.models.expense import Expense
from bookkeeper.repository.sqlite_repository import SQLiteRepository
from bookkeeper.view.tree_view import TreeView
from bookkeeper.utils import read_tree
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout


class Presenter:
    exp_repo: SQLiteRepository
    cat_repo: SQLiteRepository
    tree_widget: TreeView

    def __init__(self) -> None:
        self.exp_repo = SQLiteRepository('main.db', Expense)
        self.cat_repo = SQLiteRepository('main.db', Category)

        cats = '''
        продукты
            мясо
                сырое мясо
                мясные продукты
            сладости
        книги
        одежда
        '''.splitlines()
        Category.create_from_tree(read_tree(cats), self.cat_repo)

        tree_data = [
            {'unique_id': cat.pk,
             'parent_id': cat.parent if cat.parent is not None else 0,
             'short_name': cat.name}
            for cat in self.cat_repo.get_all()
        ]

        self.tree_widget = TreeView(tree_data)
        self.tree_widget.setGeometry(300, 100, 600, 300)
        self.tree_widget.setWindowTitle('Simple Finance App')






