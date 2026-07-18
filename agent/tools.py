from __future__ import annotations

import asyncio
import shutil
import subprocess
import sys
from pathlib import Path

from langchain_core.tools import BaseTool, tool


class OrionTools:
    """
    Local automation tools available to ORION.

    Retrieval is handled by RetrieveNode.
    """

    @staticmethod
    async def _run(*args: str) -> tuple[bool, str]:
        try:
            process = await asyncio.create_subprocess_exec(
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                return True, stdout.decode().strip()

            return False, stderr.decode().strip()

        except Exception as exc:
            return False, str(exc)

    def get_tools(self) -> list[BaseTool]:
        @tool
        async def open_browser() -> str:
            """
            Open the default web browser.
            """
            try:
                import webbrowser

                webbrowser.open("")
                return "Opened the default web browser."
            except Exception as exc:
                return f"Failed to open browser: {exc}"

        @tool
        async def open_url(url: str = "www.google.com") -> str:
            """
            Open a URL in the default web browser.
            """
            try:
                import webbrowser

                webbrowser.open(url)
                return f"Opened {url}."
            except Exception as exc:
                return f"Failed to open URL: {exc}"

        @tool
        async def open_terminal() -> str:
            """
            Open a terminal window.
            """
            try:
                if sys.platform.startswith("linux"):
                    candidates = [
                        "kitty",
                        "wezterm",
                        "gnome-terminal",
                        "konsole",
                        "xfce4-terminal",
                        "alacritty",
                        "xterm",
                    ]

                    for terminal in candidates:
                        executable = shutil.which(terminal)
                        if executable:
                            subprocess.Popen([executable])
                            return f"Opened {terminal}."

                    return "No supported terminal emulator was found."

                if sys.platform == "darwin":
                    subprocess.Popen(["open", "-a", "Terminal"])
                    return "Opened Terminal."

                if sys.platform == "win32":
                    subprocess.Popen(["cmd"])
                    return "Opened Command Prompt."

                return "Unsupported operating system."

            except Exception as exc:
                return f"Failed to open terminal: {exc}"

        @tool
        async def open_file_manager() -> str:
            """
            Open the system file manager.
            """
            try:
                if sys.platform.startswith("linux"):
                    subprocess.Popen(["xdg-open", str(Path.home())])

                elif sys.platform == "darwin":
                    subprocess.Popen(["open", str(Path.home())])

                elif sys.platform == "win32":
                    subprocess.Popen(["explorer", str(Path.home())])

                else:
                    return "Unsupported operating system."

                return "Opened the file manager."

            except Exception as exc:
                return f"Failed to open file manager: {exc}"

        @tool
        async def launch_application(
            application: str,
        ) -> str:
            """
            Launch an installed application by name.

            Examples:
            - Firefox
            - code
            - spotify
            - discord
            """

            try:
                executable = shutil.which(application)

                if executable is None:
                    return f"Application '{application}' was not found."

                subprocess.Popen([executable])

                return f"Launched '{application}'."

            except Exception as exc:
                return f"Failed to launch '{application}': {exc}"

        @tool
        async def execute_shell_command(
            command: str,
        ) -> str:
            """
            Execute a local shell command.

            Use only for local automation tasks.
            """

            try:
                process = await asyncio.create_subprocess_shell(
                    command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )

                stdout, stderr = await process.communicate()

                output = stdout.decode().strip()
                error = stderr.decode().strip()

                if process.returncode == 0:
                    return output or "Command completed successfully."

                return error or f"Command exited with code {process.returncode}."

            except Exception as exc:
                return f"Failed to execute command: {exc}"

        return [
            open_browser,
            open_terminal,
            open_file_manager,
            launch_application,
            execute_shell_command,
        ]
