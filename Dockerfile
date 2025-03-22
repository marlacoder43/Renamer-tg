# 1. Rasm sifatida Python 3.9 (yoki yangi versiya) ni ishlatamiz
FROM python:3.9

# 2. Ishchi katalogni yaratamiz va unga o'tamiz
WORKDIR /app

# 3. Kerakli kutubxonalarni o'rnatamiz
RUN pip install --no-cache-dir pyrogram tgcrypto

# 4. Git va boshqa zaruriy paketlarni o‘rnatamiz
RUN apt-get update && apt-get install -y wget && apt-get clean

# 5. GitHub-dan loyihani yuklab olamiz
RUN wget -0 https://github.com/marlacoder43/Renamer-tg/blob/main/main.py

# 7. Botni ishga tushiramiz
CMD ["python", "main.py"]
