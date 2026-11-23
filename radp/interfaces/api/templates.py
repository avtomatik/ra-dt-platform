from fastapi.templating import Jinja2Templates

from radp.config.paths import TEMPLATE_DIR

templates = Jinja2Templates(directory=str(TEMPLATE_DIR))
