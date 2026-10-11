import esphome.codegen as cg
from esphome.components import sensor
import esphome.config_validation as cv
from esphome.const import (
    DEVICE_CLASS_CURRENT,
    DEVICE_CLASS_TEMPERATURE,
    ENTITY_CATEGORY_DIAGNOSTIC,
    STATE_CLASS_MEASUREMENT,
    UNIT_AMPERE,
    UNIT_CELSIUS,
)

from . import CONF_OPOD_ID, CONF_ZONE, ZONE_SCHEMA

DEPENDENCIES = ["opod"]

CONF_WATER_TEMPERATURE = "water_temperature"
CONF_HOT_FACE_TEMPERATURE = "hot_face_temperature"
CONF_TEC_CURRENT = "tec_current"
CONF_FLOW = "flow"
CONF_FAULT_CODE = "fault_code"

_temp = sensor.sensor_schema(
    unit_of_measurement=UNIT_CELSIUS,
    accuracy_decimals=1,
    device_class=DEVICE_CLASS_TEMPERATURE,
    state_class=STATE_CLASS_MEASUREMENT,
)

CONFIG_SCHEMA = cv.Schema(
    {
        **ZONE_SCHEMA,
        cv.Optional(CONF_WATER_TEMPERATURE): _temp,
        cv.Optional(CONF_HOT_FACE_TEMPERATURE): _temp,
        cv.Optional(CONF_TEC_CURRENT): sensor.sensor_schema(
            unit_of_measurement=UNIT_AMPERE,
            accuracy_decimals=2,
            device_class=DEVICE_CLASS_CURRENT,
            state_class=STATE_CLASS_MEASUREMENT,
            entity_category=ENTITY_CATEGORY_DIAGNOSTIC,
        ),
        cv.Optional(CONF_FLOW): sensor.sensor_schema(
            unit_of_measurement="L/min",
            accuracy_decimals=2,
            icon="mdi:water-pump",
            state_class=STATE_CLASS_MEASUREMENT,
            entity_category=ENTITY_CATEGORY_DIAGNOSTIC,
        ),
        cv.Optional(CONF_FAULT_CODE): sensor.sensor_schema(
            accuracy_decimals=0,
            icon="mdi:alert-octagon",
            entity_category=ENTITY_CATEGORY_DIAGNOSTIC,
        ),
    }
)

_SETTERS = {
    CONF_WATER_TEMPERATURE: "set_water_temperature_sensor",
    CONF_HOT_FACE_TEMPERATURE: "set_hot_face_temperature_sensor",
    CONF_TEC_CURRENT: "set_tec_current_sensor",
    CONF_FLOW: "set_flow_sensor",
    CONF_FAULT_CODE: "set_fault_code_sensor",
}


async def to_code(config):
    hub = await cg.get_variable(config[CONF_OPOD_ID])
    for key, setter in _SETTERS.items():
        if key in config:
            s = await sensor.new_sensor(config[key])
            cg.add(getattr(hub, setter)(config[CONF_ZONE], s))
