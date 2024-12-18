# SPDX-FileCopyrightText: © 2024 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

# after we decorate all chunks, we can import the chunk_key -> chunk maps
from spectre_core.chunks.base import BaseChunk
from spectre_core.capture_config import CaptureConfig
from spectre_core.exceptions import ChunkNotFoundError
from spectre_core.chunks.chunk_register import chunk_map

def get_chunk(chunk_key: str) -> BaseChunk:
    Chunk = chunk_map.get(chunk_key)
    if Chunk is None:
        valid_chunk_keys = list(chunk_map.keys())
        raise ChunkNotFoundError(f"No chunk found for the chunk key: {chunk_key}. Valid chunk keys are: {valid_chunk_keys}")
    return Chunk

def get_chunk_from_tag(tag: str) -> BaseChunk:
    # if we are dealing with a callisto chunk, the chunk key is equal to the tag
    if "callisto" in tag:
        chunk_key = "callisto"
    # otherwise, we fetch the chunk key from the capture config
    else:
        capture_config= CaptureConfig(tag)
        chunk_key = capture_config.get('chunk_key')
    return get_chunk(chunk_key)
