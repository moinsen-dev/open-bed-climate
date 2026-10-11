import esphome.codegen as cg
from esphome.components import button
import esphome.config_validation as cv
from esphome.const import ENTITY_CATEGORY_CONFIG

from . import CONF_OPOD_ID, CONF_ZONE, OpodHub, opod_ns

DEPENDENCIES = ["opod"]

OpodPrimeButton = opod_ns.class_("OpodPrimeButton", button.Button, cg.Component)
OpodClearFaultsButton = opod_ns.class_("OpodClearFaultsButton", button.Button, cg.Component)

CONF_PRIME = "prime"
CONF_CLEAR_FAULTS = "clear_faults"

CONFIG_SCHEMA = cv.Schema(
    {
        cv.GenerateID(CONF_OPOD_ID): cv.use_id(OpodHub),
        cv.Optional(CONF_ZONE): cv.int_range(min=0, max=1),
        cv.Optional(CONF_PRIME): button.button_schema(
            OpodPrimeButton, icon="mdi:water-sync", entity_category=ENTITY_CATEGORY_CONFIG
        ),
        cv.Optional(CONF_CLEAR_FAULTS): button.button_schema(
            OpodClearFaultsButton, icon="mdi:alert-remove", entity_category=ENTITY_CATEGORY_CONFIG
        ),
    }
)


async def to_code(config):
    hub = await cg.get_variable(config[CONF_OPOD_ID])
    if CONF_PRIME in config:
        b = await button.new_button(config[CONF_PRIME])
        await cg.register_component(b, config[CONF_PRIME])
        cg.add(b.set_hub(hub))
    if CONF_CLEAR_FAULTS in config:
        if CONF_ZONE not in config:
            raise cv.Invalid("'clear_faults' needs a 'zone'")
        b = await button.new_button(config[CONF_CLEAR_FAULTS])
        await cg.register_component(b, config[CONF_CLEAR_FAULTS])
        cg.add(b.set_parent(hub, config[CONF_ZONE]))
