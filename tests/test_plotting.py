# SPDX-FileCopyrightText: © 2024-2025 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

import pytest
import numpy as np
from datetime import datetime, timedelta
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from copy import deepcopy

from spectre_core.plotting import (
    BasePanel,
    XAxisType,
    PanelName,
    SpectrogramPanel,
    BaseTimeSeriesPanel,
    FrequencyCutsPanel,
    TimeCutsPanel,
    IntegralOverFrequencyPanel,
    PanelStack,
    PanelFormat,
)
from spectre_core.config import TimeFormat
from spectre_core.spectrograms import Spectrogram, SpectrumUnit, TimeType


@pytest.fixture(autouse=True)
def setup_random_seed():
    """Set fixed random seed for all tests in this module."""
    # Arbitrarily chosen random seed.
    np.random.seed(42)


@pytest.fixture
def figure() -> Figure:
    return Figure()


@pytest.fixture
def axes(figure: Figure) -> Axes:
    return Axes(figure, [0.1, 0.1, 0.8, 0.8])


# An arbitrary datetime to assign to the first spectrum in the spectrogram fixture.
_ARBITRARY_DATETIME = datetime(2025, 2, 13, 6, 0, 0)


@pytest.fixture
def spectrogram() -> Spectrogram:
    """Create a spectrogram, using random values for the spectral components.

    This is used to instantiate some panels.
    """
    num_spectrums = 20
    num_spectral_components = 64

    # Populate the dynamic spectra with some random values.
    dynamic_spectra = np.random.uniform(
        -1, 1, (num_spectral_components, num_spectrums)
    ).astype(np.float32)
    # Arbitrarily, consider `num_spectrums` spectrums over an interval of 10 [s]
    times = np.linspace(0, 10, num_spectrums).astype(np.float32)
    # Arbitrarily, consider `num_spectral_components` spectral components, over the FM band
    frequencies = np.linspace(90e6, 110e6, num_spectral_components).astype(np.float32)
    # Arbitrarily, assign some date to be the datetime corresponding to the first spectrum.
    start_datetime = _ARBITRARY_DATETIME
    # Arbitrarily, set the unit (the plotting module does not care about this)
    spectrum_unit = SpectrumUnit.AMPLITUDE
    # Create a mock tag.
    tag = f"mock-{spectrum_unit.value}-spectrogram"
    return Spectrogram(
        dynamic_spectra, times, frequencies, tag, spectrum_unit, start_datetime
    )


@pytest.fixture
def base_panel(spectrogram: Spectrogram) -> BasePanel:
    """Arbitrarily create an instance of any `BasePanel` subclass, to test functionality of `BasePanel`."""
    return SpectrogramPanel(spectrogram)


@pytest.fixture
def base_time_series_panel(spectrogram: Spectrogram) -> BaseTimeSeriesPanel:
    """Arbitrarily create an instance of any `BaseTimeSeriesPanel` subclass, to test functionality of `BaseTimeSeriesPanel`."""
    return SpectrogramPanel(spectrogram)


@pytest.fixture
def frequency_cuts_panel_relative_cuts(spectrogram: Spectrogram) -> FrequencyCutsPanel:
    """A frequency cuts panel, with cuts indicated by relative times, using default keyword arguments."""
    return FrequencyCutsPanel(spectrogram, 0.0, 1.0)


@pytest.fixture
def frequency_cuts_panel_datetime_cuts(spectrogram: Spectrogram) -> FrequencyCutsPanel:
    """A frequency cuts panel, with cuts indicated by datetimes, using default keyword arguments."""
    cuts = [
        datetime.strftime(_ARBITRARY_DATETIME, TimeFormat.DATETIME),
        datetime.strftime(_ARBITRARY_DATETIME + timedelta(1), TimeFormat.DATETIME),
    ]
    return FrequencyCutsPanel(spectrogram, *cuts)


@pytest.fixture
def frequency_cuts_panel_dBb(spectrogram: Spectrogram) -> FrequencyCutsPanel:
    """A frequency cuts panel, whose spectrums are in units of decibels above the background."""
    return FrequencyCutsPanel(spectrogram, 0.0, 1.0, dBb=True)


@pytest.fixture
def frequency_cuts_panel_peak_normalised(
    spectrogram: Spectrogram,
) -> FrequencyCutsPanel:
    """A frequency cuts panel, whose spectrums are in units normalised to the peak values, respectively."""
    return FrequencyCutsPanel(spectrogram, 0.0, 1.0, peak_normalise=True)


@pytest.fixture
def time_cuts_panel(spectrogram: Spectrogram) -> TimeCutsPanel:
    """A time cuts panel, using the default keyword arguments."""
    return TimeCutsPanel(spectrogram, 90e6, 90.3e6)


@pytest.fixture
def time_cuts_panel_dBb(spectrogram: Spectrogram) -> TimeCutsPanel:
    """A time cuts panel, whose spectrums are in units of decibels above the background."""
    return TimeCutsPanel(spectrogram, 90e6, 90.3e6, dBb=True)


@pytest.fixture
def time_cuts_panel_peak_normalised(spectrogram: Spectrogram) -> TimeCutsPanel:
    """A time cuts panel, whose spectrums are in units normalised to the peak values, respectively.."""
    return TimeCutsPanel(spectrogram, 90e6, 90.3e6, peak_normalise=True)


@pytest.fixture
def integral_over_frequency_panel(
    spectrogram: Spectrogram,
) -> IntegralOverFrequencyPanel:
    """A panel plotting the integral of the spectrogram over frequency, using default system arguments."""
    return IntegralOverFrequencyPanel(spectrogram)


@pytest.fixture
def spectrogram_panel(spectrogram: Spectrogram) -> SpectrogramPanel:
    """A spectrogram panel using default keyword arguments."""
    return SpectrogramPanel(spectrogram)


@pytest.fixture
def spectrogram_panel_dBb(spectrogram: Spectrogram) -> SpectrogramPanel:
    """A spectrogram panel with dBb visualization."""
    return SpectrogramPanel(spectrogram, dBb=True)


@pytest.fixture
def spectrogram_panel_log_norm(spectrogram: Spectrogram) -> SpectrogramPanel:
    """A spectrogram panel with logarithmic normalization."""
    return SpectrogramPanel(spectrogram, log_norm=True)


@pytest.fixture
def panel_stack() -> PanelStack:
    """Create a non-interactive panel stack for testing."""
    return PanelStack(non_interactive=True)


class TestBasePanel:
    """Test shared functionality between all `BasePanel` subclasses."""

    def test_initialisation(
        self, base_panel: BasePanel, spectrogram: Spectrogram
    ) -> None:
        """Check that a `BasePanel` subclass is initialised correctly."""
        # Test the public instance attributes are set correctly
        assert base_panel.name == PanelName.SPECTROGRAM
        assert base_panel.spectrogram == spectrogram
        assert base_panel.tag == spectrogram.tag
        assert base_panel.identifier is None

        # Test that unset properties raise appropriate errors
        with pytest.raises(ValueError):
            _ = base_panel.ax

        with pytest.raises(ValueError):
            _ = base_panel.fig

        with pytest.raises(ValueError):
            _ = base_panel.panel_format

    def test_xaxis_hidden(self, base_panel: BasePanel, axes: Axes) -> None:
        """Check that calling for the xaxis labels to be hidden, actually hides them."""
        base_panel.ax = axes
        base_panel.hide_xaxis_labels()
        assert not axes.get_xaxis().get_ticklabels(which="both")

    def test_yaxis_hidden(self, base_panel: BasePanel, axes: Axes) -> None:
        """Check that calling for the yaxis labels to be hidden, actually hides them."""
        base_panel.ax = axes
        base_panel.hide_yaxis_labels()
        assert not axes.get_yaxis().get_ticklabels(which="both")


class TestBaseTimeSeriesPanel:
    def test_xaxis_is_time(self, base_time_series_panel: BaseTimeSeriesPanel) -> None:
        """Check that the xaxis type for a time series panel is always time."""
        assert base_time_series_panel.xaxis_type == XAxisType.TIME

    def test_times(
        self, base_time_series_panel: BaseTimeSeriesPanel, spectrogram: Spectrogram
    ) -> None:
        """Check that setting the time type for the panel, updates the times of each spectrum appropriately.

        The `spectrogram` fixture is used to construct the panel, so we use that to compare equality.
        """

        # Check both cases of time type.
        base_time_series_panel.time_type = TimeType.RELATIVE
        assert np.array_equal(base_time_series_panel.times, spectrogram.times)

        base_time_series_panel.time_type = TimeType.DATETIMES
        assert np.array_equal(base_time_series_panel.times, spectrogram.datetimes)

    @pytest.mark.parametrize(
        "time_type,expected_label",
        [
            (TimeType.RELATIVE, "Time [s]"),
            (TimeType.DATETIMES, "Time [UTC] (Start Date: 2025-02-13)"),
        ],
    )
    def test_xaxis_labelling(
        self,
        base_time_series_panel: BaseTimeSeriesPanel,
        axes: Axes,
        time_type: TimeType,
        expected_label: str,
    ) -> None:
        """Check axis labeling for different time types."""
        base_time_series_panel.ax = axes
        base_time_series_panel.time_type = time_type
        base_time_series_panel.annotate_xaxis()
        assert base_time_series_panel.ax.get_xlabel() == expected_label


class TestFrequencyCutsPanel:
    def test_xaxis_is_frequency(
        self, frequency_cuts_panel_relative_cuts: FrequencyCutsPanel
    ) -> None:
        """Check that the xaxis type for a time series panel is always frequency.

        Arbitrarily choose the relative cuts panel, as it doesn't matter for this test.
        """
        assert frequency_cuts_panel_relative_cuts.xaxis_type == XAxisType.FREQUENCY

    def test_frequencies(
        self,
        frequency_cuts_panel_relative_cuts: FrequencyCutsPanel,
        spectrogram: Spectrogram,
    ) -> None:
        """Check that the frequencies assigned to each spectral component as managed by the panel, are equal to the frequencies
        assigned to each spectral component in the spectrogram used to construct the panel.

        Arbitrarily choose the relative cuts panel, as it doesn't matter for this test.
        """
        assert np.array_equal(
            frequency_cuts_panel_relative_cuts.frequencies, spectrogram.frequencies
        )

    def test_annotate_xaxis(
        self, frequency_cuts_panel_relative_cuts: FrequencyCutsPanel, axes: Axes
    ) -> None:
        """Check that the xaxis gets annotated appropriately."""
        frequency_cuts_panel_relative_cuts.ax = axes
        frequency_cuts_panel_relative_cuts.annotate_xaxis()
        assert frequency_cuts_panel_relative_cuts.ax.get_xlabel() == "Frequency [Hz]"

    def test_no_times_specified(self, spectrogram: Spectrogram) -> None:
        """Check that an error is raised when the class is instantiated with no times specified."""
        times: list[float] = []
        with pytest.raises(ValueError):
            FrequencyCutsPanel(spectrogram, *times)

    def test_annotate_yaxis_dBb(
        self, frequency_cuts_panel_dBb: FrequencyCutsPanel, axes: Axes
    ) -> None:
        """Check that the ylabel is annotated appropriately, in the case where the spectrum units are `dBb`."""
        frequency_cuts_panel_dBb.ax = axes
        frequency_cuts_panel_dBb.annotate_yaxis()
        assert frequency_cuts_panel_dBb.ax.get_ylabel() == "dBb"

    def test_annotate_yaxis_peak_normalised(
        self, frequency_cuts_panel_peak_normalised: FrequencyCutsPanel, axes: Axes
    ) -> None:
        """Check that the ylabel is annotated appropriately, in the case where the spectrum units are normalised to their peak values, respectively."""
        frequency_cuts_panel_peak_normalised.ax = axes
        frequency_cuts_panel_peak_normalised.annotate_yaxis()
        # We don't expect any label in this case
        assert not frequency_cuts_panel_peak_normalised.ax.get_ylabel()

    def test_annotate_yaxis(
        self,
        frequency_cuts_panel_relative_cuts: FrequencyCutsPanel,
        axes: Axes,
        spectrogram: Spectrogram,
    ) -> None:
        """Check that the ylabel is annotated appropriately, when the spectrum units are those defined by the spectrogram used to construct
        the panel.
        """
        frequency_cuts_panel_relative_cuts.ax = axes
        frequency_cuts_panel_relative_cuts.annotate_yaxis()
        assert (
            frequency_cuts_panel_relative_cuts.ax.get_ylabel()
            == f"{spectrogram.spectrum_unit.value}".capitalize()
        )


class TestTimeCutsPanel:
    def test_no_frequencies_specified(self, spectrogram: Spectrogram) -> None:
        """Check that an error is raised when the class is instantiated with no frequencies specified."""
        frequencies: list[float] = []
        with pytest.raises(ValueError):
            TimeCutsPanel(spectrogram, *frequencies)

    def test_annotate_yaxis_dBb(
        self, time_cuts_panel_dBb: TimeCutsPanel, axes: Axes
    ) -> None:
        """Check that the ylabel is annotated appropriately, in the case where the spectrum units are `dBb`."""
        # Arbitrarily set the time type (it has to be set)
        time_cuts_panel_dBb.time_type = TimeType.RELATIVE
        time_cuts_panel_dBb.ax = axes
        time_cuts_panel_dBb.annotate_yaxis()
        assert time_cuts_panel_dBb.ax.get_ylabel() == "dBb"

    def test_annotate_yaxis_peak_normalised(
        self, time_cuts_panel_peak_normalised: TimeCutsPanel, axes: Axes
    ) -> None:
        """Check that the ylabel is annotated appropriately, in the case where the spectrum units are normalised to their peak values, respectively."""
        time_cuts_panel_peak_normalised.ax = axes
        time_cuts_panel_peak_normalised.annotate_yaxis()
        # We don't expected any label in this case
        assert not time_cuts_panel_peak_normalised.ax.get_ylabel()

    def test_annotate_yaxis(
        self,
        time_cuts_panel: TimeCutsPanel,
        axes: Axes,
        spectrogram: Spectrogram,
    ) -> None:
        """Check that the ylabel is annotated appropriately, when the spectrum units are those defined by the spectrogram used to construct
        the panel.
        """
        time_cuts_panel.ax = axes
        time_cuts_panel.annotate_yaxis()
        assert (
            time_cuts_panel.ax.get_ylabel()
            == f"{spectrogram.spectrum_unit.value}".capitalize()
        )


class TestIntegralOverFrequencyPanel:
    def test_annotate_yaxis(
        self, integral_over_frequency_panel: IntegralOverFrequencyPanel, axes: Axes
    ) -> None:
        """Check that the yaxis is not annotated."""
        integral_over_frequency_panel.ax = axes
        integral_over_frequency_panel.annotate_yaxis()
        # We don't expect any label in this case
        assert not integral_over_frequency_panel.ax.get_ylabel()


class TestSpectrogramPanel:
    """Test functionality specific to SpectrogramPanel."""

    def test_annotate_yaxis(
        self, spectrogram_panel: SpectrogramPanel, axes: Axes
    ) -> None:
        """Check that the yaxis is annotated appropriately."""
        spectrogram_panel.ax = axes
        spectrogram_panel.annotate_yaxis()
        assert spectrogram_panel.ax.get_ylabel() == "Frequency [Hz]"


class TestPanelStack:
    def test_default_initialization(self, panel_stack: PanelStack) -> None:
        """Test initialization with default parameters."""
        assert panel_stack.num_panels == 0

        # Test that unset properties raise appropriate errors
        with pytest.raises(ValueError):
            _ = panel_stack.fig

        with pytest.raises(ValueError):
            _ = panel_stack.axs

    def test_adding_panel_increments_panel_count(
        self, panel_stack: PanelStack, spectrogram_panel: SpectrogramPanel
    ) -> None:
        """Check that adding a panel increments the number of panels in the stack."""
        # Take a record of the initial number of panels
        initial_num_panels = panel_stack.num_panels

        # Check that it is zero.
        assert initial_num_panels == 0

        # Add a panel, and check that the number of panels is as expected.
        panel_stack.add_panel(spectrogram_panel)
        assert panel_stack.num_panels == initial_num_panels + 1

        # Add a panel, and check that the number of panels is as expected.
        panel_stack.add_panel(spectrogram_panel)
        assert panel_stack.num_panels == initial_num_panels + 2

    def test_adding_superimposed_panel_increments_panel_count(
        self, panel_stack: PanelStack, spectrogram_panel: SpectrogramPanel
    ) -> None:
        """Check that adding a superimposed panel increments the number of panels in the stack."""
        # Take a record of the initial number of superimposed panels
        initial_num_superimposed_panels = panel_stack.num_superimposed_panels

        # Check that it is zero.
        assert initial_num_superimposed_panels == 0

        # Add a panel, and check that the number of panels is as expected.
        panel_stack.superimpose_panel(spectrogram_panel)
        assert (
            panel_stack.num_superimposed_panels == initial_num_superimposed_panels + 1
        )

        # Add a panel, and check that the number of panels is as expected.
        panel_stack.superimpose_panel(spectrogram_panel)
        assert (
            panel_stack.num_superimposed_panels == initial_num_superimposed_panels + 2
        )

    def test_check_panel_ordering(
        self,
        panel_stack: PanelStack,
        spectrogram_panel: SpectrogramPanel,
        frequency_cuts_panel_relative_cuts: FrequencyCutsPanel,
    ) -> None:
        """Check that panels are ordered by their `XAxisType`"""
        panel_stack.add_panel(spectrogram_panel)
        panel_stack.add_panel(frequency_cuts_panel_relative_cuts)
        # Frequency cut panels should be first, at the top of the plot.
        assert panel_stack.panels == [
            frequency_cuts_panel_relative_cuts,
            spectrogram_panel,
        ]

    def test_incompatible_time_types(
        self, panel_stack: PanelStack, spectrogram_panel: SpectrogramPanel
    ) -> None:
        """Check that two panels cannot be added to the stack with incompatible time types."""
        # Add a spectrogram with time type `DATETIMES` to the stack.
        spectrogram_panel.time_type = TimeType.DATETIMES
        with pytest.raises(ValueError):
            panel_stack.add_panel(spectrogram_panel)
