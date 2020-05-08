from crowdsorting import app
import logging

logging.info('starting crowdsorting')
app.run(debug=True, use_reloader=True)

# from waitress import serve
# serve(app, listen='0.0.0.0:5000', threads=1)
