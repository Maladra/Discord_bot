import asyncio
import async_timeout
import discord
from discord.ext import commands
import discord.ext
import configparser
import os
import youtube_dl

######
#pass_context in 1.0+ not required
######



################## FICHIER DE CONFIGURATION BOT ####################
config = configparser.ConfigParser()
config.read("config.ini")

prefix=config.get('CONFIG_BOT','prefix')
token=config.get('CONFIG_BOT' , 'token')
client = commands.Bot(command_prefix=prefix)
role_liste=config.get('CONFIG_BOT','role_liste').split(",")

chann_regle=config.get('CHANNEL_ID','chann_regle')
chann_presentation=config.get('CHANNEL_ID','chann_presentation')
chann_suggestion=config.get('CHANNEL_ID','chann_suggestion')
chann_question=config.get('CHANNEL_ID', 'chann_question')
chann_generale=config.get('CHANNEL_ID','chann_generale')

client = commands.Bot(command_prefix=prefix)

# Suppress noise about console usage from errors
youtube_dl.utils.bug_reports_message = lambda: ''


########### OPTION POUR YTDL ##########
ytdl_format_options = {
    'format': 'bestaudio/best',
    'quiet' : True,
    'outtmpl' : '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'noplaylist' : True,
    'nocheckcertificate' : True,
    'no_warning' : True,
    'default_search' : 'auto'
}

ffmpeg_options = {
    'before_options': '-nostdin',
    'options': '-vn'
    }
ytdl = youtube_dl.YoutubeDL(ytdl_format_options)


########## PERMET DE RECUPERER MUSIQUE DEPUIS YOUTUBE ##########
class YTDLSource(discord.PCMVolumeTransformer):
    """A class which uses YTDL to retrieve a song and returns it as a source for Discord."""
    def __init__(self, source, *, data, volume=.4):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None ,stream=True):
        loop = loop or asyncio.get_event_loop()
        print (loop)
        #data = await loop.run_in_executor(None, ytdl.extract_info, url)
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        if 'entries' in data:
            data = data['entries'][0]
        filename = data['url']
        #filename = ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)




########## PLAYER MUSIC ##########

class MusicPlayer:
    def __init__(self, client, ctx):
        self.bot = client # représente le bot

        self.queue = asyncio.Queue() # liste de musique a jouer
        self.next = asyncio.Event() # bloque pour passer a la prochaine musique
        self.die = asyncio.Event() # permet de check l'inactivité + pour la deco du bot

        self.guild = ctx.guild # représente le serveur
        self.default_chan = ctx.channel # représente le channel du bot
        self.current = None
        self.volume = .4

        self.now_playing = None

        self.player_task = self.bot.loop.create_task(self.player_loop()) # loop player
        self.inactive_task = self.bot.loop.create_task(self.inactive_check(ctx)) # check inactivite

    async def inactive_check(self, ctx):
        await self.die.wait()
        await ctx.invoke(self.bot.get_command('stop'))

    async def player_loop(self):
        await self.bot.wait_until_ready()

        while not self.bot.is_closed():
            self.next.clear()

            try:
                with async_timeout.timeout(300):  # Auto leave after 5 minutes of inactivity.
                    entry = await self.queue.get()
            except asyncio.TimeoutError:
                await self.default_chan.send("J'ai été inactif pendant 5 minutes. Goodbye!")
                return self.die.set()

            try:
                info = await YTDLSource.from_url(entry.query, loop=self.bot.loop)
                info.volume = self.volume
            except Exception:
                await self.default_chan.send(f"Une erreur c'est produite avec la requete: `{entry.query}`")
                continue

            channel = entry.channel
            requester = entry.requester
            self.guild.voice_client.play(info, after=lambda s: self.bot.loop.call_soon_threadsafe(self.next.set()))
            self.nb_skip =0 # EN TEST
            self.user_voted=[] # EN TEST
            self.now_playing = await channel.send(f'**En lecture:** `{info.title}` ajoutée par `{requester}`')
            await self.next.wait()  # Wait until the players after function is called.

            try:
                await self.now_playing.delete()
            except (discord.Forbidden, discord.HTTPException):
                pass

class MusicEntry:
    def __init__(self, ctx, query):
        self.requester = ctx.author
        self.channel = ctx.channel
        self.query = query

bot = client
players = {}
def get_player(ctx):
    try:
        player = players[ctx.guild.id]
    except KeyError:
        player = MusicPlayer(bot, ctx)
        players[ctx.guild.id] = player
    return player

########## START COMMAND BOT ##########
@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print ('------')
"""
async def my_background_task():
    await client.wait_until_ready()
    channel = client.get_channel(int(chann_generale))
    channel_send_suggestion=client.get_channel(int(chann_suggestion))
    channel_send_question=client.get_channel(int(chann_question))
    while True:
        await channel.send("Les admins (Chef de Clan, Lieutenant et Guérisseur) sont à votre disposition pour tout renseignement. Si vous avez quelque chose à dire (problèmes, suggestion, question, etc...), n'hésitez pas à les contacter en mp, ou dans les channels "+ channel_send_suggestion.mention +" et " + channel_send_question.mention + ".") 


        await asyncio.sleep(25200) #18000
"""


@client.event
async def on_member_join(member):
    channel_mp_regle = client.get_channel(int(chann_regle))
    channel_mp_suggestion= client.get_channel(int(chann_suggestion))
    channel_mp_question=client.get_channel(int(chann_question))
    await member.send("Bienvenue " + member.mention + " sur le serveur Mirabilia World de Camifelis. Pense à lire les règles dans le channel " + channel_mp_regle.mention + " et à faire ta présentation dans le channel dédié à cet effet, ceci te permettra de discuter et de prendre part à la vie de ce serveur. N'hésite pas à poster dans " + channel_mp_suggestion.mention + " et/ou " + channel_mp_question.mention + " si tu en as, ou à contacter en MP un admin (Chef de Clan, Lieutenant, Guérisseur) si tu as un problème. En espérant que tu passeras un bon moment et à bientôt !")


@client.event
async def on_message(message):
    if message.author == client.user:
         return

    elif message.content.startswith('!help'):
        await message.channel.send("```Vous trouverez plus bas la liste des commandes disponibles:\n\n!help  :  Affiche ce message\n!music_help  :  Permet d'obtenir l'aide pour les commandes musicales\n!purge :  Permet de supprimer les messages\n!kick  :  Permet de kicker un utilisateur\n!ban  :  Permet de bannir un utilisateur```")

    elif message.content.startswith('!music_help'):
        await message.channel.send("```Commande musicale pour Spybot:\n\n!join:  Demande à Spybot de vous rejoindre\n!play  :  Ajoute une musique a la playlist\n!skip  :  Permet de voter pour passer une musique\n!current  :  Informations sur la musique en cours\n!stop  :  Commande pour les admins, permet d'arrêter Spybot```")

    elif message.channel.id == int(chann_presentation):
         i=0
         for r in message.author.roles:
             i=i+1
         if i <2:
             role = discord.utils.get(message.author.guild.roles, name=role_liste[1])
             user=message.author
             print(role.id)
             print(user)
             await user.add_roles(role)

    await client.process_commands(message)


@client.command(pass_context=True)
@commands.has_permissions(kick_members=True)
async def kick(ctx, member : discord.Member):
    print (member)
    await ctx.guild.kick(member)
    await ctx.send(member.mention +" a été kick")


@client.command(pass_context=True)
@commands.has_permissions(ban_members=True)
async def ban(ctx, member : discord.Member):
    print (member)
    await ctx.guild.ban(member)
    await ctx.send(member.mention + " a été banni")


@client.command(pass_context=True)
@commands.has_permissions(manage_messages=True)
async def purge (ctx , number):
    channel = ctx.message.channel
    number = int(number)
    await channel.purge(limit=number+1)

client.remove_command('help')

#client.my_task = client.loop.create_task(my_background_task())



########################################################################################################################

#################################################  MUSIC PART BOT  #####################################################

########################################################################################################################

@client.command(pass_context=True, name='join')
async def voice_connect(ctx, *, channel: discord.VoiceChannel=None):
    """Summon the bot to a voice channel.
    This command handles both summoning and moving the bot."""
    channel = getattr(ctx.author.voice, 'channel', channel)
    vc = ctx.guild.voice_client
    if not channel:
        return await ctx.send("Rejoins d'abord un channel avant d'appeler Spybot !")
    if not vc:
        try:
            await channel.connect(timeout=10)
        except asyncio.TimeoutError:
            return await ctx.send('Je suis incapable de rejoindre ce channel, veuillez ré-essayer.')
        await ctx.send(f'Je me connecte à : **{channel}**', delete_after=15)
    else:
        if channel == vc.channel:
            return
        try:
            await vc.move_to(channel)
        except Exception:
            return await ctx.send('Je suis incapable de rejoindre ce channel.')
        await ctx.send(f'Je me déplace dans le channel: **{channel}**', delete_after=15)

@client.command(name='play', pass_context=True)
async def play_song(ctx, *, query: str):
    """Add a song to the queue.
    Uses YTDL to auto search for a song. A URL may also be provided."""
    vc = ctx.guild.voice_client
    if vc is None:
        await ctx.invoke(voice_connect)
        if not ctx.guild.voice_client:
            return
    else:
        if ctx.author not in vc.channel.members:
            return await ctx.send(f'Tu dois être dans le channel **{vc.channel}** pour ajouter une musique.', delete_after=30)
    player = get_player(ctx)
    entry = MusicEntry(ctx, query)
    await player.queue.put(entry)
    print (client.voice_clients)
    await ctx.send(f'Musique ajoutée: `{query}` à la playlist.', delete_after=30)



@client.command(name='stop', pass_context=True)
@commands.has_permissions(manage_messages=True)
async def stop_player(ctx):
    vc = ctx.guild.voice_client
    print (vc)

    if vc is None:
        return

    player = get_player(ctx)

    vc.stop()
    try:
        player.player_task.cancel()
        del players[ctx.guild.id]
    except Exception as e:
        return print(e)

    await vc.disconnect()
    await ctx.send ('Déconnexion du channel, et vidage de la playlist.', delete_after=15)

    try:
        player.inactive_task.cancel()
    except Exception as e:
        print(e)

@client.command(name='skip')
async def skip_song(ctx):
    vc = ctx.guild.voice_client
    print (vc)
    if vc is None or not vc.is_connected() or not vc.is_playing():
        return await ctx.send('Je ne joue actuellement aucune musique', delete_after=20)
    nombre_user_chann=len(vc.channel.members)-1 # moins le bot
    print (nombre_user_chann)
    nb_vote_requis = int(nombre_user_chann/2) # nombre de vote requis pour skip
    player = get_player(ctx)
    if ctx.author in player.user_voted:
        print ("Tu as déja voté pour passer cette musique.", delete_after=10)
    else:
        player.nb_skip +=1
        player.user_voted.append(ctx.author)
        print("Ton vote pour passer la musique a été pris en compte.", delete_after=10)

    if player.nb_skip >= nb_vote_requis:
        vc.stop()
        await ctx.send('La musique a été passée',delete_after=10)


@client.command(name='current')
async def current_song(ctx):
    vc = ctx.guild.voice_client

    if not vc.is_playing():
        return await ctx.send('Je ne joue actuellement aucune musique.')

    player = get_player(ctx)

    msg = player.now_playing.content

    try:
        await player.now_playing.delete()
    except (discord.Forbidden, discord.HTTPException):
        pass

    player.now_playing = await ctx.send(msg)

client.run(token)


