# SPDX-FileCopyrightText: © 2024-2025 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from typing import Callable, Optional, TypeVar, Generic, Any

from spectre_core.exceptions import ModeNotFoundError
from spectre_core.capture_configs import CaptureTemplate, Parameters, CaptureConfig
from .plugins._receiver_names import ReceiverName
from ._specs import Specs, SpecName

T = TypeVar("T")


class ReceiverComponents(Generic[T]):
    """Base class for managing receiver components per operating mode."""

    def __init__(self) -> None:
        """Initialise an instance of `ReceiverComponents`."""
        self._components: dict[str, T] = {}

    @property
    def modes(self) -> list[str]:
        """Get all the added operating modes."""
        return list(self._components.keys())

    def add(self, mode: str, component: T) -> None:
        """Add a component for a particular operating mode.

        :param mode: The operating mode for the receiver.
        :param component: The component associated with this mode.
        """
        self._components[mode] = component

    def get(self, mode: str) -> T:
        """Retrieve the component for a particular operating mode.

        :param mode: The operating mode for the receiver.
        :return: The component associated with this mode.
        :raises ModeNotFoundError: If the mode is not found.
        """
        if mode not in self._components:
            raise ModeNotFoundError(
                f"Mode `{mode}` not found. Expected one of {self._components}"
            )
        return self._components[mode]


class CaptureMethods(ReceiverComponents[Callable[[str, Parameters], None]]):
    """Per operating mode, define how the receiver captures data."""


class CaptureTemplates(ReceiverComponents[CaptureTemplate]):
    """Per operating mode, define what parameters are required in a capture config, and the values each parameter can take."""


class PValidators(ReceiverComponents[Callable[[Parameters], None]]):
    """Validate capture config parameters en groupe, per operating mode."""


def default_pvalidator(parameters: Parameters) -> None:
    """A noop parameter validator. Doesn't check anything at all."""


class Receiver:
    """An abstraction layer for software-defined radio receivers."""

    def __init__(
        self,
        name: ReceiverName,
        mode: Optional[str] = None,
        specs: Optional[Specs] = None,
        capture_methods: Optional[CaptureMethods] = None,
        capture_templates: Optional[CaptureTemplates] = None,
        pvalidators: Optional[PValidators] = None,
    ) -> None:
        """Initialise a receiver instance.

        :param name: The name of the receiver.
        :param capture_methods: Defines how the receiver captures data per mode.
        :param capture_templates: Defines required parameters per mode.
        :param pvalidators: Defines parameter validation functions per mode.
        :param specs: Hardware specifications for the receiver.
        :param mode: The initial active operating mode. Defaults to None.
        """
        self._name = name
        self._mode = mode
        self._specs = specs or Specs()
        self._capture_methods = capture_methods or CaptureMethods()
        self._capture_templates = capture_templates or CaptureTemplates()
        self._pvalidators = pvalidators or PValidators()

    @property
    def name(self) -> ReceiverName:
        """Retrieve the receiver's name."""
        return self._name

    @property
    def mode(self) -> Optional[str]:
        """Retrieve the operating mode."""
        return self._mode

    @mode.setter
    def mode(self, value: str) -> None:
        """Set the operating mode.

        :param value: The new operating mode of the receiver. Use `None` to unset the mode.
        """
        if value not in self.modes:
            raise ModeNotFoundError(
                f"Mode `{value}` not found. Expected one of {self.modes}"
            )
        self._mode = value

    @property
    def modes(self) -> list[str]:
        """The operating modes for the receiver.

        :raises ValueError: If the modes are inconsistent.
        """
        if (
            not self._capture_methods.modes
            == self._pvalidators.modes
            == self._capture_templates.modes
        ):
            raise ValueError(f"Modes are inconsistent for the receiver {self.name}.")
        return self._capture_methods.modes

    @property
    def active_mode(self) -> str:
        """Retrieve the active operating mode, raising an error if not set.

        :raises ValueError: If no mode is currently set.
        :return: The active operating mode.
        """
        if self._mode is None:
            raise ValueError(
                f"An active mode is not set for the receiver `{self.name.value}`. Currently, the mode is {self._mode}"
            )
        return self._mode

    @property
    def capture_method(self) -> Callable[[str, Parameters], None]:
        """Retrieve the capture method for the active operating mode."""
        return self._capture_methods.get(self.active_mode)

    @property
    def capture_template(self) -> CaptureTemplate:
        """Retrieve the capture template for the active operating mode."""
        return self._capture_templates.get(self.active_mode)

    @property
    def pvalidator(self) -> Callable[[Parameters], None]:
        """Retrieve the parameter validator for the active operating mode."""
        return self._pvalidators.get(self.active_mode)

    @property
    def specs(self) -> dict[SpecName, Any]:
        """Retrieve all hardware specifications.

        :return: A dictionary of all specifications.
        """
        return self._specs.all()

    def start_capture(self, tag: str, validate: bool = True) -> None:
        """Start capturing data using the active operating mode.

        :param tag: The tag identifying the capture config.
        :param validate: If True, validate the capture config. Defaults to False.
        :raises ValueError: If no mode is currently set.
        """
        self.capture_method(tag, self.load_parameters(tag, validate))

    def save_parameters(
        self,
        tag: str,
        parameters: Parameters,
        force: bool = False,
        validate: bool = True,
    ) -> None:
        """Save parameters to a capture config.

        :param tag: The tag identifying the capture config.
        :param parameters: The parameters to save.
        :param force: If True, overwrite existing configuration if it exists.
        :param validate: If True, validate capture config parameters.
        :raises ValueError: If no mode is currently set.
        """
        parameters = self.capture_template.apply_template(
            parameters, apply_pconstraints=validate
        )

        if validate:
            self.pvalidator(parameters)

        capture_config = CaptureConfig(tag)
        capture_config.save_parameters(
            self.name.value, self.active_mode, parameters, force
        )

    def load_parameters(self, tag: str, validate: bool = True) -> Parameters:
        """Load parameters from a capture config.

        :param tag: The tag identifying the capture config.
        :param validate: If True, validate capture config parameters.
        :raises ValueError: If no mode is currently set.
        :return: The validated parameters stored in the configuration.
        """
        capture_config = CaptureConfig(tag)

        parameters = self.capture_template.apply_template(
            capture_config.parameters, apply_pconstraints=validate
        )

        if validate:
            self.pvalidator(parameters)

        return parameters

    def add_mode(
        self,
        mode: str,
        capture_method: Callable[[str, Parameters], None],
        capture_template: CaptureTemplate,
        pvalidator: Callable[[Parameters], None] = default_pvalidator,
    ) -> None:
        """Add a new mode to the receiver.

        :param mode: The name of the new mode.
        :param capture_method: Define how data is captured in this mode.
        :param capture_template: Define what parameters are required in a capture config, and the values each parameter can take.
        :param pvalidator: The function to validate parameters for this mode, as a group.
        """
        self._capture_methods.add(mode, capture_method)
        self._capture_templates.add(mode, capture_template)
        self._pvalidators.add(mode, pvalidator)

    def add_spec(self, name: SpecName, value: Any) -> None:
        """Add a hardware specification.

        :param name: The specification's name.
        :param value: The specification's value.
        """
        self._specs.add(name, value)

    def get_spec(self, name: SpecName) -> Any:
        """Retrieve a specific hardware specification.

        :param name: The specification's name.
        :return: The specification's value.
        """
        return self._specs.get(name)
