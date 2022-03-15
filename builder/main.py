# WizIO 2021 Georgi Angelov
#   http://www.wizio.eu/
#   https://github.com/Wiz-IO/wizio-pico

from __future__ import print_function

import sys
from os.path import join

from SCons.Script import (
    AlwaysBuild,
    COMMAND_LINE_TARGETS,
    Default,
    DefaultEnvironment,
    Builder,
    ARGUMENTS,
)
from platformio.util import get_serial_ports

from pioasm import dev_pioasm


def BeforeUpload(target, source, env):  # pylint: disable=W0613,W0621
    upload_options = {}
    if "BOARD" in env:
        upload_options = env.BoardConfig().get("upload", {})

    env.AutodetectUploadPort()
    before_ports = get_serial_ports()

    if upload_options.get("use_1200bps_touch", False):
        env.TouchSerialPort("$UPLOAD_PORT", 1200)

    if upload_options.get("wait_for_upload_port", False):
        env.Replace(UPLOAD_PORT=env.WaitForNewSerialPort(before_ports))


def generate_uf2(target, source, env):
    elf_file = target[0].get_path()
    env.Execute(
        " ".join(
            [
                "elf2uf2",
                '"%s"' % elf_file,
                '"%s"' % elf_file.replace(".elf", ".uf2"),
            ]
        )
    )


env = DefaultEnvironment()
platform = env.PioPlatform()
board = env.BoardConfig()

env.Replace(
    AR="arm-none-eabi-ar",
    AS="arm-none-eabi-as",
    CC="arm-none-eabi-gcc",
    CXX="arm-none-eabi-g++",
    GDB="arm-none-eabi-gdb",
    OBJCOPY="arm-none-eabi-objcopy",
    RANLIB="arm-none-eabi-ranlib",
    SIZETOOL="arm-none-eabi-size",
    ARFLAGS=["rc"],
    SIZEPROGREGEXP=r"^(?:\.text|\.data|\.rodata|\.text.align|\.ARM.exidx)\s+(\d+).*",
    SIZEDATAREGEXP=r"^(?:\.data|\.bss|\.noinit)\s+(\d+).*",
    SIZECHECKCMD="$SIZETOOL -A -d $SOURCES",
    SIZEPRINTCMD="$SIZETOOL -B -d $SOURCES",
    PROGSUFFIX=".elf",
)

# Allow user to override via pre:script
if env.get("PROGNAME", "program") == "program":
    env.Replace(PROGNAME="firmware")


env.Append(
    BUILDERS=dict(
        ElfToBin=Builder(
            action=env.VerboseAction(
                " ".join(["$OBJCOPY", "-O", "binary", "$SOURCES", "$TARGET"]),
                "Building $TARGET",
            ),
            suffix=".bin",
        ),
        ElfToHex=Builder(
            action=env.VerboseAction(
                " ".join(
                    ["$OBJCOPY", "-O", "ihex", "-R", ".eeprom", "$SOURCES", "$TARGET"]
                ),
                "Building $TARGET",
            ),
            suffix=".hex",
        ),
    )
)

print(f"<<<<<<<<<<<< {board.get('name').upper()} 2021 Georgi Angelov >>>>>>>>>>>>")

dev_pioasm(env)

#
# Target: Build executable and linkable firmware
#

target_elf = None
if "nobuild" in COMMAND_LINE_TARGETS:
    target_elf = join("$BUILD_DIR", "${PROGNAME}.elf")
    target_firm = join("$BUILD_DIR", "${PROGNAME}.bin")
else:
    target_elf = env.BuildProgram()
    target_firm = env.ElfToBin(join("$BUILD_DIR", "${PROGNAME}"), target_elf)
    env.Depends(target_firm, "checkprogsize")
target_buildprog = env.Alias("buildprog", target_firm, target_firm)
AlwaysBuild(target_buildprog)
env.AddPostAction(target_elf, env.VerboseAction(generate_uf2, "Generating UF2 image"))

#
# Target: Print binary size
#

target_size = env.Alias(
    "size", target_elf, env.VerboseAction("$SIZEPRINTCMD", "Calculating size $SOURCE")
)
AlwaysBuild(target_size)

#
# Target: Upload by default .bin file
#

debug_tools = env.BoardConfig().get("debug.tools", {})
upload_protocol = env.subst("$UPLOAD_PROTOCOL") or "picotool"
upload_actions = []
upload_source = target_firm

if upload_protocol == "picotool":
    env.Replace(
        UPLOADER=join(platform.get_package_dir("tool-rp2040tools") or "", "rp2040load"),
        UPLOADERFLAGS=["-v", "-D"],
        UPLOADCMD='"$UPLOADER" $UPLOADERFLAGS $SOURCES',
    )
    upload_actions = [
        env.VerboseAction(BeforeUpload, "Looking for upload port..."),
        env.VerboseAction("$UPLOADCMD", "Uploading $SOURCE"),
    ]

    upload_source = target_elf

elif upload_protocol in debug_tools:
    openocd_args = ["-d%d" % (2 if int(ARGUMENTS.get("PIOVERBOSE", 0)) else 1)]
    openocd_args.extend(
        debug_tools.get(upload_protocol).get("server").get("arguments", [])
    )
    if env.GetProjectOption("debug_speed"):
        openocd_args.extend(
            ["-c", "adapter speed %s" % env.GetProjectOption("debug_speed")]
        )
    openocd_args.extend(
        [
            "-c",
            "program {$SOURCE} %s verify reset; shutdown;"
            % board.get("upload.offset_address", ""),
        ]
    )
    openocd_args = [
        f.replace(
            "$PACKAGE_DIR", platform.get_package_dir("tool-openocd-raspberrypi") or ""
        )
        for f in openocd_args
    ]
    env.Replace(
        UPLOADER="openocd",
        UPLOADERFLAGS=openocd_args,
        UPLOADCMD="$UPLOADER $UPLOADERFLAGS",
    )
    upload_actions = [env.VerboseAction("$UPLOADCMD", "Uploading $SOURCE")]
    upload_source = target_elf

# custom upload tool
elif upload_protocol == "custom":
    upload_actions = [env.VerboseAction("$UPLOADCMD", "Uploading $SOURCE")]

if not upload_actions:
    sys.stderr.write(f"Warning! Unknown upload protocol {upload_protocol}\n")

AlwaysBuild(env.Alias("upload", upload_source, upload_actions))

#
# Default targets
#

Default([target_buildprog, target_size])
