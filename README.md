# Discord Staff Bot

Questo è un bot Discord per la gestione dello staff tramite comandi slash (`/`). Permette di assegnare ruoli, gestire blacklist, segnare assenze e visualizzare la lista dello staff attivo e anche usufruisce di un sistema ticket per la tua community.

## Funzionalità principali
- `/pex` — Assegna un ruolo a un utente
- `/depex` — Declassa un utente a user
- `/blacklist` — Aggiunge un utente alla blacklist e lo banna permanentemente
- `/blacklistlist`-Permette di vedere la lista di tutti gli utenti blacklistati
- `/assenza` — Segna un utente in assenza
- `/stafflist` — Mostra la lista dello staff attivo
- `/ticketpannel`- Crea un pannello per i ticket e la categoria Ticket, modificate il codice per personalizzare il messaggio 
- `/claim`-Permette allo staff di prendere in carico un ticket
- `/rename`-Permette allo staff di rinominare un ticket
- `/close`-Permette allo staff di chiudere un ticket

## Requisiti
- Python 3.10 o superiore
- Un bot Discord con i permessi corretti ("Server Members Intent" e "Message Content Intent" abilitati nel portale Discord Developer)

## Installazione
1. Clona la repository:
   ```sh
   git clone https://github.com/Ghost001-byte/staff-management-discord-bot.git
   cd staff-management-discord-bot.git
   ```
2. Installa le dipendenze:
   ```sh
   pip install -r requirements.txt
   ```
3. Crea un file `.env` oppure imposta le variabili d'ambiente:
   - `DISCORD_TOKEN` — Il token del tuo bot Discord
   - `LOG_CHANNEL_ID` — (opzionale) ID del canale dove inviare i log

   Esempio su Windows PowerShell:
   ```powershell
   $env:DISCORD_TOKEN="il-tuo-token"
   $env:LOG_CHANNEL_ID="1234567890"
   python "staff-management-discord-bot.git.py"
   ```

## Avvio

```sh
python "staff-management-discord-bot.git.py"
```

## Note
- **Non condividere mai il tuo token Discord pubblicamente!**
- Il file `bot_data.json` verrà creato automaticamente per salvare ruoli, blacklist e assenze.
- Se vuoi ripristinare i dati, elimina `bot_data.json` a bot spento.

## Versione
-Staffbot v:1.0
-Made by Ghost


