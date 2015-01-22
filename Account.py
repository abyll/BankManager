import BankManager
from BankManager import toDollar

class Transaction:
	def __init__(self, date, action, amount, desc):
		self.date = date		# Date of transaction (going to be month#)
		self.action = action	#
		self.amount = amount	# amount - going to be positive or negative, depending on transaction
		self.description = desc # Further details

	def __str__(self):
		return "{%2s} %s (%s): $%.2f" %(self.date, self.action, self.description, toDollar(self.amount))

class Delinquency:
	def __init__(self, date, due, fee):
		self.date = date
		self.due = due
		self.fee = fee

	def __str__(self):
		return "{%s} $%.2f, $%.2f" %(self.date, toDollar(self.due), toDollar(self.fee))

	def amount(self):
		return self.due + self.fee

class Account:
	def __init__(self, fname, lname, acctID):
		self.firstname = 	fname
		self.lastname = 	lname
		self.accountID = 	acctID
		self.savings_balance = 0		# Current Savings amount - Savings account is 'closed' if this is empty
		self.loan_balance = 0				# Current Loan amount - loan is 'paid and closed' if this is empty.
		self.loan_principal = 0
		self.savings_transactions = []
		self.savings_pending = []
		self.loan_transactions = []
		self.loan_pending = []
		self.delinquencies = []		# Unpaid bills will be collected as delinquencies, with a fee added for each one.
		self.bill = 0				# Store bill from previous month, for informational purposes.

	def hasSavings(self):
		"""We have a savings account if we had any money this month
		it's only closed at the end of the month, if all money is withdrawn.
		Note: it's still open if the account opened from 0, and was immediately withdrawn to empty"""
		return self.savings_balance > 0 or len(self.savings_pending) > 0

	def hasLoan(self):
		"Like hasSavings, the loan is only closed after the month its balance goes to 0."
		return self.loan_balance > 0 or self.loan_pending

	def SavingsAvailable(self):
		"""Calculates 'available' amount in savings, accounting for pending transactions"""
		total = self.savings_balance
		for trans in self.savings_pending:
			total += trans.amount
		return total

	def LoanTotal(self):
		"""Calculates 'actual' amount on loan, including from pending transactions"""
		total = self.loan_balance
		for trans in self.loan_pending:
			total += trans.amount
		return total

	def ProcessPending(self):
		for x in self.savings_pending:
			self.savings_balance += x.amount
		self.savings_transactions += self.savings_pending
		self.savings_pending = []
		for x in self.loan_pending:
			self.loan_balance += x.amount
		self.loan_transactions += self.loan_pending
		self.loan_pending = []

