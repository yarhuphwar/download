import logging
from telegram import Update, ForceReply
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
import re

# Database functions တွေကို ဒီကနေ import လုပ်ပါမယ်။
# delete_expense_by_id နှင့် clear_all_expenses တို့ကို ထပ်ထည့်ပါ။
from db_manager import connect_db, close_db, create_table, add_expense, get_total_expenses, get_all_expenses, delete_expense_by_id, clear_all_expenses

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Conversation states for deleting a single item
DELETE_ID = range(1)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/start command ကို ဖြေကြားတယ်။"""
    conn = connect_db()
    if conn:
        create_table(conn)
        close_db(conn)
    await update.message.reply_text("👋 ငွေစာရင်း Bot မှ ကြိုဆိုပါတယ်။\n\n'အသုံးအနှုန်း - တန်ဖိုး' ပုံစံဖြင့် စာရင်းသွင်းနိုင်ပါတယ်။ ဥပမာ: `ထမင်းစား - 3000`\n\nစာရင်းချုပ်ရန် /summary ကို ပို့ပါ။ စာရင်းဖျက်ရန် /delete သို့မဟုတ် /clearall ကို ပို့ပါ။")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """ပုံမှန် message တွေကို ဖြေကြားပြီး ငွေစာရင်းသွင်းတယ်။"""
    text = update.message.text
    
    match = re.match(r'^(.*?)\s*-\s*(\d+)\s*$', text) 
    
    if match:
        item = match.group(1).strip()
        try:
            amount = int(match.group(2).strip())
            
            conn = connect_db()
            if conn:
                if add_expense(conn, item, amount):
                    await update.message.reply_text(f"✅ '{item}' အတွက် **{amount}** ကျပ်ကို မှတ်တမ်းတင်ပြီးပါပြီ။", parse_mode='MarkdownV2')
                else:
                    await update.message.reply_text("❌ မှတ်တမ်းတင်ရာတွင် အမှားဖြစ်ပွားပါသည်။ ကျေးဇူးပြု၍ ပြန်လည်စမ်းသပ်ပါ။")
                close_db(conn)
            else:
                await update.message.reply_text("Database ချိတ်ဆက်၍ မရပါ။ ကျေးဇူးပြု၍ Admin ကို ဆက်သွယ်ပါ။")
        except ValueError:
            await update.message.reply_text("❌ တန်ဖိုးက ကိန်းဂဏန်း (နံပါတ်) ဖြစ်ရပါမယ်။ ဥပမာ: `အအေးသောက် - 5000`")
        except Exception as e:
            logger.error(f"Error adding expense: {e}")
            await update.message.reply_text(f"❌ အမှားတစ်ခုခုဖြစ်သွားပါတယ်။ ကျေးဇူးပြု၍ နောက်မှ ပြန်လည်စမ်းသပ်ပါ။")
    else:
        await update.message.reply_text("❌ ပုံစံမှားနေပါတယ်။ 'အသုံးအနှုန်း - တန်ဖိုး' ပုံစံဖြင့် ရိုက်ပါ။ ဥပမာ: `ထမင်းစား - 3000`")

async def summary(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/summary command ကို ဖြေကြားပြီး စာရင်းချုပ်ပြတယ်။"""
    conn = connect_db()
    if conn:
        total = get_total_expenses(conn)
        expenses = get_all_expenses(conn)
        close_db(conn)
        
        if total is not None:
            summary_text = f"💰 \\*\\*စုစုပေါင်း အသုံးစရိတ်:\\*\\* `{total}` ကျပ်\n\n"
            
            if expenses:
                summary_text += "\\-\\-\\- \\*\\*နောက်ဆုံး မှတ်တမ်းများ\\*\\* \\-\n"
                
                for i, exp in enumerate(expenses[:10]): 
                    date_only = exp[3].split(' ')[0]
                    item_escaped = re.sub(r'([_`*\[\]()~>#\+\-=|{}\.!])', r'\\\1', exp[1])
                    date_escaped = re.sub(r'([_`*\[\]()~>#\+\-=|{}\.!])', r'\\\1', date_only)

                    # ID ကိုပါ ပြပေးမယ်၊ ဒါမှ ဖျက်ချင်ရင် ID ကို သုံးနိုင်မယ်။
                    summary_text += f"{i+1}\\. ID:`{exp[0]}` \\- `{item_escaped}` \\- `{exp[2]}` ကျပ် \\(`{date_escaped}`\\)\n" 
                
                if len(expenses) > 10:
                    summary_text += "\n_\\(စာရင်းအပြည့်အစုံကို နောက်ထပ် feature များဖြင့် ကြည့်ရှုနိုင်ပါသည်\\)_"
            else:
                summary_text += "စာရင်းမရှိသေးပါ။ စတင်မှတ်တမ်းတင်နိုင်ပါပြီ။"
            
            await update.message.reply_markdown_v2(summary_text)
        else:
            await update.message.reply_text("စာရင်းချုပ်ရာတွင် အမှားဖြစ်ပွားပါသည်။")
    else:
        await update.message.reply_text("Database ချိတ်ဆက်၍ မရပါ။")

# --- အသစ်ထပ်ထည့်မည့် Command Handlers များ ---

async def delete_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """/delete command ကို စတင်ပြီး ဖျက်ချင်သော ID ကို မေးမြန်းသည်။"""
    await update.message.reply_text("ဖျက်လိုသော မှတ်တမ်း၏ ID နံပါတ်ကို ရိုက်ထည့်ပါ။ /summary command ဖြင့် ID ကို ကြည့်ရှုနိုင်ပါသည်။ (ဖျက်ခြင်းကို ဖျက်သိမ်းရန် /cancel)")
    return DELETE_ID # Conversation state ကို ပြန်ပေး

async def delete_item(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """ဖျက်လိုသော ID ကို လက်ခံပြီး မှတ်တမ်းကို ဖျက်သည်။"""
    try:
        expense_id = int(update.message.text)
        conn = connect_db()
        if conn:
            if delete_expense_by_id(conn, expense_id):
                await update.message.reply_text(f"✅ ID **{expense_id}** မှတ်တမ်းကို ဖျက်ပြီးပါပြီ။", parse_mode='MarkdownV2')
            else:
                await update.message.reply_text(f"❌ ID **{expense_id}** ဖြင့် မှတ်တမ်းကို ရှာမတွေ့ပါ။", parse_mode='MarkdownV2')
            close_db(conn)
        else:
            await update.message.reply_text("Database ချိတ်ဆက်၍ မရပါ။")
        return ConversationHandler.END # Conversation ကို အဆုံးသတ်
    except ValueError:
        await update.message.reply_text("❌ ID နံပါတ်မှားယွင်းနေပါသည်။ ဂဏန်း (နံပါတ်) ဖြင့်သာ ရိုက်ထည့်ပါ။")
        return DELETE_ID # မှားယွင်းပါက ပြန်မေး

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """ဖျက်ခြင်း လုပ်ငန်းစဉ်ကို ဖျက်သိမ်းသည်။"""
    await update.message.reply_text("ဖျက်ခြင်းလုပ်ငန်းစဉ်ကို ဖျက်သိမ်းလိုက်ပါပြီ။")
    return ConversationHandler.END # Conversation ကို အဆုံးသတ်

async def clear_all_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/clearall command ကို ဖြေကြားပြီး မှတ်တမ်းအားလုံးကို ဖျက်သည်။ (သတိထားရန်)"""
    # အတည်ပြုချက် ထပ်မမေးတော့ပါဘူး၊ တိုက်ရိုက်ဖျက်လိုက်ပါမယ်။
    # ပိုပြီး လုံခြုံစေချင်ရင် အတည်ပြုချက်မေးတဲ့ ConversationHandler ထပ်ထည့်နိုင်ပါတယ်။
    conn = connect_db()
    if conn:
        if clear_all_expenses(conn):
            await update.message.reply_text("🗑️ မှတ်တမ်းအားလုံးကို ဖျက်လိုက်ပါပြီ။")
        else:
            await update.message.reply_text("❌ မှတ်တမ်းများ ဖျက်ရာတွင် အမှားဖြစ်ပွားပါသည်။")
        close_db(conn)
    else:
        await update.message.reply_text("Database ချိတ်ဆက်၍ မရပါ။")

def main():
    """Bot ကို စတင် Run ပါ။"""
    application = Application.builder().token("7249385846:AAE5zvsF2ot1wIVtacTagCtTrrKsf9XMVJo").build() 

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("summary", summary))

    # တစ်ခုချင်းစီ ဖျက်ရန် ConversationHandler
    delete_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("delete", delete_start)],
        states={
            DELETE_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, delete_item)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    application.add_handler(delete_conv_handler)

    # မှတ်တမ်းအားလုံး ဖျက်ရန် CommandHandler
    application.add_handler(CommandHandler("clearall", clear_all_data))

    # ပုံမှန် message handler (ဒါကို ConversationHandler တွေအောက်မှာ ထားတာ ပိုကောင်းပါတယ်)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Bot စတင်ပါပြီ...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()

