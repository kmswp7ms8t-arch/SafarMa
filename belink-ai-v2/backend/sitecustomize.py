"""Load local server environment before the application modules are imported.

Python imports ``sitecustomize`` automatically during normal interpreter startup.
Production platforms still inject environment variables directly; ``override=False``
ensures those production values always win.
"""

from dotenv import load_dotenv

load_dotenv(".env.local", override=False)
load_dotenv(".env", override=False)
