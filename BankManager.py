from Account import *
from functools import partial as part
from menusystem.MenuSystem import *
from decimal import *

## Bank Manager
# Holds accounts, handles transactions and processing of accounts
# All currency calculated in cents - Convert to dollars (div by 100) for printing output
#		- Input should be converted from decimal ($[...].XX) to cents immediately

def toDollar(c):
	return float(c) / 100

class BankManager:
	max_accounts = 20
	max_savings = 10000000	# $100,000 - remember, cents.
	min_loan = 500000
	max_loan = 10000000
	delinquency_fee = 5000
	min_loan_payment = 1000
	loan_payment_percentage = 0.01
	def __init__(self, savings_interest, loan_interest):
		self.accounts = []
		self.month = 0		# 0-11 for months
		self.savings_interest = savings_interest 	# yearly interest
		self.loan_interest = loan_interest 			# yearly interest
		self.last_id = 0

	def GetAccount(self, ID):
		for a in self.accounts:
			if a.accountID == ID:
				return a
		raise KeyError(str(ID) + " does not exist")

	def GetAccountByName(self, fname, lname):
		for a in self.accounts:
			if a.firstname == fname and a.lastname == lname:
				return a
		raise KeyError(fname + " " + lname + " does not exist")

	def CreateID(self):
		if self.last_id > 999999: #can't have more than 6-length account number.
			raise RuntimeError("IDs have run out of bounds")
		self.last_id += 1
		return "%06d" %self.last_id

	def CreateAccount(self, first_name, last_name, initial_savings):
		if len(self.accounts) >= self.max_accounts:
			raise RuntimeError("Cannot create more than %d accounts" %self.max_accounts)
		if initial_savings <= 0 or initial_savings > self.max_savings:
			raise ValueError("Savings must be between 0 and %d" %self.max_savings)
		a = Account(first_name, last_name, self.CreateID())
		a.savings_pending.append(Transaction(self.month, "Deposit", initial_savings, "Initial deposit"))
		return a

	def CloseAccount(self, a):
		if a.SavingsAvailable() > 0:
			raise RuntimeError("Cannot close an Account with open savings")
		if a.LoanTotal() > 0:
			raise RuntimeError("Cannot close an Account with an open loan")
		a.ProcessPending()
		self.accounts.remove(a)

	def ForwardMonth(self):

		for a in self.accounts:
			# Add Interest, via a transaction - Only if account still has a balance and isn't closing.
			if a.SavingsAvailable() > 0:
				s_int = int(round(a.SavingsAvailable() * self.savings_interest / 12))
				a.savings_pending.append(Transaction(self.month, "Interest", s_int, "Interest for month"))
			if a.LoanTotal() > 0:
				l_int = int(round(a.LoanTotal() * self.loan_interest / 12))
				a.loan_pending.append(Transaction(self.month, "Interest", l_int, "Interest for month"))

			# Print month's statement
			self.SendStatement(a)

			# Check for delinquency from previous month's bill
			if a.hasLoan():
				loan_payment = 0 # Amount paid this month
				for x in a.loan_pending:
					if x.amount < 0:
						loan_payment += -x.amount # Payments are recorded in negatives
				due = a.bill
				print "%s %s paid $%.2f, owed $%.2f" %(a.firstname, a.lastname, toDollar(loan_payment),toDollar(due))
				if loan_payment < due:
					a.delinquencies.append(Delinquency(self.month, due-loan_payment, self.delinquency_fee))

			print
			#Print bill for loan
			if a.LoanTotal() > 0:
				print "$%.2f left on loan" %(toDollar(a.LoanTotal()))
				self.SendBill(a)

			# Process Transactions
			a.ProcessPending()

		self.month += 1



	def SetSavingsInterest(self, interest):
		if self.month % 12 != 0:
			raise RuntimeError("Unable to set interest outside of January.")

		if  interest < 0.01 or interest > .05:
			raise ValueError("Savings interest must be between 1% and 5%")
		if interest > self.loan_interest / 3:
			raise ValueError("Savings interest must be less than 1/3 of Loan interest")
		self.savings_interest = interest

	def SetLoanInterest(self, interest):
		if self.month % 12 != 0:
			raise RuntimeError("Unable to set interest outside of January.")

		if  interest < 0.06 or interest > .18:
			raise ValueError("Loan interest must be between 6% and 18%")
		if interest < self.savings_interest * 3:
			raise ValueError("Loan interest must be more than 3x Savings interest")
		self.loan_interest = interest

	def SendBill(self, a):
		interest = int(round(a.LoanTotal() * self.loan_interest / 12))
		a.bill = interest + max(self.loan_payment_percentage * a.loan_principal, self.min_loan_payment)
		print "Amount due for loan: ", toDollar(a.bill)
		if a.delinquencies:
			print "Delinquencies:\n{Month} Due Fee"
			for x in a.delinquencies:
				print x

	def SendStatement(self, a, datestart=None, dateend=None):
		if not dateend:		dateend = self.month 	#Show for current month by default.
		if not datestart: datestart = dateend-2 # Show previous 2 months

		print "\n(%s) %s %s's Monthly Statement" %(a.accountID, a.firstname, a.lastname)
		print "Savings\n{Month} Action (Details) Amount"
		for x in a.savings_transactions + a.savings_pending:
			if x.date >= datestart and x.date <= dateend:
				print x
		print "Balance: $%.2f" %(toDollar(a.savings_balance))
		print "Current: $%.2f" %(toDollar(a.SavingsAvailable()))
		print "Loan\n{Month} Action (Details) Amount"
		for x in a.loan_transactions + a.loan_pending:
			if x.date >= datestart and x.date <= dateend:
				print x
		print "Balance: $%.2f" %toDollar(a.loan_balance)
		print "Total: $%.2f" %toDollar(a.LoanTotal())


	def OpenSavings(self, a, initial_savings):
		if initial_savings <= 0 or initial_savings > self.max_savings:
			raise ValueError("Savings must be between 0 and %d" %toDollar(self.max_savings))
		a.savings_pending.append(Transaction(self.month, "Deposit", initial_savings, "Initial deposit"))

	def OpenLoan(self, a, loan_principal):
		if a.hasLoan():
			raise RuntimeError("Cannot open a second loan.")
		if loan_principal < self.min_loan or loan_principal > a.SavingsAvailable() * 5 or loan_principal > self.max_loan:
			raise ValueError("(%.2f)\nLoan principal must be at least $%.2f, and no more than $%.2f (5x your savings) or $%.2f, whichever is lower." %(toDollar(loan_principal), toDollar(self.min_loan), toDollar(a.SavingsAvailable() * 5), toDollar(self.max_loan)))
		a.loan_pending.append(Transaction(self.month, "Loan Opening", loan_principal, "Loan Opening"))
		a.loan_principal = loan_principal


	def Withdraw(self, a, amount):
		if amount <= 0:
			raise ValueError("You must withdraw a proper amount")
		if amount > a.SavingsAvailable():
			raise ValueError("You don't have that much left")
		else:
			if amount == a.SavingsAvailable():
				a.savings_pending.append(Transaction(self.month, "Withdrawal", -amount, "Closing Account"))
			else:
				a.savings_pending.append(Transaction(self.month, "Withdrawal", -amount, "Withdrawal"))


	def Deposit(self, a, amount):
		if amount <= 0:
			raise ValueError("You must deposit a proper amount")
		if amount + a.SavingsAvailable() > self.max_savings:
			raise ValueError("Your account can't hold more than %s" %self.max_savings)
		else:
			a.savings_pending.append(Transaction(self.month, "Deposit", amount, "Deposit"))

	def LoanPayment(self, a, amount):
		if amount <= 0:
			raise ValueError("You must pay a proper amount")
		if a.LoanTotal() - amount < 0:
			raise ValueError("You cannot pay more than you owe.")
		else:
			if amount == a.LoanTotal():
				a.loan_pending.append(Transaction(self.month, "Payment", -amount, "Closing Loan"))
			else:
				a.loan_pending.append(Transaction(self.month, "Payment", -amount, "Loan Payment"))




def SimulateBank():
	#initial setup of Bank - set interest rates, etc.

	def validsavingsrate(v):
		try:
			v = int(float(v)*100)
			if v % 25 == 0 and v > 100 and v < 500:
				return float(v) / 10000 # convert to float value, not Percentage value
		except:
			pass
		return None

	savings_interest_menu = DataMenu("Savings interest rate", "Enter rate: ", validsavingsrate, "Rate must be between 1% and 5%, and in .25 increments, and less than 1/3 the loan rate", False)
	savings_interest = savings_interest_menu.waitForInput()

	def validloanrate(v): # Needs savings_interest to verify against.
		try:
			v = int(float(v) * 100)
			if v % 25 == 0:
				if v > 600 and v < 1800 and v >= 300 * savings_interest:
					return float(v) / 10000
		except:
			pass
		return None

	loan_interest_menu = DataMenu("Loan interest rate", "Enter rate: ", validloanrate, "Rate must be between 6% and 18%, and in .25 increments, and more than 3x the savings rate.", False)
	loan_interest = loan_interest_menu.waitForInput()
	bank = BankManager(savings_interest, loan_interest)

	## Menu helper functions
	def cancel(x):
		return False

	def disable(x):
		print "Disabled"

	def validMoney(s):
		"""Validates and converts a string, expecting a Dollar amount
		"""
		s.lstrip("$ ")
		val = s.split('.') # Can only have one decimal point
		if len(val) > 2:
			return False
		val[0] = int(val[0])
		if len(val) == 2:
			if len(val[1]) > 2:
				return False	# Can only operate in cents, no smaller
			val[1] = int(val[1])
		else:
			val.append(0)
		# Convert up to cents
		val = val[0] * 100 + val[1] ## DEBUGGER NOTE: This will make an entirely wrong value for negative amounts
		return val 					## This will only be visible if the dollar value is -0 which returns a positive cent value.

	def validName(s):
		s = s.strip()
		if len(s) <= 2:
			return None
		s = s[:16]
		return s

	getMoney = part(DataMenu, prompt="Amount: ", valid=validMoney, err="Please enter in proper format: XX.XX")

	## Menus
	def manageAccount(a):
		# Only certain options are available depending on status of accounts.
		manage_acct = []
		if a.hasSavings():
			manage_acct.append(Choice(1,"Withdraw from Savings", handler=lambda v: bank.Withdraw(a=a, amount=v),
								subMenu=getMoney("Withdrawing")))
			manage_acct.append(Choice(2,"Deposit to Savings", handler=lambda v: bank.Deposit(a=a, amount=v),
					subMenu=getMoney("Depositing")))
		else:
			manage_acct.append(Choice(3, "Open Savings account", handler=lambda v: bank.OpenSavings(a=a, amount=v),
					subMenu=getMoney("Initial Deposit")))
		if a.hasLoan():
			manage_acct.append(Choice(4,"Make Payment on Loan", handler=lambda v: bank.LoanPayment(a=a, amount=v),
					subMenu=getMoney("Paying Loan")))
		else:
			manage_acct.append(Choice(5,"Open Loan", handler=lambda v: bank.OpenLoan(a=a, loan_principal=v),
					subMenu=getMoney("Opening Loan")))
		manage_acct.append(Choice(6,"View Statement", handler=lambda v: bank.SendStatement(a)))
		def closeAccount(x):
			bank.CloseAccount(a)
			return False # If it succeeded, exit management menu
		manage_acct.append(Choice(7,"Close Account", handler=closeAccount))
		manage_acct.append(Choice(0,"Log Out",handler=cancel))
		manageAcct=Menu("Managing Account", manage_acct)
		manageAcct.waitForInput()

	def GetByName(x=None):
		fname = DataMenu(prompt="First Name: ", valid=validName).waitForInput()
		if fname == None: return
		lname = DataMenu(prompt="Last Name: ", valid=validName).waitForInput()
		if lname == None: return
		try:
			a = bank.GetAccountByName(fname, lname)
			return a
		except Exception as e:
			print "Account not found",e

	def GetByID(x=None):
		acctID = DataMenu(prompt="Account ID: ", valid=lambda s: s if len(s)==6 and s.isdigit() else None, err="Account ID must be exactly 6 digits").waitForInput()
		try:
			a = bank.GetAccount(acctID)
			return a
		except Exception as e:
			print "Account not found", e

	def AccessByName(x=None):
		a = GetByName()
		if a == None:
			return
		manageAccount(a)
		return False # When done, return to main menu.

	def AccessByID(x=None):
		a = GetByID()
		if a == None:
			return
		manageAccount(a)
		return False # When done, return to main menu.

	def createAccount(x=None):
		fname = DataMenu(prompt="First Name: ", valid=validName).waitForInput()
		if fname == None: return
		lname = DataMenu(prompt="Last Name: ", valid=validName).waitForInput()
		if lname == None: return
		initial_savings = getMoney("Initial Amount").waitForInput()
		if initial_savings == None: return
		a = bank.CreateAccount(fname, lname, initial_savings)
		bank.accounts.append(a)
		print "Account %s created for %s %s, with initial deposit of %.2f" %(a.accountID, a.firstname, a.lastname, initial_savings / 100)

	def setSavingsRate(x):
		def validsavingsrate(v):
			try:
				v = int(float(v)*100)
				if v % 25 == 0 and v >= 100 and v <= 500 and v >= bank.loan_interest / 300:
					return float(v) / 10000 # convert to float value, not Percentage value
			except:
				pass
			return None

		savings_interest_menu = DataMenu("Savings interest rate", "Enter rate: ", validsavingsrate, "Rate must be between 1% and 5%, and in .25 increments, and less than 1/3 the loan rate")
		savings_rate = savings_interest_menu.waitForInput()
		if savings_rate != None:
			bank.savings_interest = savings_rate

	def setLoanRate(x):
		def validloanrate(v): # Needs savings_interest to verify against.
			try:
				v = int(float(v) * 100)
				if v % 25 == 0 and v >= 600 and v <= 1800 and v >= 300 * bank.savings_interest:
						return float(v) / 10000
			except:
				pass
			return None
		loan_interest_menu = DataMenu("Loan interest rate", "Enter rate: ", validloanrate, "Rate must be between 6% and 18%, and in .25 increments, and more than 3x the savings rate.")
		rate =  loan_interest_menu.waitForInput()
		if rate != None:
			bank.loan_interest = rate


	access_acct = [\
		Choice(1,"Enter by Name", handler=AccessByName),
		Choice(2,"Enter by ID", handler=AccessByID),
		Choice(0,"Cancel",handler=cancel)]
	accessAcct = Menu("Accessing Account", access_acct)

	bank_actions = [\
				"List Accounts", "View Account by ID", "Issue Check", "Send Statement", "Send Bill", "Send Delinquency",
				"Set Savings Interest", "Set Loan Interest", "Forward One Month"]
	bank_action = [Choice(1,"Forward 1 Month", handler=lambda x:bank.ForwardMonth()),
					Choice(2,"Set Savings Interest Rate", handler=setSavingsRate),
					Choice(3,"Set Loan Interest Rate", handler=setLoanRate),
					Choice(0,"Cancel", handler=cancel)]
	bankActions= Menu("Bank Actions", bank_action)
	main_menu = [\
		Choice(1,"Create New Account", handler=createAccount),
		Choice(2, "Access Account", subMenu=accessAcct),
		Choice(3, "Bank Actions", subMenu=bankActions),
		Choice(0, "Exit",handler=cancel) ]

	mainMenu = Menu("Bank Sim", main_menu)
	mainMenu.waitForInput()

if __name__ == "__main__":
	SimulateBank()
