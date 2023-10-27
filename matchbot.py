# WRITTEN BY TAL ASHKENAZI
# GITHUB LINK FOUND AT: https://github.com/tal-ashkenazi01/BasicDiscordMatchmakingBot
import os
import discord
import random
from discord.ext import commands
from dotenv import load_dotenv
import interactions

intents = discord.Intents.all()
intents.message_content = True

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
# YOU CAN REPLACE THIS WITH THE TOKEN OR BY CREATING A .env FILE IN THE SAME DIRECTORY THAT CONTAINS DISCORD_TOKEN=YOUR_TOKEN
bot = commands.Bot(command_prefix='$-', intents=intents)


@bot.event
async def on_ready():
    # GENERAL CHAT:
    textChannel = bot.get_channel(0)  # REPLACE WITH CHANNEL ID


@bot.event
async def on_message(message):
    channels = [0, 1, 2]  # REPLACE WITH CHANNEL IDS
    if message.channel.id in channels:
        await bot.process_commands(message)


# START THE GAME WITH A COMMAND
@bot.command()
async def startGame(location):
    await location.send("Starting game")

    # GET THE VC
    channel = bot.get_channel(0)  # REPLACE WITH CHANNEL ID. Gets the channel you want to get the list from
    members = channel.members  # finds members connected to the channel

    # GET THE SPECIFIC USERS IN VC
    users_in_vc = []  # (list)
    for member in members:
        users_in_vc.append(member.id)

    # ERROR CHECKING
    if len(users_in_vc) <= 2:
        await location.send("Not enough users to start a game (Minimum 6)")
        return

    # SELECT THE TWO TEAM CAPTAINS
    teamCaptain1 = random.choice(users_in_vc)
    teamCaptain2 = random.choice(users_in_vc)

    # MAKE SURE THE TEAM CAPTAIN IS NOT THE SAME
    while teamCaptain2 == teamCaptain1:
        teamCaptain2 = random.choice(users_in_vc)

    server = bot.get_guild(0)  # REPLACE WITH GUILD ID
    teamCaptainRole = discord.utils.get(server.roles, id=0)  # REPLACE WITH ROLE ID
    member1 = await server.fetch_member(teamCaptain1)
    member2 = await server.fetch_member(teamCaptain2)

    # ADD THE TEAM CAPTAIN ROLES
    await member1.add_roles(teamCaptainRole)
    await member2.add_roles(teamCaptainRole)
    await location.send(f"Your two captains are: {member1.name} and {member2.name}")

    # FLIP A COIN TO SEE WHO PICKS FIRST
    global selectFirst
    selectFirst = random.choice([True, False])
    if selectFirst:
        await location.send(f"@{member1.name} is selecting first")
    else:
        await location.send(f"@{member2.name} is selecting first")

    # REMOVE THE TEAM CAPTAINS FROM THE LIST
    users_in_vc.remove(teamCaptain1)
    users_in_vc.remove(teamCaptain2)

    usersInTeamOne = []
    usersInTeamTwo = []

    async def buttonCallback(interaction):
        permittedRoleList = [x.id for x in interaction.user.roles]
        if (0 not in permittedRoleList) and (
                0 not in permittedRoleList):  # REPLACE WITH ROLE ID OF USERS PERMITTED TO START/END GAME, IN THIS EXAMPLE, IT WAS ADMIN AND TEAM CAPTAIN
            return

        # CHECK IF THE CORRECT USER SENT THE INTERACTION
        global selectFirst
        if (selectFirst and interaction.user == member1) or ((not selectFirst) and interaction.user == member2):
            if selectFirst:
                usersInTeamOne.append(int(interaction.data['custom_id']))
                selectFirst = False
            else:
                usersInTeamTwo.append(int(interaction.data['custom_id']))
                selectFirst = True

        users_in_vc.remove(int(interaction.data['custom_id']))
        if len(users_in_vc) <= 0:
            await display_teams(teamCaptain1, teamCaptain2, usersInTeamOne, usersInTeamTwo)

        updated_view = await create_view(users_in_vc)
        if selectFirst:
            await captainOnlyChannel.send(f"@{member1.name}'s turn to select", view=updated_view)
        else:
            await captainOnlyChannel.send(f"@{member2.name}'s turn to select", view=updated_view)

    # SHOW A LIST OF PEOPLE THAT CAN BE PICKED FROM
    async def create_view(userList):
        view = discord.ui.View()
        for i in userList:
            new_member_object = await server.fetch_member(i)
            new_button = discord.ui.Button(label=new_member_object.name, style=discord.ButtonStyle.green,
                                           custom_id=str(new_member_object.id))
            new_button.callback = buttonCallback
            view.add_item(new_button)
        return view

    captainOnlyChannel = bot.get_channel(0)  # REPLACE WITH CHANNEL ID
    new_view = await create_view(users_in_vc)
    if selectFirst:
        await captainOnlyChannel.send(f"@{member1.name}'s turn to select", view=new_view)
    else:
        await captainOnlyChannel.send(f"@{member2.name}'s turn to select", view=new_view)


# ON END COMMAND MOVE USERS BACK TO THE MAIN VC
@bot.command()
async def endGame(location):
    permittedRoleList = [x.id for x in location.author.roles]
    if (0 not in permittedRoleList) and (
            0 not in permittedRoleList):  # REPLACE WITH ROLE ID OF USERS PERMITTED TO START/END GAME, IN THIS EXAMPLE, IT WAS ADMIN AND TEAM CAPTAIN
        return

    # Gets the channel you want to get the list from
    team1channel = bot.get_channel(0)  # REPLACE WITH VOICE CHANNEL
    team2channel = bot.get_channel(0)  # REPLACE WITH VOICE CHANNEL
    completedGameChannel = bot.get_channel(0)  # REPLACE WITH VOICE CHANNEL

    # CONCATENATE THE TWO LISTS OF MEMBERS
    members = team1channel.members
    members.extend(team2channel.members)

    # REMOVE THE CAPTAIN ROLE FROM ALL USERS
    server = bot.get_guild(0)  # REPLACE WITH TEAM CAPTAIN/ROLE ID
    teamCaptainRole = discord.utils.get(server.roles, id=0)  # REPLACE WITH ROLE ID

    for current_member in members:
        await current_member.remove_roles(teamCaptainRole)
        await current_member.move_to(completedGameChannel)

    teamSelectChannel = bot.get_channel(0)  # REPLACE WITH TEXT CHANNEL WHERE TEAM SELECTION OCCURS
    await teamSelectChannel.purge(limit=100)

    await location.send("Ended game")


# RESET ALL OF THE USERS
@bot.command()
async def resetUsers(location):
    permittedRoleList = [x.id for x in location.author.roles]
    if 0 in permittedRoleList:  # REPLACE WITH IDS OF PERMITTED USERS
        team1channel = bot.get_channel(0)  # gets the channel you want to get the list from
        team2channel = bot.get_channel(0)
        completedGameChannel = bot.get_channel(0)

        # CONCATENATE THE TWO LISTS OF MEMBERS
        members = team1channel.members
        members.extend(team2channel.members)

        # REMOVE THE CAPTAIN ROLE FROM ALL USERS
        server = bot.get_guild(0)  # REPLACE WITH GUILD ID
        teamCaptainRole = discord.utils.get(server.roles, id=0)  # REPLACE WITH ROLE ID

        for current_member in members:
            await current_member.remove_roles(teamCaptainRole)
            await current_member.move_to(completedGameChannel)

        await location.send("Reset all users")


async def display_teams(captain1id, captain2id, team1, team2):
    server = bot.get_guild(0)  # REPLACE WITH GUILD ID
    # GET USERS
    captain1 = await server.fetch_member(captain1id)
    captain2 = await server.fetch_member(captain2id)

    # DISPLAY THE TWO TEAMS
    botOnlyChannel = bot.get_channel(0)  # REPLACE WITH VOICE CHANNEL
    team1channel = bot.get_channel(0)  # REPLACE WITH VOICE CHANNEL
    team2channel = bot.get_channel(0)  # REPLACE WITH VOICE CHANNEL

    await captain1.move_to(team1channel)
    await captain2.move_to(team2channel)

    team1MessageString = f"**Team 1:**\nCaptain: {captain1.name}"
    team2MessageString = f"**Team 2:**\nCaptain: {captain2.name}"

    for i in team1:
        on_member = await server.fetch_member(i)
        await on_member.move_to(team1channel)
        team1MessageString += f"\n- {on_member.name}"

    for i in team2:
        on_member = await server.fetch_member(i)
        await on_member.move_to(team2channel)
        team2MessageString += f"\n- {on_member.name}"

    await botOnlyChannel.send(team1MessageString)
    await botOnlyChannel.send(team2MessageString)


@bot.command()
async def getJuggernaut(location):
    # GET THE VC
    channel = bot.get_channel(1)  # REPLACE WITH CHANNEL -- gets the channel you want to get the list from
    members = channel.members  # finds members connected to the channel

    # GET THE SPECIFIC USERS IN VC
    juggernaut = random.choice(members)

    await location.send(f"Your juggernaut is: {juggernaut.name}")


bot.run(TOKEN)
