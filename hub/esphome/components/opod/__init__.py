"""Open Bed Climate hub component: ESPHome side of the Open Peltier Link (OPL) to the Pico 2 control board."""

import esphome.codegen as cg
import esphome.config_validation as cv
from esphome.components import sensor, uart
from esphome.const import CONF_ID

CODEOWNERS = []
DEPENDENCIES = ["uart"]
MULTI_CONF = False

CONF_OPOD_ID = "opod_id"
CONF_ZONE = "zone"
CONF_ROOM_TEMPERATURE = "room_temperature"
CONF_ROOM_HUMIDITY = "room_humidity"

opod_ns = cg.esphome_ns.namespace("opod")
OpodHub = opod_ns.class_("OpodHub", cg.Component, uart.UARTDevice)

CONFIG_SCHEMA = (
    cv.Schema(
        {
            cv.GenerateID(): cv.declare_id(OpodHub),
            # Optional, enables the dew-point guard (recommended when cooling below 16 °C).
            cv.Optional(CONF_ROOM_TEMPERATURE): cv.use_id(sensor.Sensor),
            cv.Optional(CONF_ROOM_HUMIDITY): cv.use_id(sensor.Sensor),
        }
    )
    .extend(cv.COMPONENT_SCHEMA)
    .extend(uart.UART_DEVICE_SCHEMA)
)

FINAL_VALIDATE_SCHEMA = uart.final_validate_device_schema(
    "opod", baud_rate=460800, require_tx=True, require_rx=True
)

ZONE_SCHEMA = {
    cv.GenerateID(CONF_OPOD_ID): cv.use_id(OpodHub),
    cv.Required(CONF_ZONE): cv.int_range(min=0, max=1),
}


async def to_code(config):
    var = cg.new_Pvariable(config[CONF_ID])
    await cg.register_component(var, config)
    await uart.register_uart_device(var, config)
    if CONF_ROOM_TEMPERATURE in config:
        cg.add(var.set_room_temperature_sensor(await cg.get_variable(config[CONF_ROOM_TEMPERATURE])))
    if CONF_ROOM_HUMIDITY in config:
        cg.add(var.set_room_humidity_sensor(await cg.get_variable(config[CONF_ROOM_HUMIDITY])))
