import asyncio
import discord
from discord.ext import commands
import discord.ext
import configparser
import os


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
         await message.channel.send('```Vous trouverez plus bas la liste des commandes disponibles:\n\n!help  :  Affiche ce message\n!purge :  Permet de supprimer les messages\n!kick  :  Permet de kicker un utilisateur\n!ban   :  Permet de bannir un utilisateur```')

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

client.run(token)
