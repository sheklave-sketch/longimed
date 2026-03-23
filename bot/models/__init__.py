# Import all models so Alembic can detect them for autogenerate
from bot.models.user import User
from bot.models.doctor import Doctor, Specialty, RegistrationStatus
from bot.models.question import Question, QuestionStatus
from bot.models.follow_up import FollowUp, FollowUpStatus
from bot.models.session import Session, SessionPackage, SessionStatus, SessionMode
from bot.models.relay_message import RelayMessage, SenderRole
from bot.models.payment import Payment, PaymentProvider, PaymentStatus
from bot.models.moderator import Moderator
from bot.models.notification import Notification
from bot.models.waitlist import Waitlist, WaitlistStatus
from bot.models.doctor_earnings import DoctorEarnings, EarningsStatus
from bot.models.report import Report, TargetType, ReportStatus
from bot.models.translation import Translation
from bot.models.settings_model import AppSetting
from bot.models.subscription import Subscription, SubscriptionPlan, SubscriptionStatus
