from spectre_core.receivers.factory import get_receiver
from spectre_core.parameters import make_parameters, parse_string_parameters
from spectre_core.capture_config import CaptureConfig


tag           = "my-tag"
string_params = []
receiver_name = "test"
receiver_mode = "tagged-staircase"

test_receiver = get_receiver(receiver_name, 
                             receiver_mode)
params = make_parameters ( parse_string_parameters(string_params) )
test_receiver.save_parameters(tag,
                              params,
                              force=True)

capture_config = CaptureConfig(tag)
for parameter in capture_config.parameters:
    print(f"{parameter.name}: {parameter.value} ({type(parameter.value)})")