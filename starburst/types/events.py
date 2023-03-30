import time
from enum import Enum

from starburst.types.job import Job


class EventTypes(Enum):
    """ Event types. """
    MISC = 0
    SCHED_TICK = 1
    JOB_ADD = 2

class BaseEvent:
    """ Basic event abstraction. """

    def __init__(self,
                 timestamp: float = None,
                 event_type: EventTypes = EventTypes.MISC):
        """
        Base event.
        :param timestamp: When the event was created (float)
        :param event_type: Enum of EventTypes
        """
        if timestamp is None:
            timestamp = time.time()
        self.timestamp = timestamp
        self.event_type = event_type

    def __repr__(self):
        return f"BaseEvent, type:{self.event_type}"


class SchedTick(BaseEvent):
    """ Scheduler tick event """

    def __init__(self,
                 timestamp: float = None,
                 event_type: EventTypes = EventTypes.SCHED_TICK):
        super().__init__(timestamp, event_type)

    def __repr__(self):
        return f"Sched Tick, type:{self.event_type}"

class JobAddEvent(BaseEvent):
    """ JobAddEvent """

    def __init__(self,
                 job: Job = None,
                 timestamp: float = None,
                 event_type: EventTypes = EventTypes.JOB_ADD):
        self.job = job
        super().__init__(timestamp, event_type)

    def __repr__(self):
        """ representation. """
        return f"JobAddEvent: {self.job}"
