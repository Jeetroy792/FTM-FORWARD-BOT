import asyncio 
from database import db
from config import Config
from translation import Translation
from pyrogram import Client, filters
from .test import get_configs, update_configs, CLIENT, parse_buttons
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

CLIENT = CLIENT()



@Client.on_message(filters.private & filters.command(['settings']))
async def settings(client, message):
    text="<b>Change Your Settings As Your Wish</b>"
    await message.reply_text(
        text=text,
        reply_markup=main_buttons(),
        quote=True
    )
    


    
@Client.on_callback_query(filters.regex(r'^settings'))
async def settings_query(bot, query):
    user_id = query.from_user.id
    i, type = query.data.split("#")
    buttons = [[InlineKeyboardButton('🔙 Back', callback_data="settings#main")]]

    if type=="main":
        await query.message.edit_text(
            "<b>Change Your Settings As Your Wish</b>",
            reply_markup=main_buttons()
        )

    elif type=="bots":
        buttons = []
        _bot = await db.get_bot(user_id)
        if _bot is not None:
            buttons.append([InlineKeyboardButton(_bot['name'],
                             callback_data=f"settings#editbot")])
        else:
            buttons.append([InlineKeyboardButton('✚ Add Bot ✚',
                             callback_data="settings#addbot")])
            buttons.append([InlineKeyboardButton('✚ Add User Bot ✚',
                             callback_data="settings#adduserbot")])
        buttons.append([InlineKeyboardButton('🔙 Back',
                          callback_data="settings#main")])
        await query.message.edit_text(
            "<b><u>My Bots</u></b>\n\nYou Can Manage Your Bots In Here",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    elif type=="adduserbot":
        await query.message.edit_text(
            "🧩 Choose Login Method for Userbot:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔐 Login with String Session", callback_data="settings#userbot_string")],
                [InlineKeyboardButton("📱 Login via Phone Number", callback_data="settings#userbot_phone")],
                [InlineKeyboardButton("⬅️ Back", callback_data="settings#main")]
            ])
        )

    elif type=="userbot_string":
        await query.message.delete()
        msg = await bot.send_message(user_id, "📥 Please send your <b>Pyrogram String Session</b>.\n\n/cancel - Cancel")
        try:
            session = await bot.listen(user_id, timeout=300)
            if session.text == "/cancel":
                await msg.edit("❌ Process Cancelled.")
                return
            success = await CLIENT.add_session(session.text, user_id)
            if success is not True:
                await msg.edit(f"❌ Failed to login:\n{success}")
            else:
                await msg.edit("✅ Userbot successfully connected!")
        except asyncio.exceptions.TimeoutError:
            await msg.edit("⏰ Timeout. Process cancelled.")

    elif type=="userbot_phone":
        await query.message.delete()
        msg = await bot.send_message(user_id, "📞 Please send your <b>phone number</b> to log in.\n\n/cancel - Cancel")
        try:
            phone = await bot.listen(user_id, timeout=300)
            if phone.text == "/cancel":
                await msg.edit("❌ Process Cancelled.")
                return
            result = await CLIENT.add_session(phone.text, user_id)
            if result != True:
                await msg.edit(f"❌ Failed to send OTP:\n{result}")
                return
            otp = await bot.ask(user_id, "📩 Enter the OTP you received:")
            login_status = await CLIENT.verify_code(user_id, otp.text)
            if login_status == True:
                await msg.edit("✅ Userbot successfully connected!")
            else:
                await msg.edit(f"❌ Login failed:\n{login_status}")
        except asyncio.exceptions.TimeoutError:
            await msg.edit("⏰ Timeout. Process cancelled.")
            
    elif type=="channels":
        buttons = []
        channels = await db.get_user_channels(user_id)
        for channel in channels:
            buttons.append([InlineKeyboardButton(f"{channel['title']}",
                             callback_data=f"settings#editchannels_{channel['chat_id']}")])
        buttons.append([InlineKeyboardButton('✚ Add Channel ✚', 
                          callback_data="settings#addchannel")])
        buttons.append([InlineKeyboardButton('🔙 Back', 
                          callback_data="settings#main")])
        await query.message.edit_text( 
            "<b><u>My Channels</u></b>\n\nYou Can Manage Your Target Chats In Here",
            reply_markup=InlineKeyboardMarkup(buttons))
   
    elif type=="addchannel":  
        await query.message.delete()
        try:
            text = await bot.send_message(user_id, "<b><u>Set Target Chat</u></b>\n\nForward A Message From Your Target Chat\n/cancel - To Cancel This Process")
            chat_ids = await bot.listen(chat_id=user_id, timeout=300)
            if chat_ids.text=="/cancel":
                await chat_ids.delete()
                return await text.edit_text(
                      "Process Canceled",
                      reply_markup=InlineKeyboardMarkup(buttons))
            elif not chat_ids.forward_date:
                await chat_ids.delete()
                return await text.edit_text("This Is Not A Forward Message")
            else:
                chat_id = chat_ids.forward_from_chat.id
                title = chat_ids.forward_from_chat.title
                username = chat_ids.forward_from_chat.username
                username = "@" + username if username else "private"
            chat = await db.add_channel(user_id, chat_id, title, username)
            await chat_ids.delete()
            await text.edit_text(
                "Successfully Updated" if chat else "This Channel Already Added",
                reply_markup=InlineKeyboardMarkup(buttons))
        except asyncio.exceptions.TimeoutError:
            await text.edit_text('Process Has Been Automatically Cancelled', reply_markup=InlineKeyboardMarkup(buttons))
  
    elif type=="editbot": 
        bot_details = await db.get_bot(user_id)
        TEXT = Translation.BOT_DETAILS if bot_details['is_bot'] else Translation.USER_DETAILS
        buttons = [[InlineKeyboardButton('❌ Remove ❌', callback_data=f"settings#removebot")
                  ],
                  [InlineKeyboardButton('🔙 Back', callback_data="settings#bots")]]
        await query.message.edit_text(
            TEXT.format(bot_details['name'], bot_details['id'], bot_details['username']),
            reply_markup=InlineKeyboardMarkup(buttons))
                                             
    elif type=="removebot":
        await db.remove_bot(user_id)
        await query.message.edit_text(
            "Successfully Updated",
            reply_markup=InlineKeyboardMarkup(buttons))
                                             
    elif type.startswith("editchannels"): 
        chat_id = type.split('_')[1]
        chat = await db.get_channel_details(user_id, chat_id)
        buttons = [[InlineKeyboardButton('❌ Remove ❌', callback_data=f"settings#removechannel_{chat_id}")
                  ],
                  [InlineKeyboardButton('🔙 Back', callback_data="settings#channels")]]
        await query.message.edit_text(
            f"<b><u>📄 Channel Details</b></u>\n\n<b>Title :</b> <code>{chat['title']}</code>\n<b>Channel ID :</b> <code>{chat['chat_id']}</code>\n<b>Username :</b> {chat['username']}",
            reply_markup=InlineKeyboardMarkup(buttons))
                                             
    elif type.startswith("removechannel"):
        chat_id = type.split('_')[1]
        await db.remove_channel(user_id, chat_id)
        await query.message.edit_text(
            "Successfully Updated",
            reply_markup=InlineKeyboardMarkup(buttons))
                               
    elif type=="caption":
        buttons = []
        data = await get_configs(user_id)
        caption = data['caption']
        if caption is None:
            buttons.append([InlineKeyboardButton('✚ Add Caption ✚', 
                          callback_data="settings#addcaption")])
        else:
            buttons.append([InlineKeyboardButton('👀 See Caption', 
                          callback_data="settings#seecaption")])
            buttons[-1].append(InlineKeyboardButton('🗑️ Delete Caption', 
                          callback_data="settings#deletecaption"))
        buttons.append([InlineKeyboardButton('🔙 Back', 
                          callback_data="settings#main")])
        await query.message.edit_text(
            "<b><u>Custom Caption</b></u>\n\nYou Can Set A Custom Caption To Videos And Documents. Normaly Use Its Default Caption\n\n<b><u>Available Fillings :</b></u>\n\n<code>{filename}</code> : Filename\n<code>{size}</code> : File Size\n<code>{caption}</code> : Default Caption",
            reply_markup=InlineKeyboardMarkup(buttons))
                               
    elif type=="seecaption":   
        data = await get_configs(user_id)
        buttons = [[InlineKeyboardButton('✏️ Edit Caption', 
                      callback_data="settings#addcaption")
                   ],[
                   InlineKeyboardButton('🔙 Back', 
                     callback_data="settings#caption")]]
        await query.message.edit_text(
            f"<b><u>Your Custom Caption</b></u>\n\n<code>{data['caption']}</code>",
            reply_markup=InlineKeyboardMarkup(buttons))
    
    elif type=="deletecaption":
        await update_configs(user_id, 'caption', None)
        await query.message.edit_text(
            "Successfully Updated",
            reply_markup=InlineKeyboardMarkup(buttons))
                              
    elif type=="addcaption":
        await query.message.delete()
        try:
            text = await bot.send_message(query.message.chat.id, "Send your custom caption\n/cancel - <code>cancel this process</code>")
            caption = await bot.listen(chat_id=user_id, timeout=300)
            if caption.text=="/cancel":
                await caption.delete()
                return await text.edit_text(
                      "Process Canceled !",
                      reply_markup=InlineKeyboardMarkup(buttons))
            try:
                caption.text.format(filename='', size='', caption='')
            except KeyError as e:
                await caption.delete()
                return await text.edit_text(
                   f"Wrong Filling {e} Used In Your Caption. Change It",
                   reply_markup=InlineKeyboardMarkup(buttons))
            await update_configs(user_id, 'caption', caption.text)
            await caption.delete()
            await text.edit_text(
                "Successfully Updated",
                reply_markup=InlineKeyboardMarkup(buttons))
        except asyncio.exceptions.TimeoutError:
            await text.edit_text('Process Has Been Automatically Cancelled', reply_markup=InlineKeyboardMarkup(buttons))
  
    elif type=="button":
        buttons = []
        button = (await get_configs(user_id))['button']
        if button is None:
            buttons.append([InlineKeyboardButton('✚ Add Button ✚', 
                          callback_data="settings#addbutton")])
        else:
            buttons.append([InlineKeyboardButton('👀 See Button', 
                          callback_data="settings#seebutton")])
            buttons[-1].append(InlineKeyboardButton('🗑️ Remove Button ', 
                          callback_data="settings#deletebutton"))
        buttons.append([InlineKeyboardButton('🔙 Back', 
                          callback_data="settings#main")])
        await query.message.edit_text(
            "<b><u>Custom Button</b></u>\n\nYou Can Set A Inline Button To Messages.\n\n<b><u>Format :</b></u>\n`[Madflix Botz][buttonurl:https://t.me/Madflix_Bots]`\n",
            reply_markup=InlineKeyboardMarkup(buttons))
  
    elif type=="addbutton":
        await query.message.delete()
        try:
            txt = await bot.send_message(user_id, text="**Send your custom button.\n\nFORMAT:**\n`[forward bot][buttonurl:https://t.me/KR_Forward_Bot]`\n")
            ask = await bot.listen(chat_id=user_id, timeout=300)
            button_parsed = parse_buttons(ask.text.html)
            if not button_parsed:
                await ask.delete()
                return await txt.edit_text("Invalid Button")
            await update_configs(user_id, 'button', ask.text.html)
            await ask.delete()
            await txt.edit_text("Successfully Button Added",
                reply_markup=InlineKeyboardMarkup(buttons))
        except asyncio.exceptions.TimeoutError:
            await txt.edit_text('Process Has Been Automatically Cancelled', reply_markup=InlineKeyboardMarkup(buttons))
  
    elif type=="seebutton":
        button_val = (await get_configs(user_id))['button']
        button_markup = parse_buttons(button_val, markup=False)
        button_markup.append([InlineKeyboardButton("🔙 Back", "settings#button")])
        await query.message.edit_text(
             "**Your Custom Button**",
             reply_markup=InlineKeyboardMarkup(button_markup))
      
    elif type=="deletebutton":
        await update_configs(user_id, 'button', None)
        await query.message.edit_text(
            "Successfully Button Deleted",
            reply_markup=InlineKeyboardMarkup(buttons))
   
    elif type=="database":
        buttons = []
        db_uri = (await get_configs(user_id))['db_uri']
        if db_uri is None:
            buttons.append([InlineKeyboardButton('✚ Add URL ✚', 
                          callback_data="settings#addurl")])
        else:
            buttons.append([InlineKeyboardButton('👀 See URL', 
                          callback_data="settings#seeurl")])
            buttons[-1].append(InlineKeyboardButton('🗑️ Remove URL', 
                          callback_data="settings#deleteurl"))
        buttons.append([InlineKeyboardButton('🔙 Back', 
                          callback_data="settings#main")])
        await query.message.edit_text(
            "<b><u>Database</u></b>\n\nDatabase Is Required For Store Your Duplicate Messages Permenant. Other Wise Stored Duplicate Media May Be Disappeared When After Bot Restart.",
            reply_markup=InlineKeyboardMarkup(buttons))

    elif type=="addurl":
        await query.message.delete()
        uri = await bot.ask(user_id, "<b>please send your mongodb url.</b>\n\n<i>get your Mongodb url from [here](https://mongodb.com)</i>", disable_web_page_preview=True)
        if uri.text=="/cancel":
            return await uri.reply_text(
                      "Process Cancelled !",
                      reply_markup=InlineKeyboardMarkup(buttons))
        if not uri.text.startswith("mongodb+srv://") and not uri.text.endswith("majority"):
            return await uri.reply("Invalid Mongodb URL",
                       reply_markup=InlineKeyboardMarkup(buttons))
        await update_configs(user_id, 'db_uri', uri.text)
        await uri.reply("Successfully Database URL Added ✅",
                 reply_markup=InlineKeyboardMarkup(buttons))
  
    elif type=="seeurl":
        db_uri = (await get_configs(user_id))['db_uri']
        await query.answer(f"Database URL : {db_uri}", show_alert=True)
  
    elif type=="deleteurl":
        await update_configs(user_id, 'db_uri', None)
        await query.message.edit_text(
            "Successfully Your Database URL Deleted",
            reply_markup=InlineKeyboardMarkup(buttons))
      
    elif type=="filters":
        await query.message.edit_text(
            "<b><u>Custom Filters</u></b>\n\nConfigure The Type Of Messages Which You Want Forward",
            reply_markup=await filters_buttons(user_id))
  
    elif type=="nextfilters":
        await query.edit_message_reply_markup( 
            reply_markup=await next_filters_buttons(user_id))
   
    elif type.startswith("updatefilter"):
        i, key, value = type.split('-')
        if value=="True":
            await update_configs(user_id, key, False)
        else:
            await update_configs(user_id, key, True)
        if key in ['poll', 'protect']:
            return await query.edit_message_reply_markup(
               reply_markup=await next_filters_buttons(user_id)) 
        await query.edit_message_reply_markup(
            reply_markup=await filters_buttons(user_id))
   
    elif type.startswith("file_size"):
        settings_data = await get_configs(user_id)
        size_val = settings_data.get('file_size', 0)
        i, limit_sts = size_limit(settings_data['size_limit'])
        await query.message.edit_text(
            f'<b><u>Size Limit</u></b>\n\nYou Can Set File Size Limit To Forward\n\nStatus : Files With {limit_sts} `{size_val} MB` Will Forward',
            reply_markup=size_button(size_val)
        )  
    elif type.startswith("update_size"):
        size_up = int(query.data.split('-')[1])
        if 0 < size_up > 2000:
            return await query.answer("Size Limit Exceeded", show_alert=True)
        await update_configs(user_id, 'file_size', size_up)
        i, limit_sts = size_limit((await get_configs(user_id))['size_limit'])
        await query.message.edit_text(
            f'<b><u>Size Limit</u></b>\n\nYou Can Set File Size Limit To Forward\n\nStatus : Files With {limit_sts} `{size_up} MB` Will Forward',
            reply_markup=size_button(size_up))
  
    elif type.startswith('update_limit'):
        i, limit_val, size_val = type.split('-')
        limit_val, sts_val = size_limit(limit_val)
        await update_configs(user_id, 'size_limit', limit_val) 
        await query.message.edit_text(
           f'<b><u>Size Limit</u></b>\n\nYou Can Set File Size Limit To Forward\n\nStatus : Files With {sts_val} `{size_val} MB` Will Forward',
           reply_markup=size_button(int(size_val)))
      
    elif type == "add_extension":
        await query.message.delete() 
        ext = await bot.ask(user_id, text="Please Send Your Extensions (Seperete By Space)")
        if ext.text == '/cancel':
            return await ext.reply_text(
                      "Process Cancelled",
                      reply_markup=InlineKeyboardMarkup(buttons))
        extensions_list = ext.text.split(" ")
        extension_config = (await get_configs(user_id))['extension']
        if extension_config:
            for extn in extensions_list:
                extension_config.append(extn)
        else:
            extension_config = extensions_list
        await update_configs(user_id, 'extension', extension_config)
        await ext.reply_text(
            f"Successfully Updated",
            reply_markup=InlineKeyboardMarkup(buttons))
      
    elif type == "get_extension":
        extensions_data = (await get_configs(user_id))['extension']
        btn_ext = extract_btn(extensions_data)
        btn_ext.append([InlineKeyboardButton('✚ Add ✚', 'settings#add_extension')])
        btn_ext.append([InlineKeyboardButton('Remove All', 'settings#rmve_all_extension')])
        btn_ext.append([InlineKeyboardButton('🔙 Back', 'settings#main')])
        await query.message.edit_text(
            text='<b><u>Extensions</u></b>\n\nFiles With These Extiontions Will Not Forward',
            reply_markup=InlineKeyboardMarkup(btn_ext))
  
    elif type == "rmve_all_extension":
        await update_configs(user_id, 'extension', None)
        await query.message.edit_text(text="Successfully Deleted",
                                       reply_markup=InlineKeyboardMarkup(buttons))
                                       
    elif type == "add_keyword":
        await query.message.delete()
        ask_key = await bot.ask(user_id, text="Please Send The Keywords (Seperete By Space)")
        if ask_key.text == '/cancel':
            return await ask_key.reply_text(
                      "Process Canceled",
                      reply_markup=InlineKeyboardMarkup(buttons))
        keywords_list = ask_key.text.split(" ")
        keyword_config = (await get_configs(user_id))['keywords']
        if keyword_config:
            for word in keywords_list:
                keyword_config.append(word)
        else:
            keyword_config = keywords_list
        await update_configs(user_id, 'keywords', keyword_config)
        await ask_key.reply_text(
            f"Successfully Updated",
            reply_markup=InlineKeyboardMarkup(buttons))
  
    elif type == "get_keyword":
        keywords_data = (await get_configs(user_id))['keywords']
        btn_key = extract_btn(keywords_data)
        btn_key.append([InlineKeyboardButton('✚ Add ✚', 'settings#add_keyword')])
        btn_key.append([InlineKeyboardButton('Remove All', 'settings#rmve_all_keyword')])
        btn_key.append([InlineKeyboardButton('🔙 Back', 'settings#main')])
        await query.message.edit_text(
            text='<b><u>Keywords</u></b>\n\nFile With These Keywords In File Name Will Forwad',
            reply_markup=InlineKeyboardMarkup(btn_key))
      
    elif type == "rmve_all_keyword":
        await update_configs(user_id, 'keywords', None)
        await query.message.edit_text(text="Successfully Deleted",
                                       reply_markup=InlineKeyboardMarkup(buttons))
                                       
    elif type.startswith("alert"):
        alert_msg = type.split('_')[1]
        await query.answer(alert_msg, show_alert=True)
      
def main_buttons():
  buttons = [[
       InlineKeyboardButton('🤖 Bots',
                    callback_data=f'settings#bots'),
       InlineKeyboardButton('🔥 Channels',
                    callback_data=f'settings#channels')
       ],[
       InlineKeyboardButton('✏️ Caption',
                    callback_data=f'settings#caption'),
       InlineKeyboardButton('🗃 MongoDB',
                    callback_data=f'settings#database')
       ],[
       InlineKeyboardButton('🕵‍♀ Filters',
                    callback_data=f'settings#filters'),
       InlineKeyboardButton('🏓 Button',
                    callback_data=f'settings#button')
       ],[
       InlineKeyboardButton('⚙️ Extra Settings',
                    callback_data='settings#nextfilters')
       ],[      
       InlineKeyboardButton('🔙 Back', callback_data='back')
       ]]
  return InlineKeyboardMarkup(buttons)

def size_limit(limit):
   if str(limit) == "None":
      return None, ""
   elif str(limit) == "True":
      return True, "more than"
   else:
      return False, "less than"

def extract_btn(datas):
    i = 0
    btn = []
    if datas:
       for data in datas:
         if i >= 5:
            i = 0
         if i == 0:
            btn.append([InlineKeyboardButton(data, f'settings#alert_{data}')])
            i += 1
            continue
         elif i > 0:
            btn[-1].append(InlineKeyboardButton(data, f'settings#alert_{data}'))
            i += 1
    return btn 

def size_button(size):
  buttons = [[
       InlineKeyboardButton('+',
                    callback_data=f'settings#update_limit-True-{size}'),
       InlineKeyboardButton('=',
                    callback_data=f'settings#update_limit-None-{size}'),
       InlineKeyboardButton('-',
                    callback_data=f'settings#update_limit-False-{size}')
       ],[
       InlineKeyboardButton('+1',
                    callback_data=f'settings#update_size-{size + 1}'),
       InlineKeyboardButton('-1',
                    callback_data=f'settings#update_size_-{size - 1}')
       ],[
       InlineKeyboardButton('+5',
                    callback_data=f'settings#update_size-{size + 5}'),
       InlineKeyboardButton('-5',
                    callback_data=f'settings#update_size_-{size - 5}')
       ],[
       InlineKeyboardButton('+10',
                    callback_data=f'settings#update_size-{size + 10}'),
       InlineKeyboardButton('-10',
                    callback_data=f'settings#update_size_-{size - 10}')
       ],[
       InlineKeyboardButton('+50',
                    callback_data=f'settings#update_size-{size + 50}'),
       InlineKeyboardButton('-50',
                    callback_data=f'settings#update_size_-{size - 50}')
       ],[
       InlineKeyboardButton('+100',
                    callback_data=f'settings#update_size-{size + 100}'),
       InlineKeyboardButton('-100',
                    callback_data=f'settings#update_size_-{size - 100}')
       ],[
       InlineKeyboardButton('↩ Back',
                    callback_data="settings#main")
     ]]
  return InlineKeyboardMarkup(buttons)
       
async def filters_buttons(user_id):
  filter_cfg = await get_configs(user_id)
  filters_list = filter_cfg['filters']
  buttons = [[
       InlineKeyboardButton('🏷️ Forward Tag',
                    callback_data=f'settings_#updatefilter-forward_tag-{filter_cfg["forward_tag"]}'),
       InlineKeyboardButton('✅' if filter_cfg['forward_tag'] else '❌',
                    callback_data=f'settings#updatefilter-forward_tag-{filter_cfg["forward_tag"]}')
       ],[
       InlineKeyboardButton('🖍️ Texts',
                    callback_data=f'settings_#updatefilter-text-{filters_list["text"]}'),
       InlineKeyboardButton('✅' if filters_list['text'] else '❌',
                    callback_data=f'settings#updatefilter-text-{filters_list["text"]}')
       ],[
       InlineKeyboardButton('📁 Documents',
                    callback_data=f'settings_#updatefilter-document-{filters_list["document"]}'),
       InlineKeyboardButton('✅' if filters_list['document'] else '❌',
                    callback_data=f'settings#updatefilter-document-{filters_list["document"]}')
       ],[
       InlineKeyboardButton('🎞️ Videos',
                    callback_data=f'settings_#updatefilter-video-{filters_list["video"]}'),
       InlineKeyboardButton('✅' if filters_list['video'] else '❌',
                    callback_data=f'settings#updatefilter-video-{filters_list["video"]}')
       ],[
       InlineKeyboardButton('📷 Photos',
                    callback_data=f'settings_#updatefilter-photo-{filters_list["photo"]}'),
       InlineKeyboardButton('✅' if filters_list['photo'] else '❌',
                    callback_data=f'settings#updatefilter-photo-{filters_list["photo"]}')
       ],[
       InlineKeyboardButton('🎧 Audios',
                    callback_data=f'settings_#updatefilter-audio-{filters_list["audio"]}'),
       InlineKeyboardButton('✅' if filters_list['audio'] else '❌',
                    callback_data=f'settings#updatefilter-audio-{filters_list["audio"]}')
       ],[
       InlineKeyboardButton('🎤 Voices',
                    callback_data=f'settings_#updatefilter-voice-{filters_list["voice"]}'),
       InlineKeyboardButton('✅' if filters_list['voice'] else '❌',
                    callback_data=f'settings#updatefilter-voice-{filters_list["voice"]}')
       ],[
       InlineKeyboardButton('🎭 Animations',
                    callback_data=f'settings_#updatefilter-animation-{filters_list["animation"]}'),
       InlineKeyboardButton('✅' if filters_list['animation'] else '❌',
                    callback_data=f'settings#updatefilter-animation-{filters_list["animation"]}')
       ],[
       InlineKeyboardButton('🃏 Stickers',
                    callback_data=f'settings_#updatefilter-sticker-{filters_list["sticker"]}'),
       InlineKeyboardButton('✅' if filters_list['sticker'] else '❌',
                    callback_data=f'settings#updatefilter-sticker-{filters_list["sticker"]}')
       ],[
       InlineKeyboardButton('▶️ Skip Duplicate',
                    callback_data=f'settings_#updatefilter-duplicate-{filter_cfg["duplicate"]}'),
       InlineKeyboardButton('✅' if filter_cfg['duplicate'] else '❌',
                    callback_data=f'settings#updatefilter-duplicate-{filter_cfg["duplicate"]}')
       ],[
       InlineKeyboardButton('🔙 back',
                    callback_data="settings#main")
       ]]
  return InlineKeyboardMarkup(buttons) 

async def next_filters_buttons(user_id):
  filter_cfg = await get_configs(user_id)
  filters_list = filter_cfg['filters']
  buttons = [[
       InlineKeyboardButton('📊 Poll',
                    callback_data=f'settings_#updatefilter-poll-{filters_list["poll"]}'),
       InlineKeyboardButton('✅' if filters_list['poll'] else '❌',
                    callback_data=f'settings#updatefilter-poll-{filters_list["poll"]}')
       ],[
       InlineKeyboardButton('🔒 Secure Message',
                    callback_data=f'settings_#updatefilter-protect-{filter_cfg["protect"]}'),
       InlineKeyboardButton('✅' if filter_cfg['protect'] else '❌',
                    callback_data=f'settings#updatefilter-protect-{filter_cfg["protect"]}')
       ],[
       InlineKeyboardButton('🛑 Size Limit',
                    callback_data='settings#file_size')
       ],[
       InlineKeyboardButton('💾 Extension',
                    callback_data='settings#get_extension')
       ],[
       InlineKeyboardButton('📌 Keywords',
                    callback_data='settings#get_keyword')
       ],[
       InlineKeyboardButton('🔙 Back', 
                    callback_data="settings#main")
       ]]
  return InlineKeyboardMarkup(buttons)
