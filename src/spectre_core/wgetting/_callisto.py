# SPDX-FileCopyrightText: © 2024 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

import os
import subprocess
import shutil
import gzip
from datetime import datetime

from spectre_core.config import (
    get_spectre_data_dir_path, get_batches_dir_path, TimeFormat, trim_spectre_data_dir_path
)

from enum import Enum

class CallistoInstrumentCode(Enum):
    """e-Callisto network station codes."""
    ALASKA_ANCHORAGE     = "ALASKA-ANCHORAGE"
    ALASKA_COHOE         = "ALASKA-COHOE"
    ALASKA_HAARP         = "ALASKA-HAARP"
    ALGERIA_CRAAG        = "ALGERIA-CRAAG"
    ALMATY               = "ALMATY"
    AUSTRIA_KRUMBACH     = "AUSTRIA-Krumbach"
    AUSTRIA_MICHELBACH   = "AUSTRIA-MICHELBACH"
    AUSTRIA_OE3FLB       = "AUSTRIA-OE3FLB"
    AUSTRIA_UNIGRAZ      = "AUSTRIA-UNIGRAZ"
    AUSTRALIA_ASSA       = "Australia-ASSA"
    BIR                  = "BIR"
    CROATIA_VISNJAN      = "Croatia-Visnjan"
    DENMARK              = "DENMARK"
    EGYPT_ALEXANDRIA     = "EGYPT-Alexandria"
    EGYPT_SPACEAGENCY    = "EGYPT-SpaceAgency"
    FINLAND_SIUNTIO      = "FINLAND-Siuntio"
    FINLAND_KEMPELE      = "Finland-Kempele"
    GERMANY_DLR          = "GERMANY-DLR"
    GLASGOW              = "GLASGOW"
    GREENLAND            = "GREENLAND"
    HUMAIN               = "HUMAIN"
    HURBANOVO            = "HURBANOVO"
    INDIA_GAURI          = "INDIA-GAURI"
    INDIA_OOTY           = "INDIA-OOTY"
    INDIA_UDAIPUR        = "INDIA-UDAIPUR"
    JAPAN_IBARAKI        = "JAPAN-IBARAKI"
    KASI                 = "KASI"
    MEXART               = "MEXART"
    MEXICO_FCFM_UANL     = "MEXICO-FCFM-UANL"
    MEXICO_LANCE_A       = "MEXICO-LANCE-A"
    MEXICO_LANCE_B       = "MEXICO-LANCE-B"
    MONGOLIA_UB          = "MONGOLIA-UB"
    MRO                  = "MRO"
    MRT3                 = "MRT3"
    MALAYSIA_BANTING     = "Malaysia-Banting"
    NORWAY_EGERSUND      = "NORWAY-EGERSUND"
    NORWAY_NY_AALESUND   = "NORWAY-NY-AALESUND"
    NORWAY_RANDABERG     = "NORWAY-RANDABERG"
    POLAND_GROTNIKI      = "POLAND-Grotniki"
    ROMANIA              = "ROMANIA"
    ROSWELL_NM           = "ROSWELL-NM"
    SPAIN_PERALEJOS      = "SPAIN-PERALEJOS"
    SSRT                 = "SSRT"
    SWISS_HB9SCT         = "SWISS-HB9SCT"
    SWISS_HEITERSWIL     = "SWISS-HEITERSWIL"
    SWISS_IRSOL          = "SWISS-IRSOL"
    SWISS_LANDSCHLACHT   = "SWISS-Landschlacht"
    SWISS_MUHEN          = "SWISS-MUHEN"
    TRIEST               = "TRIEST"
    TURKEY               = "TURKEY"
    UNAM                 = "UNAM"
    URUGUAY              = "URUGUAY"
    USA_BOSTON           = "USA-BOSTON"


def _get_batch_name(
    station: str, 
    date: str, 
    time: str, 
    code: str
) -> str:
    """
    Create a standardised batch file name for a `spectre` batch file.

    :param station: Station name.
    :param date: Observation date in 'YYYYMMDD' format.
    :param time: Observation time in 'HHMMSS' format.
    :param code: Numeric instrument code.
    :return: Formatted batch file name.
    """
    dt = datetime.strptime(f"{date}T{time}", "%Y%m%dT%H%M%S")
    formatted_time = dt.strftime(TimeFormat.DATETIME)
    return f"{formatted_time}_callisto-{station.lower()}-{code}.fits"


def _get_batch_components(
    gz_path: str
) -> list[str]:
    """
    Extract station, date, time, and instrument code from the `.fit.gz` file name.

    :param gz_path: Path to the `.fit.gz` file.
    :return: List of [station, date, time, instrument_code].
    :raises ValueError: If file format is invalid.
    """
    file_name = os.path.basename(gz_path)
    if not file_name.endswith(".fit.gz"):
        raise ValueError(f"Invalid file extension: {file_name}. Expected .fit.gz")
    file_base_name = file_name.rstrip(".fit.gz")
    parts = file_base_name.split('_')
    if len(parts) != 4:
        raise ValueError("Invalid file name format. Expected '[station]_[date]_[time]_[code].fit.gz'")
    return parts


def _get_batch_path(
    gz_path: str
) -> str:
    """
    Generate the full path for the `spectre` batch file.

    :param gz_path: Path to the raw `.fit.gz` file.
    :return: Path to the corresponding batch file.
    """
    station, date, time, code = _get_batch_components(gz_path)
    batch_name = _get_batch_name(station, date, time, code)
    batch_start_time = batch_name.split("_")[0]
    dt = datetime.strptime(batch_start_time, TimeFormat.DATETIME)
    batch_dir = get_batches_dir_path(year=dt.year, month=dt.month, day=dt.day)
    os.makedirs(batch_dir, exist_ok=True)
    return os.path.join(batch_dir, batch_name)


def _unzip_file_to_batches(
    gz_path: str
) -> str:
    """
    Decompress a `.fit.gz` file and save it as a `.fits` batch file.

    :param gz_path: Path to the `.fit.gz` file.
    :return: The file path of the newly created batch file, relative to the mounted volume.
    """
    fits_path = _get_batch_path(gz_path)
    with gzip.open(gz_path, "rb") as f_in, open(fits_path, "wb") as f_out:
        shutil.copyfileobj(f_in, f_out)
        return trim_spectre_data_dir_path(f_out.name)


def _unzip_to_batches(
    tmp_dir: str
) -> list[str]:
    """
    Decompress all `.gz` files in a temporary directory and save them as `spectre`
    batch files.

    :param tmp_dir: Path to the temporary directory containing `.gz` files.
    :return: A list of file names of all newly created batch files, relative to the mounted volume.
    """
    batch_file_names = []
    for entry in os.scandir(tmp_dir):
        if entry.is_file() and entry.name.endswith(".gz"):
            batch_file_names.append( _unzip_file_to_batches(entry.path) )
            os.remove(entry.path)
    shutil.rmtree(tmp_dir)
    return batch_file_names
            


def _wget_callisto_data(
    instrument_code: str, 
    year: int, 
    month: int, 
    day: int, 
    tmp_dir: str
) -> None:
    """
    Download raw `.fit.gz` files from the e-Callisto network using `wget`.

    :param instrument_code: Instrument code for filtering files.
    :param year: Observation year.
    :param month: Observation month.
    :param day: Observation day.
    :param tmp_dir: Path to the temporary directory for downloads.
    """
    date_str = f"{year:04d}/{month:02d}/{day:02d}"
    base_url = f"http://soleil.i4ds.ch/solarradio/data/2002-20yy_Callisto/{date_str}/"
    command = [
        "wget", "-r", "-l1", "-nd", "-np",
        "-R", ".tmp", "-A", f"{instrument_code}*.fit.gz",
        "-P", tmp_dir, base_url
    ]
    subprocess.run(command, check=True)


def download_callisto_data(
    instrument_code: CallistoInstrumentCode, 
    year: int, 
    month: int, 
    day: int
) -> list[str]:
    """
    Download and decompress e-Callisto FITS files, saving them as `spectre` batch files.

    :param instrument_code: e-Callisto station instrument code.
    :param year: Year of the observation.
    :param month: Month of the observation.
    :param day: Day of the observation.
    :return: A list of file names of all newly created batch files, relative to the mounted volume.
    """
    tmp_dir = os.path.join(get_spectre_data_dir_path(), "tmp")
    # if there are any residual files in the temporary directory, remove them.
    if os.path.exists(tmp_dir):
        shutil.rmtree(tmp_dir)
    os.makedirs(tmp_dir, exist_ok=True)
    
    _wget_callisto_data(instrument_code.value, year, month, day, tmp_dir)
    return sorted( _unzip_to_batches(tmp_dir) )