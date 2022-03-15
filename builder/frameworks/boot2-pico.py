# WizIO 2021 Georgi Angelov
#   http://www.wizio.eu/
#   https://github.com/Wiz-IO/wizio-pico

from common import *


def dev_create_asm(target, source, env):
    py = pjoin(env.framework_dir, env.sdk, "boot_stage2", "pad_checksum")
    dir = pjoin(env["BUILD_DIR"], env["PROGNAME"])
    env.Execute("python " + py + " -s 0xffffffff " + dir + ".bin " + dir + ".S")
    f = open(dir + ".S", "a")
    f.write('\n#include "../link.S')
    f.close()


def dev_init(env, platform):
    print("RASPBERRYPI PI PICO RP2040 BOOT STAGE 2 COMPILER")
    env.platform = platform
    env.framework_dir = env.PioPlatform().get_package_dir("framework-wizio-pico")
    env.libs = []
    dev_create_template(env)
    env.Append(
        ASFLAGS=[env.cortex, "-x", "assembler-with-cpp"],
        CPPDEFINES=["PICO_FLASH_SPI_CLKDIV=2"],
        CPPPATH=[
            pjoin("$PROJECT_DIR", "include"),
            pjoin(env.framework_dir, env.sdk, "include"),
            pjoin(env.framework_dir, env.sdk, "boards"),
            pjoin(env.framework_dir, env.sdk, "boot_stage2", "asminclude"),
        ],
        CFLAGS=[
            env.cortex,
            "-Os",
            "-fdata-sections",
            "-ffunction-sections",
            "-Wall",
            "-Wfatal-errors",
            "-Wstrict-prototypes",
        ],
        LINKFLAGS=[
            env.cortex,
            "-Os",
            "-nostartfiles",
            "-nostdlib",
            "-Wall",
            "-Wfatal-errors",
            "--entry=_stage2_boot",
        ],
        LDSCRIPT_PATH=[
            pjoin(env.framework_dir, env.sdk, "boot_stage2", "boot_stage2.ld")
        ],
        BUILDERS=dict(
            ElfToBin=Builder(
                action=env.VerboseAction(
                    " ".join(
                        [
                            "$OBJCOPY",
                            "-O",
                            "binary",
                            "$SOURCES",
                            "$TARGET",
                        ]
                    ),
                    "Building $TARGET",
                ),
                suffix=".bin",
            )
        ),
        UPLOADCMD=dev_create_asm,
    )

    libs = []
    env.Append(LIBS=libs)

    # Select file, Clean, Upload, Get boot2.S from build folder

    env.BuildSources(
        pjoin("$BUILD_DIR", "BOOT2"),
        pjoin(env.framework_dir, env.sdk, "boot_stage2"),
        src_filter="-<*> +<boot2_w25q080.S>",
    )  # is default
    # env.BuildSources(pjoin("$BUILD_DIR", "BOOT2"), pjoin(env.framework_dir, env.sdk, "boot_stage2"), src_filter="-<*> +<boot2_w25x10cl.S>")
    # env.BuildSources(pjoin("$BUILD_DIR", "BOOT2"), pjoin(env.framework_dir, env.sdk, "boot_stage2"), src_filter="-<*> +<boot2_is25lp080.S>")
    # env.BuildSources(pjoin("$BUILD_DIR", "BOOT2"), pjoin(env.framework_dir, env.sdk, "boot_stage2"), src_filter="-<*> +<boot2_generic_03h.S>")
    # env.BuildSources(pjoin("$BUILD_DIR", "BOOT2"), pjoin(env.framework_dir, env.sdk, "boot_stage2"), src_filter="-<*> +<boot2_usb_blinky.S>")
