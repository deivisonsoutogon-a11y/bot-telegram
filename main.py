import os
import threading
import requests
import telebot
from flask import Flask

# --- Servidor Web para o Render manter o bot ativo 24/7 ---
app = Flask('')

@app.route('/')
def home():
    return "Bot de Downloads ativo 24h!"

def run_web_server():
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

# --- TOKEN DO BOT ---
TOKEN = '8850265902:AAEw5eD2VMCXfEseVNgHOfqL4PkZkHgw0us'
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    msg_texto = (
        "👋 **Bem-vindo ao Bot de Downloads!**\n\n"
        "Envia ou cola qualquer link de vídeo do **TikTok, Instagram, YouTube Shorts ou Kwai** "
        "aqui no chat para baixar sem marca d'água!"
    )
    bot.reply_to(message, msg_texto, parse_mode='Markdown')

@bot.message_handler(func=lambda message: message.text and 'http' in message.text)
def handle_video_download(message):
    words = message.text.split()
    url = None
    for word in words:
        if word.startswith('http://') or word.startswith('https://'):
            url = word
            break

    if not url:
        return

    chat_id = message.chat.id
    message_id = message.message_id

    status_msg = bot.reply_to(message, "⏳ *A processar e a baixar o vídeo, aguarde...*", parse_mode='Markdown')
    output_filename = f"video_{message_id}.mp4"

    try:
        # Requisição à API do Cobalt
        cobalt_api = "https://api.cobalt.tools/api/json"
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        payload = {
            "url": url,
            "vCodec": "h264",
            "noWatermark": True
        }

        response = requests.post(cobalt_api, json=payload, headers=headers, timeout=30)
        res_data = response.json()

        video_url = None
        if res_data.get("status") in ["stream", "redirect"]:
            video_url = res_data.get("url")
        elif res_data.get("status") == "picker" and len(res_data.get("picker", [])) > 0:
            video_url = res_data["picker"][0].get("url")

        if not video_url:
            raise Exception("Não foi possível obter o link direto do vídeo.")

        # Descarrega o ficheiro do vídeo
        video_bytes = requests.get(video_url, stream=True, timeout=60)
        with open(output_filename, 'wb') as f:
            for chunk in video_bytes.iter_content(chunk_size=8192):
                f.write(chunk)

        if os.path.exists(output_filename):
            bot.edit_message_text("📤 *A enviar o vídeo...*", chat_id=chat_id, message_id=status_msg.message_id, parse_mode='Markdown')

            with open(output_filename, 'rb') as video_file:
                bot.send_video(
                    chat_id=chat_id,
                    video=video_file,
                    reply_to_message_id=message_id,
                    caption="✨ *Vídeo descarregado com sucesso!*",
                    parse_mode='Markdown',
                    supports_streaming=True
                )

            os.remove(output_filename)
            bot.delete_message(chat_id=chat_id, message_id=status_msg.message_id)

    except Exception as e:
        bot.edit_message_text(f"❌ *Ocorreu um erro ao processar este link.*\n`Erro: {str(e)[:100]}`", chat_id=chat_id, message_id=status_msg.message_id, parse_mode='Markdown')
        if os.path.exists(output_filename):
            os.remove(output_filename)

if __name__ == '__main__':
    t = threading.Thread(target=run_web_server)
    t.start()

    print("🤖 Bot rodando com sucesso...")
    bot.infinity_polling()
