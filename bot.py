import logging
import pytz
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from google import genai

# ================= إعدادات عامة =================
TELEGRAM_TOKEN = '8423246055:AAGV4ruVzLJGFrcrhcbGtJadZvVvlNVTfsc'
GEMINI_API_KEY = 'AQ.Ab8RN6LB_lzHT75WWGRsoq1gGDJzzeAi5O89VZjl9OWg1FfihQ'
TIMEZONE = pytz.timezone('Asia/Riyadh')

client = genai.Client(api_key=GEMINI_API_KEY)
activated_users = set()
group_members = {}  # لتخزين أعضاء المجموعات

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# ================= دالة توليد الفكرة =================
def generate_weekly_idea():
    prompt = """
    أنت خبير استراتيجي في التكنولوجيا والذكاء الاصطناعي وريادة الأعمال.
    مهمتك هي توليد فكرة برمجية/رقمية واحدة قوية جداً ومبتكرة تعتمد على الذكاء الاصطناعي.
    الفكرة يجب أن تكون قابلة للتطبيق فوراً وتخدم إما الشركات أو الأفراد.
    
    يجب أن يكون الرد مفصلاً جداً ومقسماً إلى النقاط التالية:
    
    💡 اسم الفكرة: (اسم جذاب ومختصر)
    🎯 الجمهور المستهدف: (شركات / أفراد / كلاهما)
    🚨 المشكلة التي تحلها: (وصف دقيق للألم أو المشكلة في السوق)
    🤖 كيف يحلها الذكاء الاصطناعي: (الشرح التقني والمبتكر لاستخدام الـ AI)
    🛠️ الأدوات والتقنيات المطلوبة: (لغات البرمجة، مكتبات الـ AI، APIs، استضافة)
    💰 نموذج الربح: (كيف سيتم جني الأموال من هذا المشروع)
    🚀 خطة التنفيذ: (خطوات عملية لبناء النسخة الأولى خلال أسبوعين)
    ⚠️ التحديات وكيفية تجاوزها: (عقبات متوقعة وحلولها)
    
    اجعل الفكرة غير تقليدية، قوية، ومكتوبة بلغة عربية فصحى، احترافية، ومحفزة.
    """
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        return response.text
    except Exception as e:
        logging.error(f"Error generating idea: {e}")
        return "عذراً، حدث خطأ في توليد فكرة هذا الأسبوع."

# ================= دوال البوت =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_msg = (
        "أهلاً بك في بوت الأفكار البرمجية الأسبوعية! 🚀\n\n"
        "📌 الأوامر المتاحة:\n"
        "• /start - عرض رسالة الترحيب\n"
        "• /activate - تفعيل الاشتراك\n"
        "• /tagall [رسالة] - تاغ جميع أعضاء المجموعة\n\n"
        "كل يوم خميس الساعة 8 مساءً، سأرسل لك فكرة برمجية قوية!\n\n"
        "اكتب 'تفعيل' أو استخدم /activate للبدء 💡"
    )
    await update.message.reply_text(welcome_msg)

async def activate_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    
    if user_id in activated_users:
        await update.message.reply_text(f"مرحباً {user_name}! ✅ أنت مفعل مسبقاً")
        return
    
    activated_users.add(user_id)
    await update.message.reply_text(
        f"🎉 تم التفعيل بنجاح! 🎉\n\n"
        f"مرحباً {user_name}! ستصلك فكرة برمجية قوية كل خميس الساعة 8 مساءً"
    )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    
    # حفظ أعضاء المجموعة تلقائياً
    if update.effective_chat.type in ['group', 'supergroup']:
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id
        user_name = update.effective_user.first_name
        
        if chat_id not in group_members:
            group_members[chat_id] = set()
        group_members[chat_id].add(user_id)
    
    # تفعيل المستخدم
    if text in ["تفعيل", "تفعيل.", "تفعيل!"]:
        await activate_user(update, context)

async def tag_all_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تاغ جميع أعضاء المجموعة"""
    chat = update.effective_chat
    message = update.message
    
    # التحقق إذا كانت الرسالة في مجموعة
    if chat.type not in ['group', 'supergroup']:
        await message.reply_text("⚠️ هذا الأمر يعمل فقط في المجموعات!")
        return
    
    chat_id = chat.id
    
    # الحصول على النص المطلوب إرساله
    args = context.args
    if args:
        custom_message = " ".join(args)
    else:
        custom_message = "📢 تنبيه مهم لجميع الأعضاء!"
    
    # الحصول على قائمة الأعضاء المحفوظة
    if chat_id not in group_members or not group_members[chat_id]:
        await message.reply_text(
            "⚠️ لا يوجد أعضاء مسجلين!\n\n"
            "💡 يجب أن يرسل الأعضاء أي رسالة في المجموعة أولاً ليتم تسجيلهم."
        )
        return
    
    members = list(group_members[chat_id])
    
    # بناء رسالة التاغ
    mentions = []
    for user_id in members:
        try:
            user = await context.bot.get_chat(user_id)
            user_mention = f"[{user.first_name}](tg://user?id={user_id})"
            mentions.append(user_mention)
        except:
            continue
    
    if not mentions:
        await message.reply_text("⚠️ لا يمكن تاغ الأعضاء!")
        return
    
    # إرسال الرسالة (تيليغرام يسمح بـ 200 mention في رسالة واحدة)
    chunk_size = 200
    chunks = [mentions[i:i + chunk_size] for i in range(0, len(mentions), chunk_size)]
    
    for i, chunk in enumerate(chunks):
        mention_text = " | ".join(chunk)
        full_message = f"{custom_message}\n\n{mention_text}"
        
        await message.reply_text(full_message, parse_mode='Markdown')
        
        # انتظار ثانية بين الرسائل
        if i < len(chunks) - 1:
            import asyncio
            await asyncio.sleep(1)

async def send_weekly_idea(context: ContextTypes.DEFAULT_TYPE):
    logging.info("Generating and sending the weekly idea...")
    idea_text = generate_weekly_idea()
    
    if not activated_users:
        logging.warning("No activated users yet!")
        return

    for user_id in list(activated_users):
        try:
            await context.bot.send_message(chat_id=user_id, text=idea_text)
        except Exception as e:
            logging.error(f"Failed to send to {user_id}: {e}")
            activated_users.discard(user_id)

def main():
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("activate", activate_user))
    application.add_handler(CommandHandler("tagall", tag_all_members))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    job_queue = application.job_queue
    job_queue.run_daily(
        send_weekly_idea,
        time=pytz.datetime.time(hour=20, minute=0, tzinfo=TIMEZONE),
        days=(4,)
    )
    
    logging.info("Bot is running...")
    application.run_polling()

if __name__ == '__main__':
    main()