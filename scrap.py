from spectre_core.receivers import get_receiver

test_receiver = get_receiver("test", mode="cosine-signal-1")
test_receiver.start_capture("tag1")
