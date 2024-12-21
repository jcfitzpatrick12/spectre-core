from spectre_core.receivers.factory import get_receiver
from spectre_core.parameters import make_parameters, parse_string_parameters

test_receiver = get_receiver("test",
                             "cosine-signal-1")

string_params = ["watch_extension=bins", "sample_rate=128000", "frequency=64000"]

params = make_parameters ( parse_string_parameters(string_params) )
test_receiver.save_parameters("my-tag",
                              params,
                              force=True)