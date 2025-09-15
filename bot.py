import os
import random
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import requests
from telegram import Bot, Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ---------------- CONFIG -----------------
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("Please set TELEGRAM_BOT_TOKEN environment variable!")

PREFERRED_PAIRS = {
    5758014151: [7874738561, 7454346375],
    7874738561: [5758014151],
    7454346375: [5758014151],
}
PREFERRED_CHANCE = 0.55
SAMPLE_NAMES = ["Romeo", "Juliet", "Aryan", "Isha", "Sneha", "Rohit"]

bot = Bot(BOT_TOKEN)

# -------- Profile Picture Fetch --------
def get_profile_pic(user_id):
    try:
        photos = bot.get_user_profile_photos(user_id, limit=1)
        if photos.total_count > 0:
            file_id = photos.photos[0][0].file_id
            file = bot.get_file(file_id)
            content = requests.get(file.file_path).content
            return Image.open(BytesIO(content)).convert("RGBA")
    except Exception:
        pass
    # fallback avatar
    img = Image.new("RGBA", (300, 300), (200, 200, 200, 255))
    draw = ImageDraw.Draw(img)
    draw.ellipse((0, 0, 300, 300), fill=(150, 150, 150, 255))
    return img

# -------- Cute Couple Image --------
def make_cute_couple_image(user_a_name, user_a_img, user_b_name, user_b_img, preferred=False):
    bg_color = (255, 220, 230) if preferred else (220, 240, 255)
    img = Image.new("RGBA", (800, 400), bg_color)
    draw = ImageDraw.Draw(img)

    def circle_avatar(avatar):
        size = 300
        avatar = avatar.resize((size, size))
        # Shadow
        shadow = Image.new("RGBA", (size+20, size+20), (0,0,0,0))
        shadow_draw = ImageDraw.Draw(shadow)
        shadow_draw.ellipse((10,10,size+10,size+10), fill=(0,0,0,100))
        shadow.paste(avatar, (10,10), avatar)
        # Border
        border = Image.new("RGBA", (size+20, size+20), (0,0,0,0))
        border_draw = ImageDraw.Draw(border)
        border_draw.ellipse((0,0,size+20,size+20), outline=(255,255,255,255), width=6)
        border.paste(shadow, (0,0), shadow)
        return border

    user_a_avatar = circle_avatar(user_a_img)
    user_b_avatar = circle_avatar(user_b_img)
    img.paste(user_a_avatar, (50, 50), user_a_avatar)
    img.paste(user_b_avatar, (450, 50), user_b_avatar)

    heart_color = (255, 100, 150, 200)
    for _ in range(15):
        x = random.randint(100, 700)
        y = random.randint(50, 350)
        draw.text((x,y), "❤️", fill=heart_color, font=ImageFont.load_default())

    try:
        font = ImageFont.truetype("arial.ttf", 50)
    except:
        font = ImageFont.load_default()

    text = "Couple of the Day ❤️" if preferred else "Random Couple 💙"
    text_size = draw.textsize(text, font=font)
    draw.rectangle([ (img.width//2 - text_size[0]//2 - 10, 10),
                     (img.width//2 + text_size[0]//2 + 10, 70) ],
                     fill=(255,255,255,200), outline=(200,200,200,255), width=2)
    draw.text((img.width//2 - text_size[0]//2, 15), text, fill=(0,0,0), font=font)

    bio = BytesIO()
    img.save(bio, format="PNG")
    bio.seek(0)
    return bio

# -------- Choose Partner --------
def choose_partner(user_id):
    if user_id in PREFERRED_PAIRS and random.random() < PREFERRED_CHANCE:
        return random.choice(PREFERRED_PAIRS[user_id]), True
    return random.choice(SAMPLE_NAMES), False

# -------- Command Handler --------
async def command_couples(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    partner, is_pref = choose_partner(user.id)

    if isinstance(partner, int):
        partner_obj = await bot.get_chat(partner)
        partner_name = partner_obj.full_name
        partner_img = get_profile_pic(partner)
    else:
        partner_name = partner
        partner_img = Image.new("RGBA", (300, 300), (150, 150, 150, 255))

    user_img = get_profile_pic(user.id)
    img = make_cute_couple_image(user.full_name, user_img, partner_name, partner_img, preferred=is_pref)

    caption = f"💖 {user.full_name} + {partner_name} = {'❤️' if is_pref else '💙'}"
    await context.bot.send_photo(chat_id=update.effective_chat.id, photo=img, caption=caption)

# -------- Run Bot --------
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("couples", command_couples))

print("Bot running with polling...")
app.run_polling()
