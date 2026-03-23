"""
Private Session Flow — stub.
Full implementation: Step 11 of the build order.
"""
from telegram.ext import ConversationHandler

private_session_conv_handler = ConversationHandler(
    entry_points=[],
    states={},
    fallbacks=[],
    name="private_session_conv",
)
