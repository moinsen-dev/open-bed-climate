import esphome.codegen as cg
from esphome.components import datetime, switch, time
import esphome.config_validation as cv
from esphome.const import CONF_TIME_ID

from . import opod_ns
from .climate import OpodClimate

DEPENDENCIES = ["opod", "time"]

CONF_CLIMATE_ID = "climate_id"
CONF_POINTS = "points"
CONF_AT = "at"
CONF_TEMPERATURE = "temperature"
CONF_WAKE_TIME = "wake_time"
CONF_WAKE_RAMP = "wake_ramp"
CONF_WAKE_TEMPERATURE = "wake_temperature"

OpodProgram = opod_ns.class_("OpodProgram", switch.Switch, cg.Component)

# Same limits and default curve as software/opod/src/opod/schedule.py.
SETPOINT = cv.float_range(min=13.0, max=43.0)
DEFAULT_POINTS = [(0, 24.0), (30, 21.0), (120, 20.0), (300, 23.0), (420, 25.0)]
MAX_POINTS = 16


def _sorted_points(points):
    mins = [p[CONF_AT].total_minutes for p in points]
    if mins != sorted(mins):
        raise cv.Invalid("points must be sorted by 'at'")
    return points


POINT_SCHEMA = cv.Schema(
    {
        cv.Required(CONF_AT): cv.positive_time_period_minutes,
        cv.Required(CONF_TEMPERATURE): SETPOINT,
    }
)

CONFIG_SCHEMA = (
    switch.switch_schema(OpodProgram, icon="mdi:sleep")
    .extend(
        {
            cv.Required(CONF_CLIMATE_ID): cv.use_id(OpodClimate),
            cv.Required(CONF_TIME_ID): cv.use_id(time.RealTimeClock),
            cv.Optional(CONF_WAKE_TIME): cv.use_id(datetime.TimeEntity),
            cv.Optional(CONF_POINTS): cv.All(
                cv.ensure_list(POINT_SCHEMA), cv.Length(min=1, max=MAX_POINTS), _sorted_points
            ),
            cv.Optional(CONF_WAKE_RAMP, default="30min"): cv.All(
                cv.positive_time_period_minutes, cv.Range(min=cv.TimePeriod(minutes=1))
            ),
            cv.Optional(CONF_WAKE_TEMPERATURE, default=32.0): SETPOINT,
        }
    )
    .extend(cv.COMPONENT_SCHEMA)
)


async def to_code(config):
    var = await switch.new_switch(config)
    await cg.register_component(var, config)
    clim = await cg.get_variable(config[CONF_CLIMATE_ID])
    cg.add(var.set_climate(clim))
    cg.add(clim.set_program(var))
    cg.add(var.set_time(await cg.get_variable(config[CONF_TIME_ID])))
    if CONF_WAKE_TIME in config:
        cg.add(var.set_wake_time(await cg.get_variable(config[CONF_WAKE_TIME])))
    if CONF_POINTS in config:
        points = [(p[CONF_AT].total_minutes, p[CONF_TEMPERATURE]) for p in config[CONF_POINTS]]
    else:
        points = DEFAULT_POINTS
    for minute, c in points:
        cg.add(var.add_point(minute, c))
    cg.add(var.set_wake_ramp(config[CONF_WAKE_RAMP].total_minutes, config[CONF_WAKE_TEMPERATURE]))
