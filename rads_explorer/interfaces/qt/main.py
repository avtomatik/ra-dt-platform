import sys

from PySide6.QtWidgets import QApplication

from rads_explorer.container.container import get_container
from rads_explorer.interfaces.qt.main_window import MainWindow


def main():
    app = QApplication(sys.argv)

    container = get_container()
    certificate_service = container.certificate_service()

    window = MainWindow(certificate_service)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
