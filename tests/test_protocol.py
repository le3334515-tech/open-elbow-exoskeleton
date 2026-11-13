import json
import pytest
from elbow_exo.protocol import crc16, frame, unframe, request, response


def test_crc_known_independent_check_value():
    assert crc16(b"123456789") == 0x29B1


def test_roundtrip_commands_and_sequence_wrap():
    assert unframe(request(65535, "TARGET", 1.25), 96) == b"65535 TARGET 1.25"
    assert unframe(request(0, "HB"), 96) == b"0 HB 0"


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf")])
def test_nonfinite_control_values_never_reach_wire(value):
    with pytest.raises(ValueError):
        request(1, "TARGET", value)


@pytest.mark.parametrize("wire", [b"0 HB 0*0000\n", b"0 HB 0*FFFF", b"x*1\n", b"x*000Z\n", b"*FFFF*0000\n", b"x" * 1025 + b"\n"])
def test_malformed_or_corrupted_frame(wire):
    with pytest.raises(ValueError):
        unframe(wire)


def test_response_schema_and_json_finite():
    msg = {"type": "ack", "seq": 1, "ok": True}
    assert response(frame(json.dumps(msg).encode())) == msg
    with pytest.raises(ValueError):
        response(frame(b'{"type":"status","q":NaN}'))
    with pytest.raises(ValueError):
        response(frame(b'[]'))


def test_injection_delimiters_rejected():
    with pytest.raises(ValueError):
        frame(b"1 HB 0\n2 ARM 0")

