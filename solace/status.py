"""Low-overhead, local-only status collection for Solace."""

from __future__ import annotations

import ctypes
import importlib.util
import json
import os
import platform
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from . import __version__
from .config import SolaceConfig


UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class MemoryUsage:
    used: int | None
    total: int | None


@dataclass(frozen=True, slots=True)
class DiskUsage:
    free: int | None
    total: int | None


@dataclass(frozen=True, slots=True)
class StatusSnapshot:
    version: str
    cpu: str
    memory: MemoryUsage
    disk: DiskUsage
    chat_model: str
    embedding_model: str
    embedding_dimensions: str
    ollama_state: str
    mem0_state: str
    long_term_memories: int | None
    qdrant_storage_bytes: int | None
    conversations_bytes: int
    solace_data_bytes: int


def _windows_cpu_name() -> str | None:
    try:
        import winreg

        key_path = r"HARDWARE\DESCRIPTION\System\CentralProcessor\0"
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
            value, _ = winreg.QueryValueEx(key, "ProcessorNameString")
        return str(value).strip() or None
    except (ImportError, OSError):
        return None


def cpu_name() -> str:
    if platform.system() == "Windows":
        detected = _windows_cpu_name()
        if detected:
            return detected
    detected = platform.processor().strip()
    if detected:
        return detected
    if Path("/proc/cpuinfo").is_file():
        try:
            for line in Path("/proc/cpuinfo").read_text(encoding="utf-8").splitlines():
                if line.lower().startswith("model name"):
                    return line.split(":", 1)[1].strip()
        except (OSError, IndexError):
            pass
    return platform.machine() or UNKNOWN


def _windows_memory_usage() -> MemoryUsage | None:
    if platform.system() != "Windows":
        return None

    class MemoryStatus(ctypes.Structure):
        _fields_ = [
            ("length", ctypes.c_ulong),
            ("memory_load", ctypes.c_ulong),
            ("total_physical", ctypes.c_ulonglong),
            ("available_physical", ctypes.c_ulonglong),
            ("total_page_file", ctypes.c_ulonglong),
            ("available_page_file", ctypes.c_ulonglong),
            ("total_virtual", ctypes.c_ulonglong),
            ("available_virtual", ctypes.c_ulonglong),
            ("available_extended_virtual", ctypes.c_ulonglong),
        ]

    status = MemoryStatus()
    status.length = ctypes.sizeof(MemoryStatus)
    try:
        success = ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status))
    except (AttributeError, OSError):
        return None
    if not success:
        return None
    total = int(status.total_physical)
    return MemoryUsage(used=total - int(status.available_physical), total=total)


def _proc_memory_usage() -> MemoryUsage | None:
    path = Path("/proc/meminfo")
    if not path.is_file():
        return None
    try:
        entries = {}
        for line in path.read_text(encoding="utf-8").splitlines():
            key, value = line.split(":", 1)
            entries[key] = int(value.strip().split()[0]) * 1024
        total = entries["MemTotal"]
        available = entries.get("MemAvailable", entries.get("MemFree", 0))
        return MemoryUsage(used=total - available, total=total)
    except (OSError, KeyError, ValueError):
        return None


def _macos_memory_usage() -> MemoryUsage | None:
    if platform.system() != "Darwin":
        return None
    try:
        total = int(subprocess.check_output(["sysctl", "-n", "hw.memsize"], text=True).strip())
        output = subprocess.check_output(["vm_stat"], text=True)
        page_size = 4096
        pages: dict[str, int] = {}
        for line in output.splitlines():
            if "page size of" in line:
                page_size = int(line.split("page size of", 1)[1].split()[0])
            elif ":" in line:
                key, value = line.split(":", 1)
                pages[key] = int(value.strip().rstrip("."))
        available_pages = pages.get("Pages free", 0) + pages.get("Pages inactive", 0)
        available_pages += pages.get("Pages speculative", 0)
        return MemoryUsage(used=total - (available_pages * page_size), total=total)
    except (OSError, subprocess.SubprocessError, ValueError):
        return None


def memory_usage() -> MemoryUsage:
    return (
        _windows_memory_usage()
        or _proc_memory_usage()
        or _macos_memory_usage()
        or MemoryUsage(None, None)
    )


def disk_usage(path: Path) -> DiskUsage:
    existing = path
    while not existing.exists() and existing != existing.parent:
        existing = existing.parent
    try:
        usage = shutil.disk_usage(existing)
        return DiskUsage(free=usage.free, total=usage.total)
    except OSError:
        return DiskUsage(None, None)


def directory_size(path: Path) -> int:
    """Measure regular files without following directory symlinks."""
    if not path.exists():
        return 0
    if path.is_file():
        try:
            return path.stat().st_size
        except OSError:
            return 0

    total = 0
    try:
        entries = list(os.scandir(path))
    except OSError:
        return 0
    for entry in entries:
        try:
            if entry.is_symlink():
                continue
            if entry.is_file(follow_symlinks=False):
                total += entry.stat(follow_symlinks=False).st_size
            elif entry.is_dir(follow_symlinks=False):
                total += directory_size(Path(entry.path))
        except OSError:
            continue
    return total


def _request_json(
    url: str,
    payload: dict[str, Any] | None = None,
    timeout: float = 0.6,
) -> dict[str, Any] | None:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {"Accept": "application/json"}
    if data is not None:
        headers["Content-Type"] = "application/json"
    request = Request(url, data=data, headers=headers)
    try:
        with urlopen(request, timeout=timeout) as response:
            payload = json.load(response)
        return payload if isinstance(payload, dict) else None
    except (HTTPError, URLError, OSError, TimeoutError, ValueError):
        return None


def _get_json(url: str, timeout: float = 0.6) -> dict[str, Any] | None:
    return _request_json(url, timeout=timeout)


def _post_json(
    url: str,
    payload: dict[str, Any],
    timeout: float = 0.6,
) -> dict[str, Any] | None:
    return _request_json(url, payload=payload, timeout=timeout)


def _model_embedding_dimensions(model_info: dict[str, Any] | None) -> int | None:
    if not model_info:
        return None
    metadata = model_info.get("model_info")
    if not isinstance(metadata, dict):
        return None
    architecture = metadata.get("general.architecture")
    if isinstance(architecture, str):
        value = metadata.get(f"{architecture}.embedding_length")
        if isinstance(value, int):
            return value
    candidates = [
        value
        for key, value in metadata.items()
        if key.endswith(".embedding_length")
        and ".vision." not in key
        and isinstance(value, int)
    ]
    return candidates[0] if len(candidates) == 1 else None


def embedding_dimensions_state(config: SolaceConfig, ollama_running: bool) -> str:
    configured = config.embedding_dimensions
    if not ollama_running:
        return f"{configured} (not verified; Ollama unavailable)"
    info = _post_json(
        f"{config.ollama_base_url.rstrip('/')}/api/show",
        {"model": config.embedding_model, "verbose": False},
    )
    actual = _model_embedding_dimensions(info)
    if actual is None:
        return f"{configured} (not verified; model unavailable)"
    if actual != configured:
        return f"{configured} configured / {actual} reported (mismatch)"
    return f"{configured} (verified)"


def _package_available(distribution_module: str) -> bool:
    try:
        return importlib.util.find_spec(distribution_module) is not None
    except (ImportError, ValueError):
        return False


def qdrant_collection_info(config: SolaceConfig) -> dict[str, Any] | None:
    collection = config.memory_collection
    return _get_json(f"{config.qdrant_url.rstrip('/')}/collections/{collection}")


def _long_term_memory_count(info: dict[str, Any] | None) -> int | None:
    if not info:
        return None
    result = info.get("result")
    if not isinstance(result, dict):
        return None
    for key in ("points_count", "vectors_count"):
        value = result.get(key)
        if isinstance(value, int):
            return value
    return None


def collect_status(config: SolaceConfig) -> StatusSnapshot:
    data_dir = config.resolved_data_dir
    qdrant_info = qdrant_collection_info(config)
    ollama_version = _get_json(f"{config.ollama_base_url.rstrip('/')}/api/version")
    ollama_running = ollama_version is not None
    if ollama_running:
        version = ollama_version.get("version")
        ollama = f"running ({version})" if version else "running"
    else:
        ollama = "unavailable"
    mem0_installed = _package_available("mem0")
    qdrant_reachable = qdrant_info is not None
    if mem0_installed and qdrant_reachable:
        mem0 = "ready"
    elif not mem0_installed:
        mem0 = "not installed"
    else:
        mem0 = "Qdrant unavailable"

    qdrant_path = config.qdrant_storage_dir
    qdrant_bytes = directory_size(qdrant_path) if qdrant_path.exists() else None
    return StatusSnapshot(
        version=__version__,
        cpu=cpu_name(),
        memory=memory_usage(),
        disk=disk_usage(data_dir),
        chat_model=config.chat_model,
        embedding_model=config.embedding_model,
        embedding_dimensions=embedding_dimensions_state(config, ollama_running),
        ollama_state=ollama,
        mem0_state=mem0,
        long_term_memories=_long_term_memory_count(qdrant_info),
        qdrant_storage_bytes=qdrant_bytes,
        conversations_bytes=directory_size(config.conversations_dir),
        solace_data_bytes=directory_size(data_dir),
    )


def format_bytes(value: int | None) -> str:
    if value is None:
        return UNKNOWN
    units = ("B", "KiB", "MiB", "GiB", "TiB")
    amount = float(value)
    for unit in units:
        if abs(amount) < 1024 or unit == units[-1]:
            return f"{amount:.0f} {unit}" if unit == "B" else f"{amount:.1f} {unit}"
        amount /= 1024
    return UNKNOWN


def _count(value: int | None) -> str:
    return str(value) if value is not None else UNKNOWN


def format_status(snapshot: StatusSnapshot) -> str:
    return "\n".join(
        (
            f"Solace {snapshot.version}",
            "",
            "System",
            f"CPU: {snapshot.cpu}",
            "RAM: "
            f"{format_bytes(snapshot.memory.used)} used / "
            f"{format_bytes(snapshot.memory.total)} total",
            "Disk: "
            f"{format_bytes(snapshot.disk.free)} free / "
            f"{format_bytes(snapshot.disk.total)} total",
            "",
            "AI",
            f"Chat model: {snapshot.chat_model}",
            f"Embedding model: {snapshot.embedding_model}",
            f"Embedding dimensions: {snapshot.embedding_dimensions}",
            f"Ollama: {snapshot.ollama_state}",
            "",
            "Memory",
            f"Mem0: {snapshot.mem0_state}",
            f"Long-term memories: {_count(snapshot.long_term_memories)}",
            f"Qdrant storage: {format_bytes(snapshot.qdrant_storage_bytes)}",
            "",
            "Storage",
            f"Conversations: {format_bytes(snapshot.conversations_bytes)}",
            f"Solace data: {format_bytes(snapshot.solace_data_bytes)}",
        )
    )


def status_text(config: SolaceConfig) -> str:
    return format_status(collect_status(config))
