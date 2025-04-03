import threading
import logging

class ThreadManager:
    def __init__(self):
        self.threads = []  # List of (thread, stop_event) tuples
    
    def start_thread(self, target, *args, **kwargs):
        """Start a daemon thread with clean shutdown capability."""
        stop_event = threading.Event()
        
        def wrapped_target():
            try:
                target(stop_event, *args, **kwargs)
            except Exception as e:
                logging.error(f"Thread crash: {str(e)}")
        
        thread = threading.Thread(
            target=wrapped_target,
            daemon=True
        )
        thread.start()
        self.threads.append((thread, stop_event))
        return thread

    def stop_all(self):
        current = threading.current_thread()
        for t, stop_event in self.threads:
            stop_event.set()
        for t, stop_event in self.threads:
            if t is not current:
                t.join(0.5)
        self.threads = []
