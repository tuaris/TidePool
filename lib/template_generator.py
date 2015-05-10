from block_template import BlockTemplate

import lib.logger
log = lib.logger.get_logger('template_generator')

class BlockTemplateGenerator(object):
	def __init__(self, component_factory):
		# Component factory used for creating core objects like transactions, blocks, and coinbase
		self.component_factory = component_factory

	def new_template(self, timestamper, job_id):
		# Generate a new empty template
		log.debug("New template created")
		return BlockTemplate(self.component_factory, timestamper, job_id)

	def get_extranonce_size(self):
		# This can be obtained from the coinbaser, which is part of the component_factory
		return self.component_factory.coinbaser.get_extranonce_size()
