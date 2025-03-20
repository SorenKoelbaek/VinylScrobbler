"""Common logger configuration."""

import os
import sys
import logging


class SingleLineFormatter(logging.Formatter):
	"""Custom formatter to log messages in a single line to prevent SQLAlchemy statements to show as multiple lines in CloudWatch."""

	def format(self, record):
		"""Format the log message."""
		original = super(SingleLineFormatter, self).format(record)
		return original.replace("\n", " ")


def get_logger(name=__name__, formatter=logging.Formatter):
	"""Get a logger with the specified name and formatter.

	:param name: The name of the logger. Set it to __name__ to get the local module name
	:param formatter: How the logs should be formatted. If blank, the default formatter will be used.
	"""
	LOGLEVEL = os.environ.get("LOGLEVEL", "INFO")
	logger = logging.getLogger(name)
	logger.setLevel(LOGLEVEL)
	logger.propagate = False
	if not logger.hasHandlers():
		stream_handler = logging.StreamHandler(sys.stdout)
		log_formatter = formatter(
			"%(asctime)s [%(processName)s: %(process)s] [%(threadName)s: %(thread)s] [%(levelname)s] %(name)s: %(message)s"
		)
		stream_handler.setFormatter(log_formatter)
		logger.addHandler(stream_handler)
	return logger
