import logging, os
logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.DEBUG)
log = logging.getLogger('scheduler')


PYTHONPATH = os.environ.get('PYTHONPATH', os.getcwd())
PYTHON_EXEC =  os.environ.get('PYTHON_EXEC', '<python_exec>')
