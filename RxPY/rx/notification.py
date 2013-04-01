import types

from rx import Observable
from rx.concurrency import ImmediateScheduler

from .observer import Observer
from .anonymousobservable import AnonymousObservable

# Notifications
class Notification(object):
    """Represents a notification to an observer."""

    def __init__(self):
        """Default constructor used by derived types."""
        self.has_value = False
    
    def accept(self, on_next, on_error=None, on_completed=None):
        """Invokes the delegate corresponding to the notification or an 
        observer and returns the produced result. 
        
        1 - notification.accept(observer)
        2 - notification.accept(on_next, on_error, on_completed)
        
        Keyword arguments:
        on_next -- Delegate to invoke for an OnNext notification.
        on_error -- [Optional] Delegate to invoke for an OnError notification.
        on_completed -- [Optional] Delegate to invoke for an OnCompleted notification.
        
        Returns result produced by the observation.
        """
        if isinstance(on_next, Observer):
            return self._accept_observable(on_next)
        else:
            return self._accept(on_next, on_error, on_completed)
            
    def to_observable(self, scheduler=None):
        """Returns an observable sequence with a single notification, using the
        specified scheduler, else the immediate scheduler. 

        Keyword arguments:
        scheduler -- [Optional] Scheduler to send out the notification calls on.
        
        Returnes an observable sequence that surfaces the behavior of the 
        notification upon subscription.
        """
        notification = self
        scheduler = scheduler or ImmediateScheduler()

        def subscribe(observer):
            def action(scheduler, state):
                notification._accept_observable(observer)
                if notification.kind == 'N':
                    observer.on_completed()
                
            return scheduler.schedule(action)
        return AnonymousObservable(subscribe)

    @classmethod
    def observable_from_notifier(cls, handler):
        """Creates an observer from a notification callback.
        
        Keyword arguments:
        handler -- Action that handles a notification.
        
        Returns the observer object that invokes the specified handler using a 
        notification corresponding to each message it receives.
        """
        
        def _on_next(value):
            return handler(ON(value))
        def _on_error(ex):
            return handler(OE(ex))
        def _on_completed():
            return handler(OC())

        return Observable(_on_next, _on_error, _on_completed)

    def equals(self, other):
        """Indicates whether this instance and a specified object are equal."""
        other_string = '' if not other else str(other)
        return str(self) == other_string

    def __eq__(self, other):
        return self.equals(other)
    
class ON(Notification):
    """Represents an OnNext notification to an observer."""
    def __init__(self, value):
        """Constructs a notification of a new value."""
        self.value = value
        self.has_value = True
        self.kind = 'N'

    def _accept(self, on_next, on_error=None, on_completed=None):
        return on_next(self.value)
    
    def _accept_observable(self, observer):
        return observer.on_next(self.value)
    
    def __str__(self):
        return "OnNext(%s)" % self.value
    
class OE(Notification):
    """Represents an OnError notification to an observer."""

    def __init__(self, exception):
        """Constructs a notification of an exception."""
        self.exception = exception
        self.kind = 'E'

    def _accept(self, on_next, on_error):
        return on_error(self.exception)
    
    def _accept_observable(self, observer):
        return observer.on_error(self.exception)
    
    def __str__(self):
        return "OnError(%s)" % self.exception

class OC(Notification):
    """Represents an OnCompleted notification to an observer."""

    def __init__(self):
        """Constructs a notification of the end of a sequence."""
        self.kind = 'C'

    def _accept(self, on_next, on_error, on_completed):
        return on_completed()
    
    def _accept_observable(self, observer):
        return observer.on_completed()
    
    def __str__(self):
        return "OnCompleted()"

# Stiched here to avoid circular dependencies in import chain
Observable.from_notifier = Notification.observable_from_notifier