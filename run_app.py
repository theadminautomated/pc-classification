#!/usr/bin/env python
"""Records Classifier GUI Launcher – Production.

Loads and runs the main GUI app. LLM/model/service logic is invoked as needed by the app.
No dummy/test/stub code—this is the real deal.
"""

import logging
import sys
from pathlib import Path
import subprocess
try:
    import requests  # type: ignore
except Exception:  # pragma: no cover - fallback for minimal environments
    import json as _json
    from urllib import request as _urlreq

    class _Resp:
        def __init__(self, text: str):
            self.text = text

        def json(self):
            return _json.loads(self.text)

        def raise_for_status(self):
            pass

    class requests:  # type: ignore
        @staticmethod
        def post(url, json=None, headers=None, timeout=10):
            data = _json.dumps(json or {}).encode()
            req = _urlreq.Request(url, data=data, headers=headers or {}, method="POST")
            with _urlreq.urlopen(req, timeout=timeout) as resp:
                text = resp.read().decode()
            return _Resp(text)
from config import CONFIG

def main():
    """Main entry point for the Records Classifier GUI app."""
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.info("Starting Records Classifier GUI...")

    # Add the project root to Python path
    script_dir = Path(__file__).resolve().parent
    if str(script_dir) not in sys.path:
        sys.path.insert(0, str(script_dir))    # Add the RecordsClassifierGui package directory to Python path
    package_dir = script_dir / "RecordsClassifierGui"
    if str(package_dir) not in sys.path:
        sys.path.insert(0, str(package_dir))

    # Preload the model to avoid timeouts on first request
    try:
        subprocess.run([
            "ollama",
            "run",
            "pierce-county-records-classifier-phi2",
        ], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        url = f"{CONFIG.ollama_url}/api/generate"
        requests.post(
            url,
            json={"model": CONFIG.model_name, "prompt": "warmup", "stream": False},
            timeout=10,
        )
        logger.info("Preloaded model %s", CONFIG.model_name)
    except Exception as exc:
        logger.warning("Model preloading failed: %s", exc)

    try:
        from RecordsClassifierGui.gui.app import RecordsClassifierApp
        logger.info("Imported RecordsClassifierApp successfully.")

        # ---- Real production launch ----
        # Start Tkinter mainloop
        app = RecordsClassifierApp()
        app.mainloop()

        # After mainloop exits, close the asyncio loop properly
        logger.info("Application closing. Finalizing asyncio tasks...")
        import asyncio
        if hasattr(app, 'async_loop') and app.async_loop.is_running():
            tasks = [task for task in asyncio.all_tasks(loop=app.async_loop) if not task.done()]
            if tasks:
                logger.info("Cancelling %s outstanding asyncio tasks...", len(tasks))
                for task in tasks:
                    task.cancel()
                app.async_loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))
            logger.info("Stopping asyncio event loop...")
            if not app.async_loop.is_closed():
                app.async_loop.run_until_complete(app.async_loop.shutdown_asyncgens())
                app.async_loop.close()
            logger.info("Asyncio event loop closed")
        elif hasattr(app, 'async_loop') and not app.async_loop.is_closed():
            logger.info("Asyncio loop was not running but is not closed. Attempting cleanup...")
            app.async_loop.run_until_complete(app.async_loop.shutdown_asyncgens())
            app.async_loop.close()
            logger.info("Asyncio event loop closed")
        else:
            logger.info("No active/unclosed asyncio loop found on app instance")
        # ---- End real launch ----

    except ImportError as e:
        logger.error("Error importing RecordsClassifierApp: %s", e)
        logger.error("Python path: %s", sys.path)
        sys.exit(1)

    logger.info("App run complete.")

if __name__ == "__main__":
    main()