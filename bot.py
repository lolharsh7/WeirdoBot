import os
import random
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import requests
from telegram import Bot, Update
from telegram.ext import Updater, CommandHandler, CallbackContext

# ---------------- CONFIG -----------------
BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("Please set BOT_TOKEN environment variable!")

PREFERRED_PAIRS = {
    5758014151: [7874738561, 7454346375],
    7874738561: [5758014151],
    7454346375: [5758014151],
}
PREFERRED_CHANCE = 0.55  # 55% chance preferred pair selected
SAMPLE_NAMES = ["Romeo", "Juliet", "Aryan", "Isha", "Sneha", "Rohit"]
# -----------------------------------------

bot = Bot(BOT_TOKEN)
updater = Updater(BOT_TOKEN, use_context=True)

def get_profile_pic(user_id):
    """Fetch Telegram profile pic or fallback default avatar."""
    try:
        photos = bot.get_user_profile_photos(user_id, limit=1)
        if photos.total_count > 0:
            file_id = photos.photos[0][0].file_id
            file = bot.get_file(file_id)
            content = requests.get(file.file_path).content
            return Image.open(BytesIO(content)).convert("RGBA")
    except Exception:
        pass
    # Default avatar
    img = Image.new("RGBA", (300, 300), (200, 200, 200, 255))
    draw = ImageDraw.Draw(img)
    draw.ellipse((0, 0, 300, 300), fill=(150, 150, 150, 255))
    return img

def make_couple_image(user_a_name, user_a_img, user_b_name, user_b_img, preferred=False):
    """Generate couple image with both profile pics."""
    bg_color = (255, 200, 200) if preferred else (200, 220, 255)
    img = Image.new("RGBA", (800, 400), bg_color)

    # Resize profile pics
    user_a_img = user_a_img.resize((300, 300))
    user_b_img = user_b_img.resize((300, 300))

    img.paste(user_a_img, (50, 50), user_a_img)
    img.paste(user_b_img, (450, 50), user_b_img)

    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 50)
    except:
        font = ImageFont.load_default()

    text = "Couple of the Day ❤️" if preferred else "Random Couple 💙"
    draw.text((250, 10), text, fill=(0, 0, 0), font=font)

    bio = BytesIO()
    img.save(bio, format="PNG")
    bio.seek(0)
    return bio

def choose_partner(user_id):
    """Select partner based on preferred chance or random."""
    if user_id in PREFERRED_PAIRS and random.random() < PREFERRED_CHANCE:
        partner_id = random.choice(PREFERRED_PAIRS[user_id])
        return partner_id, True
    return random.choice(SAMPLE_NAMES), False

def command_couples(update: Update, context: CallbackContext):
    user = update.effective_user
    chat_id = update.effective_chat.id

    partner, is_pref = choose_partner(user.id)

    if isinstance(partner, int):
        # Partner is real Telegram user
        partner_obj = bot.get_chat(partner)
        partner_name = partner_obj.full_name
        partner_img = get_profile_pic(partner)
    else:
        # Random fallback name
        partner_name = partner
        partner_img = Image.new("RGBA", (300, 300), (150, 150, 150, 255))

    user_img = get_profile_pic(user.id)
    img = make_couple_image(user.full_name, user_img, partner_name, partner_img, preferred=is_pref)

    caption = f"💖 {user.full_name} + {partner_name} = {'❤️' if is_pref else '💙'}"
    context.bot.send_photo(chat_id=chat_id, photo=img, caption=caption)

dispatcher = updater.dispatcher
dispatcher.add_handler(CommandHandler("couples", command_couples))

if __name__ == "__main__":
    print("Bot running with polling...")
    updater.start_polling()
    updater.idle()
