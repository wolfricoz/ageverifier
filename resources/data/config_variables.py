messagechoices = {
	"verification_completed_message" : 'This is the welcome message that will be posted in the verification_completed_channel channel This starts with: `Welcome to {server name} {user}! This is where the message goes`',
	"server_join_message"            : 'This is the welcome message that will be posted in the lobby channel, and be the first message new users see. This starts with: `Welcome {user}! This is where the message goes`',
	# "idmessage"    : 'This message will be sent to the user when using the id request method along with the default.',
}
channelchoices = {
	'invite_log'                     : 'This channel will be used to log invite information',
	'verification_completed_channel' : 'This is your verification_completed_channel channel, where the welcome message will be posted',
	"server_join_channel"            : 'This is your lobby channel, where the lobby welcome message will be posted. This is also where the verification process will start; this is where new users should interact with the bot.',
	"age_log"                        : 'This is the channel where the lobby logs will be posted, this channel has to be hidden from the users; failure to do so will result in the bot leaving.',
	"approval_channel"               : 'This is where the verification approval happens, this channel should be hidden from the users.',
	"verification_failure_log"       : 'This is where failed verification logs will be posted, this channel should be hidden from the users.',
	"reverify_age_log"               : 'This is the channel where the reverification logs will be posted, this channel has to be hidden from the users; failure to do so will result in the bot leaving.'
}
rolechoices = {
	"verification_add_role"      : 'These roles will be added to the user after a successful verification',
	"verification_remove_role"   : 'These roles will be removed from the user after a successful verification',
	"return_remove_role"         : "These roles will be removed from the user when running the /lobby return command.",
	"server_join_role"           : "These roles will be added to the user when they join the server and removed when they verify their age.",
	"auto_update_excluded_roles" : "These roles are excluded from the automated age update system, ensuring the bot does not assign unnecessary roles to users.",
	"reverification_role"        : "These roles are added to the user when they reverify their age."
}

lobby_approval_toggles = {
	'picture_large': 'Show large profile picture in approval modal',
	'picture_small': 'Show small profile picture (hides large)',
	'bans': 'Display user’s ban records before approving',
	'joined_at': 'Show when user joined this server',
	'created_at': 'Show when the account was created',
	'legacy_message': 'Use the old approval message style',
	'user_id': 'Show the user id of the account',
	'show_previous_servers': 'Show previous servers',
	'debug': 'shows debug approval message'
}

int_options = {
	'CLEAN_LOBBY_DAYS': 'Inactive member cleanup threshold from the lobby (days).'
}

available_toggles = ["SEND_JOIN_MESSAGE", "SEND_VERIFICATION_COMPLETED_MESSAGE", "AUTOMATIC_VERIFICATION",
                     "AUTOKICK_UNDERAGED_USERS", "AUTO_UPDATE_AGE_ROLES", "PING_OWNER_ON_FAILURE",
                     "ONLINE_VERIFICATION", "SURVEY", "LOG_CONFIG_CHANGES", "CLEANUP_MESSAGES"]
enabled_toggles = ["SEND_VERIFICATION_COMPLETED_MESSAGE", "SEND_JOIN_MESSAGE", 'BANS', 'JOINED_AT', 'CREATED_AT',
                   'USER_ID', 'PICTURE_SMALL',
                   "LOG_CONFIG_CHANGES", "CLEANUP_MESSAGES"]
