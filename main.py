from gui.gui import run_gui
from config import configure_logging


def main():
    configure_logging()
    run_gui()


if __name__ == "__main__":
    main()
