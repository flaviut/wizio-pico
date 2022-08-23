# WizIO 2022 Georgi Angelov
#   http://www.wizio.eu/
#   https://github.com/Wiz-IO/wizio-pico

from common import *


def dev_init(env, platform):
    env.platform = platform
    env.framework_dir = env.PioPlatform().get_package_dir("framework-wizio-pico")
    env.libs = []
    dev_compiler(env, "ARDUINO")
    dev_create_template(env)
    core = env.BoardConfig().get("build.core")
    variant = env.BoardConfig().get("build.variant")
    PLATFORM_DIR = pjoin(env.framework_dir, platform)
    env.Append(
        CPPDEFINES=["ARDUINO=200"],
        CPPPATH=[
            pjoin(PLATFORM_DIR, platform),
            pjoin(PLATFORM_DIR, "cores", core),
            pjoin(PLATFORM_DIR, "variants", variant),
        ],
        LIBSOURCE_DIRS=[pjoin(PLATFORM_DIR, "libraries", core)],
        LIBPATH=[pjoin(PLATFORM_DIR, "libraries", core)],
    )
    dev_config_board(env)
    OBJ_DIR = pjoin("$BUILD_DIR", platform, "arduino")
    env.BuildSources(pjoin(OBJ_DIR, "arduino"), pjoin(PLATFORM_DIR, platform))
    env.BuildSources(pjoin(OBJ_DIR, "core"), pjoin(PLATFORM_DIR, "cores", core))
    env.BuildSources(
        pjoin(OBJ_DIR, "variant"), pjoin(PLATFORM_DIR, "variants", variant)
    )
    dev_finalize(env)
