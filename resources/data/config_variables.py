messagechoices = {
	'welcomemessage' : 'This is the welcome message that will be posted in the general channel This starts with: `Welcome to {server name} {user}! This is where the message goes`',
	"lobbywelcome"   : 'This is the welcome message that will be posted in the lobby channel, and be the first message new users see. This starts with: `Welcome {user}! This is where the message goes`',
}
channelchoices = {
	'inviteinfo' : 'This channel will be used to log invite information',
	'general'    : 'This is your general channel, where the welcome message will be posted',
	"lobby"      : 'This is your lobby channel, where the lobby welcome message will be posted. This is also where the verification process will start; this is where new users should interact with the bot.',
	"lobbylog"   : 'This is the channel where the lobby logs will be posted, this channel has to be hidden from the users; failure to do so will result in the bot leaving.',
	"lobbymod"   : 'This is where the verification approval happens, this channel should be hidden from the users.',
	"idlog"      : 'This is where failed verification logs will be posted, this channel should be hidden from the users.'
}
rolechoices = {
	'add'    : 'These roles will be added to the user after a successful verification',
	"rem"    : 'These roles will be removed from the user after a successful verification',
	"return" : "These roles will be removed from the user when running the /lobby return command.",
	"join"   : "These roles will be added to the user when they join the server and removed when they verify their age.",
	"exclude" : "These roles are excluded from the automated age update system, ensuring the bot does not assign unnecessary roles to users."
}