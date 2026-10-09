from enum import StrEnum

DEFAULT_VERIFICATION_BUTTON_LABEL = "Start Age Verification!"
# Discord rejects the whole message when a button label is longer than this.
MAX_BUTTON_LABEL_LENGTH = 80

GDPR_REMOVAL_GRACE_DAYS = 30

# The weekly developer stats report (classes.support.weeklyreport) posts on Sundays at this hour, UTC.
WEEKLY_REPORT_HOUR = 12
REPORT_TOP_SERVERS = 5

# A server that removes the bot within QUICK_LEAVE_DAYS of adding it, after using at least QUICK_LEAVE_MIN_COMMANDS
# commands, gets its log trail saved to QUICK_LEAVE_DIR (classes.support.quickleaves). The files hold user names
# and ids from the logs, so they are deleted after QUICK_LEAVE_RETENTION_DAYS.
QUICK_LEAVE_DAYS = 7
QUICK_LEAVE_MIN_COMMANDS = 1
QUICK_LEAVE_DIR = "logs/quick_leaves"
QUICK_LEAVE_RETENTION_DAYS = 90

# How long a recorded IP stays useful for correlation. Dynamic addresses have
# rotated well before this, so the digests are cleared here rather than being
# carried for the full 365 day record retention.
IP_RETENTION_DAYS = 30

# Points check_asn adds when a website verification does not come from the member's
# own connection. The non-residential value is a placeholder until the threshold
# these points are compared against is decided.
ASN_NON_RESIDENTIAL_POINTS = 50
KNOWN_VPN_POINTS = 100

# Risk score shown on online verification approvals, see classes.verification.risk.
# Each signal adds its points once; the total is capped at RISK_MAX. A device-only
# alt scores lower than an IP alt because identical phone models can share a
# fingerprint, while an alt matching on both is the strongest signal of all.
RISK_MAX = 100
RISK_VPN_POINTS = 35
RISK_IP_ALT_POINTS = 30
RISK_DEVICE_ALT_POINTS = 20
RISK_IP_AND_DEVICE_ALT_POINTS = 40
# (maximum account age in days, points), checked in order.
RISK_ACCOUNT_AGE_POINTS = ((7, 25), (30, 15), (90, 5))
# Lowest score for each band, highest band first.
RISK_BANDS = ((60, "High", "🔴"), (30, "Medium", "🟡"), (0, "Low", "🟢"))

messagechoices = {
	"verification_completed_message" : 'This is the welcome message that will be posted in the verification_completed_channel channel This starts with: `Welcome to {server name} {user}! This is where the message goes`',
	"server_join_message"            : 'This is the welcome message that will be posted in the lobby channel, and be the first message new users see. This starts with: `Welcome {user}! This is where the message goes`',
	"server_leave_message" : "This is the message that will be sent when a user leaves the server.",
	"verification_button_label" : f'💎 Premium: The text on the verification button itself (max 80 characters). '
	# "idmessage"    : 'This message will be sent to the user when using the id request method along with the default.',
}
channelchoices = {
	'invite_log'                     : 'This channel will be used to log invite information',
	'verification_completed_channel' : 'This is your verification_completed_channel channel, where the welcome message will be posted',
	"server_join_channel"            : 'This is your lobby channel, where the lobby welcome message will be posted. This is also where the verification process will start; this is where new users should interact with the bot.',
	"age_log"                        : 'This is the channel where the lobby logs will be posted, this channel has to be hidden from the users; failure to do so will result in the bot leaving.',
	"approval_channel"               : 'This is where the verification approval happens, this channel should be hidden from the users.',
	"verification_failure_log"       : 'This is where failed verification logs will be posted, this channel should be hidden from the users.',
	"reverify_age_log"               : 'This is the channel where the reverification logs will be posted, this channel has to be hidden from the users; failure to do so will result in the bot leaving.',
	'leave_log': "This channel is where the leaves will be logged."
}
rolechoices = {
	"verification_add_role"      : 'These roles will be added to the user after a successful verification',
	"verification_remove_role"   : 'These roles will be removed from the user after a successful verification',
	"return_remove_role"         : "These roles will be removed from the user when running the /lobby return command.",
	"server_join_role"           : "These roles will be added to the user when they join the server and removed when they verify their age.",
	"auto_update_excluded_roles" : "These roles are excluded from the automated age update system, ensuring the bot does not assign unnecessary roles to users.",
	"reverification_role"        : "These roles are added to the user when they reverify their age.",
	"approval_ping_role"         : "This role is pinged when a user successfully submits their verification and awaits approval. Not compatitable with the automatic mode."
}

# Verification choices
VERIFICATION_KEY = "VERIFICATION_METHOD"
REVERIFICATION_KEY = "REVERIFICATION_METHOD"


class VerificationMethods(StrEnum) :
	BASIC = "BASIC"
	IDVERIFY = "IDVERIFY"
	ALL = "ALL"
	WEBSITE = "WEBSITE"

# Verification methods that need premium; the others are free to pick.
PREMIUM_VERIFICATION_METHODS = (VerificationMethods.IDVERIFY, VerificationMethods.ALL)

FAIL_ACTION = "JOIN_FAIL_ACTION"

class JoinRequirementsToggles(StrEnum) :
	ACCOUNT_AGE = "ACCOUNT_AGE"
	HAS_AVATAR = "HAS_AVATAR"
	MUTUAL_GUILDS = "MUTUAL_GUILDS"
	IS_BOT = "IS_BOT"
	HAS_BANS = "HAS_BANS"
	REQUIRE_ACTIVE_PRESENCE = "REQUIRE_ACTIVE_PRESENCE"
	FILTER_WEB_ONLY_ACCOUNTS = "FILTER_WEB_ONLY_ACCOUNTS"



lobby_approval_toggles = {
	'picture_large'         : 'Show large profile picture in approval modal',
	'picture_small'         : 'Show small profile picture (hides large)',
	'bans'                  : 'Display user’s ban records before approving',
	'joined_at'             : 'Show when user joined this server',
	'created_at'            : 'Show when the account was created',
	'legacy_message'        : 'Use the old approval message style',
	'user_id'               : 'Show the user id of the account',
	'show_previous_servers' : 'Show previous servers',
	'risk_score'            : 'Show the risk score on online verifications',
	'debug'                 : 'shows debug approval message'
}

# Abandoned online verification reminder (premium). 0 or unset disables it.
VERIFICATION_REMINDER_KEY = "VERIFICATION_REMINDER_MINUTES"
# Also how far back the reminder looks, so links opened before this are never reminded.
MAX_VERIFICATION_REMINDER_MINUTES = 7 * 24 * 60

int_options = {
	'CLEAN_LOBBY_DAYS' : 'Inactive member cleanup threshold from the lobby (days).',
	'MINIMUM_ACCOUNT_AGE' : 'The minimum required account age in days',
	VERIFICATION_REMINDER_KEY : '💎 Premium: Message members who opened the online verification page but did not finish after this many minutes (0 disables).'
}

available_toggles = ["SEND_JOIN_MESSAGE", "SEND_VERIFICATION_COMPLETED_MESSAGE", "DM_VERIFICATION_COMPLETED_MESSAGE",
                     "AUTOMATIC_VERIFICATION",
                     "AUTOKICK_UNDERAGED_USERS", "AUTOKICK_ON_DISCREPANCY", "AUTO_UPDATE_AGE_ROLES", "PING_OWNER_ON_FAILURE", "SURVEY",
                     "LOG_CONFIG_CHANGES", "CLEANUP_MESSAGES", "SEND_LEAVE_MESSAGE", "KICK_ON_CLEAN"]
enabled_toggles = ["SEND_VERIFICATION_COMPLETED_MESSAGE", "SEND_JOIN_MESSAGE", 'BANS', 'JOINED_AT', 'CREATED_AT',
                   'USER_ID', 'PICTURE_SMALL',
                   "LOG_CONFIG_CHANGES", "CLEANUP_MESSAGES", "KICK_ON_CLEAN"]
