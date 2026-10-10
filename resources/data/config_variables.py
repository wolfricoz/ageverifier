from enum import StrEnum

DEFAULT_VERIFICATION_BUTTON_LABEL = "Start Age Verification!"
# Discord rejects the whole message when a button label is longer than this.
MAX_BUTTON_LABEL_LENGTH = 80

GDPR_REMOVAL_GRACE_DAYS = 30

# The member's ID image waits for review in AgeVerifier's DM to them for at most this long
# (classes.verification.idmessages); the DM and the privacy policy both promise it.
ID_MESSAGE_RETENTION_DAYS = 7

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

# The QUARANTINE fail action gives the member this role, and a task in classes.lobby.Quarantine takes it
# off again once QUARANTINE_HOURS have passed since they joined (checked every 10 minutes).
QUARANTINE_ROLE_KEY = "QUARANTINE_ROLE"
QUARANTINE_HOURS_KEY = "QUARANTINE_HOURS"
DEFAULT_QUARANTINE_HOURS = 24
MAX_QUARANTINE_HOURS = 30 * 24

class JoinRequirementsToggles(StrEnum) :
	ACCOUNT_AGE = "ACCOUNT_AGE"
	HAS_AVATAR = "HAS_AVATAR"
	MUTUAL_GUILDS = "MUTUAL_GUILDS"
	IS_BOT = "IS_BOT"
	HAS_BANS = "HAS_BANS"
	REQUIRE_ACTIVE_PRESENCE = "REQUIRE_ACTIVE_PRESENCE"
	FILTER_WEB_ONLY_ACCOUNTS = "FILTER_WEB_ONLY_ACCOUNTS"



# Staff notes on a member (classes.membernotes). Notes are capped so a handful fits in one
# 1024 character embed field; the approval message shows the newest few.
MAX_NOTE_LENGTH = 500
APPROVAL_NOTES_SHOWN = 3

# Denial reason presets (classes.denialreasons): staff pick one in the approval message's deny flow
# and the member gets the preset's message by DM. A select menu holds at most 25 options and one
# is kept for a one-off custom reason. Labels double as select option labels, which Discord caps
# at 100 characters; messages leave room for the DM's header and footer under the 2000 limit.
MAX_DENIAL_REASONS = 24
MAX_DENIAL_LABEL_LENGTH = 100
MAX_DENIAL_MESSAGE_LENGTH = 1500
# A server that has no presets gets these, see DenialReasonTransactions.get_for_guild.
# {user} and {server} in a message are replaced with the member's mention and the server name.
DEFAULT_DENIAL_REASONS = (
	("Age and date of birth don't match",
	 "The age you entered doesn't match your date of birth. Please check both and submit your verification again, "
	 "with your date of birth as mm/dd/yyyy."),
	("Invalid date of birth",
	 "The date of birth you entered isn't a valid date. Please submit your verification again and write your date "
	 "of birth as mm/dd/yyyy, for example 01/31/2000."),
	("Inappropriate profile",
	 "Your profile has content that isn't allowed here, such as an NSFW avatar, name, bio, status, banner or "
	 "pronouns. Please update your profile and then submit your verification again."),
	("Suspected alternate account",
	 "Your account looks linked to another account in {server}. If you believe this is a mistake, please contact "
	 "the server's staff."),
	("Contact staff",
	 "Your verification needs a closer look. Please contact the staff of {server} for the next steps."),
)

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
	'staff_notes'           : 'Show staff notes on the member (/notes)',
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
                     "LOG_CONFIG_CHANGES", "CLEANUP_MESSAGES", "SEND_LEAVE_MESSAGE", "KICK_ON_CLEAN", "VPN_FLAG_ONLY"]
enabled_toggles = ["SEND_VERIFICATION_COMPLETED_MESSAGE", "SEND_JOIN_MESSAGE", 'BANS', 'JOINED_AT', 'CREATED_AT',
                   'USER_ID', 'PICTURE_SMALL',
                   "LOG_CONFIG_CHANGES", "CLEANUP_MESSAGES", "KICK_ON_CLEAN", 'STAFF_NOTES']
