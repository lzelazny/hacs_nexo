import logging
from .nexo_dimmer import NexoDimmer

_LOGGER = logging.getLogger(__name__)

class NexoLed(NexoDimmer):
    """
    LED w Nexo zachowuje się jak ściemniacz:
      - state: {"is_on": 0/1, "brightness": 0..255}
      - komendy takie same jak dla dimmera:
          operation=0 -> OFF
          operation=1 + brightness=<1..255> -> ON z poziomem
          operation=4 -> ON (ostatni poziom)
    Dziedziczymy wprost z NexoDimmer, żeby nie dublować logiki.
    """
    pass
