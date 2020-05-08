from crowdsorting import app
import logging

logging.info('starting crowdsorting')
app.run(debug=True, use_reloader=True)
