import logging
from .nexo_output import NexoOutput

_LOGGER = logging.getLogger(__name__)

class NexoGroupOutput(NexoOutput):
    """
    Grupa wyjść jako przełącznik (switch).
    API takie samo jak dla pojedynczego output:
      - state: {"is_on": 0/1}
      - operation=1 -> ON, operation=0 -> OFF
    Dziedziczymy z NexoOutput.
    """
    pass
