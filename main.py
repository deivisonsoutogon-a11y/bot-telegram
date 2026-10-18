import os
import threading
import telebot
from flask import Flask
from yt_dlp import YoutubeDL

# --- Servidor Web para o Render manter o bot ativo ---
app = Flask('')


@app.route('/')
def home():
  return 'Bot do Telegram ativo 24h!'


def run_web_server():
  port = int(os.environ.get('PORT', 10000))
  app.run(host='0.0.0.0', port=port)


# --- TOKEN DO BOT ---
# Substitui 'SEU_TOKEN_AQUI' pelo teu Token real do BotFather!
TOKEN = '8850265902:AAEw5eD2VMCXfEseVNgHOfqL4PkZkHgw0us'
bot = telebot.TeleBot(TOKEN)


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
  msg_texto = (
      '👋 **Bem-vindo ao Grupo de Downloads!**\n\n'
      'Para baixar qualquer vídeo sem marca d\'água, basta **colar o link'
      ' do vídeo** (TikTok, Instagram Reels, YouTube Shorts, Kwai) aqui no'
      ' chat!'
  )
  bot.reply_to(message, msg_texto, parse_mode='Markdown')


@bot.message_handler(
    func=lambda message: message.text and 'http' in message.text
)
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

  status_msg = bot.reply_to(
      message,
      '⏳ *Baixando o vídeo, aguarde alguns segundos...*',
      parse_mode='Markdown',
  )

  output_filename = f'video_{message_id}.mp4'

  ydl_opts = {
      'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
      'outtmpl': output_filename,
      'quiet': True,
      'no_warnings': True,
  }

  try:
    with YoutubeDL(ydl_opts) as ydl:
      ydl.download([url])

    if os.path.exists(output_filename):
      bot.edit_message_text(
          '📤 *Enviando o vídeo...*',
          chat_id=chat_id,
          message_id=status_msg.message_id,
          parse_mode='Markdown',
      )

      with open(output_filename, 'rb') as video_file:
        bot.send_video(
            chat_id=chat_id,
            video=video_file,
            reply_to_message_id=message_id,
            caption='✨ *Seu vídeo baixado sem marca d\'água!*',
            parse_mode='Markdown',
            supports_streaming=True,
        )

      os.remove(output_filename)
      bot.delete_message(chat_id=chat_id, message_id=status_msg.message_id)

    else:
      bot.edit_message_text(
          '❌ Não foi possível obter o vídeo baixado.',
          chat_id=chat_id,
          message_id=status_msg.message_id,
      )

  except Exception as e:
    bot.edit_message_text(
        f'❌ Ocorreu um erro ao processar este link.\n`Erro: {str(e)[:100]}`',
        chat_id=chat_id,
        message_id=status_msg.message_id,
        parse_mode='Markdown',
    )
    if os.path.exists(output_filename):
      os.remove(output_filename)


if __name__ == '__main__':
  t = threading.Thread(target=run_web_server)
  t.start()

  print('🤖 Bot do Grupo rodando com sucesso...')
  bot.infinity_polling()
