# WizIO 2021 Georgi Angelov
#   http://www.wizio.eu/
#   https://github.com/Wiz-IO/wizio-pico

from os.path import join as pjoin

from SCons.Builder import Builder
from colorama import Fore

from pico import fix_old_new_stdio, add_sdk

bynary_type_info = []


def dev_create_template(env):
    ini = pjoin(env.subst("$PROJECT_DIR"), "platformio.ini")
    f = open(ini, "r")
    txt = f.read()
    f.close()
    with open(ini, "a+") as f:
        if "monitor_port" not in txt:
            f.write("\n;monitor_port = SERIAL_PORT\n")
        if "monitor_speed" not in txt:
            f.write(";monitor_speed = 115200\n")
        if "build_flags" not in txt:
            f.write("\n;build_flags = \n")
        if "lib_deps" not in txt:
            f.write("\n;lib_deps = \n")


def dev_nano(env):
    enable_nano = env.BoardConfig().get("build.nano", "enable")  # no <sys/lock>
    nano = []
    if enable_nano == "enable":
        nano = ["-specs=nano.specs", "-u", "_printf_float", "-u", "_scanf_float"]
    if len(nano) > 0:
        print("  * SPECS        :", nano[0][7:])
    else:
        print("  * SPECS        : default")
    return nano


def dev_compiler(env):
    env.sdk = env.BoardConfig().get("build.sdk", "SDK")  # get/set default SDK
    print()
    print(
        Fore.BLUE
        + "%s RASPBERRYPI PI PICO RP2040 ( PICO - %s )"
        % (env.platform.upper(), env.sdk.upper())
    )
    cortex = ["-march=armv6-m", "-mcpu=cortex-m0plus", "-mthumb"]
    env.heap_size = env.BoardConfig().get("build.heap", "2048")
    optimization = env.BoardConfig().get("build.optimization", "-Os")
    stack_size = env.BoardConfig().get("build.stack", "2048")
    print("  * OPTIMIZATION :", optimization)
    if "ARDUINO" == env.get("PROGNAME"):
        if "freertos" in env.GetProjectOption(
            "lib_deps", []
        ) or "USE_FREERTOS" in env.get("CPPDEFINES"):
            pass
        else:
            print("  * STACK        :", stack_size)
            print("  * HEAP         : maximum")
    else:
        print("  * STACK        :", stack_size)
        print("  * HEAP         :", env.heap_size)
    fix_old_new_stdio(env)
    env.Append(
        ASFLAGS=[cortex, "-x", "assembler-with-cpp"],
        CPPPATH=[
            pjoin("$PROJECT_DIR", "src"),
            pjoin("$PROJECT_DIR", "lib"),
            pjoin("$PROJECT_DIR", "include"),
            pjoin(env.framework_dir, "wizio", "pico"),
            pjoin(env.framework_dir, "wizio", "newlib"),
            pjoin(env.framework_dir, env.sdk, "include"),
            pjoin(env.framework_dir, env.sdk, "cmsis", "include"),  #
        ],
        CPPDEFINES=[
            "NDEBUG",
            "PICO_ON_DEVICE=1",
            "PICO_HEAP_SIZE=" + env.heap_size,
            "PICO_STACK_SIZE=" + stack_size,
        ],
        CCFLAGS=[
            cortex,
            optimization,
            "-fdata-sections",
            "-ffunction-sections",
            "-Wall",
            "-Wextra",
            "-Wfatal-errors",
            "-Wno-sign-compare",
            "-Wno-type-limits",
            "-Wno-unused-parameter",
            "-Wno-unused-function",
            "-Wno-unused-but-set-variable",
            "-Wno-unused-variable",
            "-Wno-unused-value",
            "-Wno-strict-aliasing",
            "-Wno-maybe-uninitialized",
        ],
        CFLAGS=[
            cortex,
            "-Wno-discarded-qualifiers",
            "-Wno-ignored-qualifiers",
            "-Wno-attributes",  #
        ],
        CXXFLAGS=[
            "-fno-rtti",
            "-fno-exceptions",
            "-fno-threadsafe-statics",
            "-fno-non-call-exceptions",
            "-fno-use-cxa-atexit",
        ],
        LINKFLAGS=[
            cortex,
            optimization,
            "-nostartfiles",
            "-Xlinker",
            "--gc-sections",
            "-Wl,--gc-sections",
            "--entry=_entry_point",
            dev_nano(env),
        ],
        LIBSOURCE_DIRS=[
            pjoin(env.framework_dir, "library"),
        ],
        LIBPATH=[pjoin(env.framework_dir, "library"), pjoin("$PROJECT_DIR", "lib")],
        LIBS=["m", "gcc"],
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
    )


def add_libraries(env):  # is PIO LIB-s
    if "freertos" in env.GetProjectOption("lib_deps", []) or "USE_FREERTOS" in env.get(
        "CPPDEFINES"
    ):
        env.Append(
            CPPPATH=[pjoin(pjoin(env.framework_dir, "library", "freertos"), "include")]
        )
        print("  * RTOS         : FreeRTOS")
        if "USE_FREERTOS" not in env.get("CPPDEFINES"):
            env.Append(CPPDEFINES=["USE_FREERTOS"])

    if "cmsis-dap" in env.GetProjectOption("lib_deps", []):
        env.Append(
            CPPDEFINES=["DAP"],
        )


def add_boot(env):
    boot = env.BoardConfig().get("build.boot", "w25q080")  # get boot
    if "w25q080" != boot and "$PROJECT_DIR" in boot:
        boot = boot.replace("$PROJECT_DIR", env["PROJECT_DIR"]).replace("\\", "/")
    bynary_type_info.append(boot)
    env.BuildSources(
        pjoin("$BUILD_DIR", env.platform, "wizio", "boot"),
        pjoin(env.framework_dir, "boot", boot),
    )


def add_bynary_type(env):
    add_boot(env)
    bynary_type = env.BoardConfig().get("build.bynary_type", "default")
    env.address = env.BoardConfig().get("build.address", "empty")
    linker = env.BoardConfig().get("build.linker", "empty")
    if "empty" != linker and "$PROJECT_DIR" in linker:
        linker = linker.replace("$PROJECT_DIR", env["PROJECT_DIR"]).replace("\\", "/")
    if "copy_to_ram" == bynary_type:
        if "empty" == env.address:
            env.address = "0x10000000"
        if "empty" == linker:
            linker = "memmap_copy_to_ram.ld"
        env.Append(CPPDEFINES=["PICO_COPY_TO_RAM"])
    elif "no_flash" == bynary_type:
        if "empty" == env.address:
            env.address = "0x20000000"
        if "empty" == linker:
            linker = "memmap_no_flash.ld"
        env.Append(CPPDEFINES=["PICO_NO_FLASH"])
    elif "blocked_ram" == bynary_type:
        print("TODO: blocked_ram is not supported yet")
        exit(0)
        if "empty" == env.address:
            env.address = ""
        if "empty" == linker:
            linker = ""
        env.Append(CPPDEFINES=["PICO_USE_BLOCKED_RAM"])
    else:  # default
        if "empty" == env.address:
            env.address = "0x10000000"
        if "empty" == linker:
            linker = "memmap_default.ld"
    env.Append(
        LDSCRIPT_PATH=pjoin(
            env.framework_dir, env.sdk, "pico", "pico_standard_link", linker
        )
    )
    bynary_type_info.append(linker)
    bynary_type_info.append(env.address)
    print("  * BINARY TYPE  :", bynary_type, bynary_type_info)
    add_libraries(env)


def dev_finalize(env):
    # WIZIO
    env.BuildSources(
        pjoin("$BUILD_DIR", env.platform, "wizio"), pjoin(env.framework_dir, "wizio")
    )
    # SDK
    add_bynary_type(env)
    add_sdk(env)
    env.Append(LIBS=env.libs)
    print()
