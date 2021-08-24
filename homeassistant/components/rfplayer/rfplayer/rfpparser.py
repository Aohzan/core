"""Parsers."""

import logging
import re
import time
from enum import Enum
from typing import Any, Callable, DefaultDict, Dict, Generator, cast
import json
import pprint

log = logging.getLogger(__name__)

PACKET_ID_SEP = "_"

PACKET_FIELDS = {
   "bat": "battery",
   "cmd": "command",
   "dtc": "detector",
   "sta": "status",
   "sen": "sensor",
}

UNITS = {
   "bat": None,
   "cmd": None,
   "detector": None,
   "sta": None,
}

DTC_STATUS_LOOKUP = {
    "0": "closed",
    "2": "open",
    "8": "alive",
    "16": "assoc",
}

VALUE_TRANSLATION = cast(
    Dict[str, Callable[[str], str]],
    {
        "detector": lambda x: DTC_STATUS_LOOKUP.get(x, "unknown"),
    },
)

PACKET_HEADER_RE = (
    "^("
    + "|".join(
        [
         "ZIA\-\-",  #command reply 
         "ZIA33",    #json reply
        ]
    )
    + ")"
)

packet_header_re = re.compile(PACKET_HEADER_RE)

PacketType = Dict[str, Any]


class PacketHeader(Enum):
    """Packet source identification."""

    master = "10"
    echo = "11"
    gateway = "20"


#ZIA--Welcome to Ziblue Dongle RFPLAYER (RFP1000, Firmware=V1.39 F=433Mhz & 868Mhz EU)!
#ZIA--RECEIVED PROTOCOLS: X10 RTS VISONIC BLYSS CHACON OREGONV1 OREGONV2 OREGONV3/OWL DOMIA X2D KD101 PARROT TIC FS20 EDISIO
#ZIA33{ "frame" :{"header": {"frameType": "0", "cluster": "0", "dataFlag": "1", "rfLevel": "-46", "floorNoise": "-95", "rfQuality": "10", "protocol": "8", "protocolMeaning": "X2D", "infoType": "11", "frequency": "868350"},"infos": {"subType": "0", "subTypeMeaning": "Detector/Sensor", "id": "2679630080", "qualifier": "0", "qualifierMeaning": { "flags": []}, "d0": "16637", "d1": "0", "d2": "0", "d3": "0"}}}

def valid_packet(packet: str) -> bool:
    return bool(packet_header_re.match(packet))


def decode_packet(packet: str) -> PacketType:
    data = cast(PacketType, {"node": PacketHeader("20").name})

    if packet.startswith("ZIA--"):
        data["message"]=packet.replace("ZIA--","") 
        return data

    jdata = json.loads(packet.replace("ZIA33",""))

    if jdata["frame"]["header"]["protocol"] == '8':
       data["protocol"]='x2d'
       data["id"]=jdata["frame"]["infos"]["id"]

       value = jdata["frame"]["infos"]["qualifier"]
       
       key = jdata["frame"]["infos"]["subType"]

       if key == "0":
         key = "detector" 

       if key in VALUE_TRANSLATION:
            try:
                value = VALUE_TRANSLATION[key](value)
            except ValueError:
                log.warning(
                    "Could not convert attr '%s' value '%s' to expected type '%s'",
                    key,
                    value,
                    VALUE_TRANSLATION[key].__name__,
                )
       
       data[key]=value
       unit = UNITS.get(key, None)
       if unit:
           data[key +"_unit"]=unit
      

    else:
       data["protocol"]=jdata["frame"]["header"]["protocol"] 

    return data


def encode_packet(packet: PacketType) -> str:
    """Construct packet string from packet dictionary.

    >>> encode_packet({
    ...     'protocol': 'newkaku',
    ...     'id': '000001',
    ...     'switch': '01',
    ...     'command': 'on',
    ... })
    '10;newkaku;000001;01;on;'
    """
    if packet["protocol"] == "rfdebug":
        return "10;RFDEBUG=%s;" % packet["command"]
    elif packet["protocol"] == "rfudebug":
        return "10;RFUDEBUG=%s;" % packet["command"]
    elif packet["protocol"] == "qrfdebug":
        return "10;QRFDEBUG=%s;" % packet["command"]
    else:
        return SWITCH_COMMAND_TEMPLATE.format(node=PacketHeader.master.value, **packet)


def serialize_packet_id(packet: PacketType) -> str:
    return PACKET_ID_SEP.join(
        filter(None, [packet.get("protocol",None), packet.get("id", None), packet.get("switch", None)]))



def deserialize_packet_id(packet_id: str) -> Dict[str, str]:
    log.debug("AAAAA")
    if packet_id == "rfplayer":
        return {"protocol": UNKNOWN}

    if packet_is == "ZIA":
        return {"protocol": "ZIA++"}

    if packet_id.startswith("dooya_v4"):
        protocol = "dooya_v4"
        id_switch = packet_id.replace("dooya_v4_", "").split(PACKET_ID_SEP)
    else:
        protocol, *id_switch = packet_id.split(PACKET_ID_SEP)

    assert len(id_switch) < 3

    packet_identifiers = {
        "protocol": protocol,
    }
    if id_switch:
        packet_identifiers["id"] = id_switch[0]
    if len(id_switch) > 1:
        packet_identifiers["switch"] = id_switch[1]

    return packet_identifiers


def packet_events(packet: PacketType) -> Generator[PacketType, None, None]:

    field_abbrev = {
        v: k
        for k, v in sorted(
            PACKET_FIELDS.items(), key=lambda x: (x[1], x[0]), reverse=True
        )
    }

    log.debug("ABBREV: %s",field_abbrev)
    packet_id = serialize_packet_id(packet)
    log.debug("items: %s",packet.items())
    events = {f: v for f, v in packet.items() if f in field_abbrev}
    for f,v in packet.items():
        log.debug("f:%s,v:%s",f,v)
    for s,v in events.items():
       log.debug("event: %s -> %s",s,v)

   # try:
   #   packet["message"]
   #   yield { "id": packet_id, "message": packet["message"] }
   # except KeyError:
    for sensor, value in events.items():
      log.debug("packet_events, sensor:%s,value:%s",sensor,value)
      unit = packet.get(sensor + "_unit", None)
      yield { "id": packet_id + PACKET_ID_SEP + field_abbrev[sensor], 
                "sensor": sensor, 
                "value": value,
                "unit": unit,
            }


