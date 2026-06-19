def subscribe(event_type):
    def wrapper(func):
        func._event_type = event_type
        return func

    return wrapper