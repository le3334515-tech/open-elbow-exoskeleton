"""CRC-framed ASCII transport shared with the C firmware (Apache-2.0)."""
import json
import math

MAX_REQUEST_BYTES = 96
MAX_RESPONSE_BYTES = 1024
OPS = frozenset("PING HB CAL ARM STOP RESET ESTOP TARGET ASSIST KP KD TMAX VMAX".split())


def crc16(data: bytes) -> int:
    crc = 0xFFFF
    for value in data:
        crc ^= value << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) & 0xFFFF if crc & 0x8000 else (crc << 1) & 0xFFFF
    return crc


def frame(payload: bytes) -> bytes:
    if b"\n" in payload or b"\r" in payload or b"*" in payload:
        raise ValueError("payload contains framing delimiter")
    payload.decode("ascii")
    return payload + f"*{crc16(payload):04X}\n".encode("ascii")


def unframe(line: bytes, max_bytes: int = MAX_RESPONSE_BYTES) -> bytes:
    if len(line) > max_bytes or not line.endswith(b"\n"):
        raise ValueError("oversize or unterminated frame")
    body = line[:-1]
    if body.endswith(b"\r"):
        body = body[:-1]
    if body.count(b"*") != 1:
        raise ValueError("expected one CRC delimiter")
    payload, checksum = body.rsplit(b"*", 1)
    if len(checksum) != 4 or any(c not in b"0123456789abcdefABCDEF" for c in checksum):
        raise ValueError("invalid CRC encoding")
    if crc16(payload) != int(checksum, 16):
        raise ValueError("CRC mismatch")
    payload.decode("ascii")
    return payload


def request(seq: int, op: str, value: float = 0.0) -> bytes:
    if not 0 <= seq <= 65535 or op not in OPS or not math.isfinite(value):
        raise ValueError("invalid command, sequence or nonfinite numeric value")
    result = frame(f"{seq} {op} {value:.9g}".encode("ascii"))
    if len(result) > MAX_REQUEST_BYTES:
        raise ValueError("request too long")
    return result


def response(line: bytes) -> dict:
    def reject_constant(value):
        raise ValueError(f"nonfinite JSON: {value}")
    result = json.loads(unframe(line), parse_constant=reject_constant)
    if not isinstance(result, dict) or result.get("type") not in ("ack", "status", "event", "error"):
        raise ValueError("invalid response type")
    return result

