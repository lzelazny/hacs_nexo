import logging
from .nexo_dimmer import NexoDimmer

_LOGGER = logging.getLogger(__name__)

class NexoGroupLed(NexoDimmer):
    """
    Grupa LED działa analogicznie do pojedynczego dimmera/LED:
    - ten sam format state i te same operacje.
    Dziedziczymy z NexoDimmer, bo API jest takie samo (po ID grupy).
    """
    pass
