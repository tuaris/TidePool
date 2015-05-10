from lib.core.standard import CTransaction
from lib.core.extended import CPosTransaction
from lib.core.extended import CPosTransactionMessage
from lib.core.extended import CTransactionMessage

class TransactionFactory(object):
	def new_transaction(self):
		return CTransaction()

	def build_transaction(self, data):
		# New blank transaction
		transaction = self.new_transaction()
		# Fill data
		transaction.deserialize(data)
		# Ready
		return transaction

class TransactionMessageFactory(TransactionFactory):
	def new_transaction(self):
		return CTransactionMessage('')

class PoSTransactionFactory(TransactionFactory):
	def new_transaction(self):
		return CPosTransaction(0)

class PoSTransactionMessageFactory(TransactionFactory):
	def new_transaction(self):
		return CPosTransactionMessage('', 0)