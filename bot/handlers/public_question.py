"""
Public Q&A Flow — stub.
Full implementation: Step 9 of the build order.
"""
from telegram.ext import ConversationHandler

public_question_conv_handler = ConversationHandler(
    entry_points=[],
    states={},
    fallbacks=[],
    name="public_question_conv",
)
