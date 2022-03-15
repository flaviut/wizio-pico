import os
import shlex
import subprocess


def picoprobe_upload(target, source, env):
    elf_name = os.path.join(env.get("BUILD_DIR"), env.get("PROGNAME")) + ".elf"
    if env.GetProjectOption("upload_protocol") == "picoprobe":
        # Gets Picoprobe configuration
        picoprobe = env.BoardConfig().__dict__["_manifest"]["debug"]["tools"][
            "picoprobe"
        ]

        pico_ocd_dir = env.PioPlatform().get_package_dir("tool-pico-openocd")

        print("Flashing through picoprobe...")
        subprocess.run(
            [
                os.path.join(
                    env.PioPlatform().get_package_dir("tool-pico-openocd"),
                    picoprobe["server"]["executable"],
                )
            ]
            + [
                arg.replace("$PACKAGE_DIR", pico_ocd_dir)
                for arg in picoprobe["server"]["arguments"]
            ]
            + ["-c", f"program {shlex.quote(elf_name)} verify reset exit"],
            check=True,
        )
        print("Done.")
