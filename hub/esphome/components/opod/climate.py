import esphome.codegen as cg
from esphome.components import climate
import esphome.config_validation as cv

from . import CONF_OPOD_ID, CONF_ZONE, ZONE_SCHEMA, opod_ns

DEPENDENCIES = ["opod"]

OpodClimate = opod_ns.class_("OpodClimate", climate.Climate, cg.Component)

CONFIG_SCHEMA = climate.climate_schema(OpodClimate).extend(ZONE_SCHEMA).extend(cv.COMPONENT_SCHEMA)


async def to_code(config):
    var = await climate.new_climate(config)
    await cg.register_component(var, config)
    hub = await cg.get_variable(config[CONF_OPOD_ID])
    cg.add(var.set_parent(hub, config[CONF_ZONE]))
    cg.add(hub.register_climate(config[CONF_ZONE], var))
