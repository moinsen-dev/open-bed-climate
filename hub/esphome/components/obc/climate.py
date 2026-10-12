import esphome.codegen as cg
from esphome.components import climate
import esphome.config_validation as cv

from . import CONF_OBC_ID, CONF_ZONE, ZONE_SCHEMA, obc_ns

DEPENDENCIES = ["obc"]

ObcClimate = obc_ns.class_("ObcClimate", climate.Climate, cg.Component)

CONFIG_SCHEMA = climate.climate_schema(ObcClimate).extend(ZONE_SCHEMA).extend(cv.COMPONENT_SCHEMA)


async def to_code(config):
    var = await climate.new_climate(config)
    await cg.register_component(var, config)
    hub = await cg.get_variable(config[CONF_OBC_ID])
    cg.add(var.set_parent(hub, config[CONF_ZONE]))
    cg.add(hub.register_climate(config[CONF_ZONE], var))
