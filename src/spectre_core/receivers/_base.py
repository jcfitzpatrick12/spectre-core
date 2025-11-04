# SPDX-FileCopyrightText: © 2024-2025 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

import typing
import logging

import watchdog.observers
import watchdog.events

import spectre_core.exceptions
import spectre_core.batches
import spectre_core.post_processing
import spectre_core.config

from ._flowgraph import BaseFlowgraph, BaseFlowgraphModel
from ._config import Config, read_config, write_config

_LOGGER = logging.getLogger(__name__)

T = typing.TypeVar("T")


class ReceiverComponents(typing.Generic[T]):
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
            raise spectre_core.exceptions.ModeNotFoundError(
                f"Mode `{mode}` not found. Expected one of {self.modes}"
            )
        return self._components[mode]


class Flowgraphs(
    ReceiverComponents[
        tuple[typing.Type[BaseFlowgraph], typing.Type[BaseFlowgraphModel]]
    ]
): ...


class EventHandlers(
    ReceiverComponents[
        tuple[
            typing.Type[spectre_core.post_processing.BaseEventHandler],
            typing.Type[spectre_core.post_processing.BaseEventHandlerModel],
        ]
    ]
): ...


class Batches(ReceiverComponents[typing.Type[spectre_core.batches.BaseBatch]]): ...


class BaseReceiver:
    """An abstraction layer for software-defined radio receivers."""

    def __init__(
        self,
        name: str,
        mode: typing.Optional[str] = None,
        flowgraphs: typing.Optional[Flowgraphs] = None,
        event_handlers: typing.Optional[EventHandlers] = None,
        batches: typing.Optional[Batches] = None,
    ) -> None:
        self._name = name
        self._mode = mode
        self._flowgraphs = flowgraphs or Flowgraphs()
        self._event_handlers = event_handlers or EventHandlers()
        self._batches = batches or Batches()

    @property
    def name(self) -> str:
        """Retrieve the name of the receiver."""
        return self._name

    @property
    def mode(self) -> typing.Optional[str]:
        """Retrieve the operating mode."""
        return self._mode

    @mode.setter
    def mode(self, value: str) -> None:
        """Set the operating mode.

        :param value: The new operating mode of the receiver. Use `None` to unset the mode.
        """
        if value not in self.modes:
            raise spectre_core.exceptions.ModeNotFoundError(
                f"Mode `{value}` not found. Expected one of {self.modes}"
            )
        self._mode = value

    @property
    def modes(self) -> list[str]:
        """The operating modes for the receiver.

        :raises ValueError: If the modes are inconsistent.
        """
        if (
            not self._flowgraphs.modes
            == self._event_handlers.modes
            == self._batches.modes
        ):
            raise ValueError(f"Inconsistent modes for the receiver '{self.name}'")
        return self._flowgraphs.modes

    @property
    def active_mode(self) -> str:
        """Retrieve the active operating mode, raising an error if not set.

        :raises ValueError: If no mode is currently set.
        :return: The active operating mode.
        """
        if self._mode is None:
            raise ValueError(
                f"An active mode is not set for the receiver '{self.name}'. "
                f"Currently, the mode is {self._mode}"
            )
        return self._mode

    @property
    def flowgraph(
        self,
    ) -> tuple[typing.Type[BaseFlowgraph], typing.Type[BaseFlowgraphModel]]:
        return self._flowgraphs.get(self.active_mode)

    @property
    def event_handler(
        self,
    ) -> tuple[
        typing.Type[spectre_core.post_processing.BaseEventHandler],
        typing.Type[spectre_core.post_processing.BaseEventHandlerModel],
    ]:
        return self._event_handlers.get(self.active_mode)

    @property
    def batch(self) -> typing.Type[spectre_core.batches.BaseBatch]:
        return self._batches.get(self.active_mode)

    def validate(self, parameters: dict[str, str]) -> dict[str, typing.Any]:

        # Validate the flowgraph parameters
        _, flowgraph_model_cls = self.flowgraph
        flowgraph_params = flowgraph_model_cls.model_validate(parameters).model_dump()

        # Validate event handler parameters
        _, event_handler_model_cls = self.event_handler
        event_handler_params = event_handler_model_cls.model_validate(
            flowgraph_params
        ).model_dump()

        # Merge the two (the event handler parameters take precedence)
        return {**flowgraph_params, **event_handler_params}

    def read_config(
        self, tag: str, configs_dir_path: typing.Optional[str] = None
    ) -> Config:
        configs_dir_path = (
            configs_dir_path or spectre_core.config.paths.get_configs_dir_path()
        )
        return read_config(tag, configs_dir_path)

    def write_config(
        self,
        tag: str,
        parameters: dict[str, str],
        configs_dir_path: typing.Optional[str] = None,
    ) -> None:
        write_config(
            tag,
            self.name,
            self.active_mode,
            self.validate(parameters),
            configs_dir_path,
        )

    def activate_flowgraph(
        self, config: Config, batches_dir_path: typing.Optional[str] = None
    ) -> None:
        parameters = self.validate(config.parameters)
        flowgraph_cls, _ = self.flowgraph
        flowgraph_cls(
            config.tag, batches_dir_path=batches_dir_path, **parameters
        ).activate()

    def activate_post_processing(
        self, config: Config, batches_dir_path: typing.Optional[str] = None
    ) -> None:

        batches_dir_path = (
            batches_dir_path or spectre_core.config.paths.get_batches_dir_path()
        )
        observer = watchdog.observers.Observer()

        parameters = self.validate(config.parameters)
        event_handler_cls, _ = self.event_handler
        observer.schedule(
            event_handler_cls(config.tag, **parameters),
            batches_dir_path,
            recursive=True,
            event_filter=[watchdog.events.FileCreatedEvent],
        )

        try:
            _LOGGER.info("Starting the post processing thread...")
            observer.start()
            observer.join()
        except KeyboardInterrupt:
            _LOGGER.warning(
                (
                    "Keyboard interrupt detected. Signalling "
                    "the post processing thread to stop"
                )
            )
            observer.stop()
            _LOGGER.warning(("Post processing thread has been successfully stopped"))

    def add_mode(
        self,
        mode: str,
        flowgraph: tuple[typing.Type[BaseFlowgraph], typing.Type[BaseFlowgraphModel]],
        event_handler: tuple[
            typing.Type[spectre_core.post_processing.BaseEventHandler],
            typing.Type[spectre_core.post_processing.BaseEventHandlerModel],
        ],
        batch: typing.Type[spectre_core.batches.BaseBatch],
    ) -> None:
        self._flowgraphs.add(mode, flowgraph)
        self._event_handlers.add(mode, event_handler)
        self._batches.add(mode, batch)
