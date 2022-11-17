from strategy.signals import save_stop_signal_db

def stop(message):
    """Handler for stop event type."""
    save_stop_signal_db(message)
    return "signal saved"