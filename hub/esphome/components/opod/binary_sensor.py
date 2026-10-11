import esphome.codegen as cg
from esphome.components import binary_sensor
import esphome.config_validation as cv
from esphome.const import DEVICE_CLASS_CONNECTIVITY, DEVICE_CLASS_PROBLEM, ENTITY_CATEGORY_DIAGNOSTIC

from . import CONF_OPOD_ID, CONF_ZONE, OpodHub

DEPENDENCIES = ["opod"]

CONF_FAULT = "fault"
CONF_LINK = "link"

CONFIG_SCHEMA = cv.Schema(
    {
        cv.GenerateID(CONF_OPOD_ID): cv.use_id(OpodHub),
        cv.Optional(CONF_ZONE): cv.int_range(min=0, max=1),
        cv.Optional(CONF_FAULT): binary_sensor.binary_sensor_schema(device_class=DEVICE_CLASS_PROBLEM),
        cv.Optional(CONF_LINK): binary_sensor.binary_sensor_schema(
            device_class=DEVICE_CLASS_CONNECTIVITY, entity_category=ENTITY_CATEGORY_DIAGNOSTIC
        ),
    }
)


def _validate(config):
    if CONF_FAULT in config and CONF_ZONE not in config:
        raise cv.Invalid("'fault' needs a 'zone'")
    return config


FINAL_VALIDATE_SCHEMA = _validate


async def to_code(config):
    hub = await cg.get_variable(config[CONF_OPOD_ID])
    if CONF_FAULT in config:
        s = await binary_sensor.new_binary_sensor(config[CONF_FAULT])
        cg.add(hub.set_fault_binary_sensor(config[CONF_ZONE], s))
    if CONF_LINK in config:
        s = await binary_sensor.new_binary_sensor(config[CONF_LINK])
        cg.add(hub.set_link_binary_sensor(s))
