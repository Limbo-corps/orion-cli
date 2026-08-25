"""
Application runtime.

The runtime is the top-level lifecycle manager for Orion.

It owns long-lived components (lifecycles), starts them in registration
order, and shuts them down in reverse order.
"""

from __future__ import annotations

from typing_extensions import override

from orion.runtime.lifecycle import Lifecycle


class OrionRuntime(Lifecycle):
    """
    Top-level runtime for Orion.
    """

    def __init__(self) -> None:
        self._lifecycles: list[Lifecycle] = []
        self._started = False

    def register(
        self,
        lifecycle: Lifecycle,
    ) -> None:
        """
        Register a lifecycle component.

        Components are started in registration order and stopped in
        reverse registration order.

        Raises:
            RuntimeError:
                If the runtime has already been started.
        """
        if self._started:
            raise RuntimeError(
                "Cannot register components after the runtime has started."
            )

        self._lifecycles.append(lifecycle)

    @override
    async def startup(self) -> None:
        """
        Start the runtime.
        """
        if self._started:
            raise RuntimeError("Runtime has already been started.")

        for lifecycle in self._lifecycles:
            await lifecycle.startup()

        self._started = True

    @override
    async def shutdown(self) -> None:
        """
        Shutdown the runtime.
        """
        if not self._started:
            return

        errors: list[Exception] = []

        for lifecycle in reversed(self._lifecycles):
            try:
                await lifecycle.shutdown()
            except Exception as exc:
                errors.append(exc)

        self._started = False

        if errors:
            raise ExceptionGroup(
                "One or more runtime components failed to shut down.",
                errors,
            )
