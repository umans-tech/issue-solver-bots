from mangum import Mangum

from issue_solver.webapi.main import app

handler = Mangum(app)
