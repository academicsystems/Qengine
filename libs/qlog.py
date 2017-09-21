# qengine errors
def loge(message):
	with open('./logs/error.log','a+') as file:
		file.write("%s\n\n" % message)

# user errors
def logu(message):
	with open('./logs/user-error.log','a+') as file:
		file.write("%s\n\n" % message)