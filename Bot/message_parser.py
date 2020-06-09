# created by Sami Bosch on Wednesday, 27 November 2019

# This file contains all functions necessary to reply to messages
from asynctimer import AsyncTimer
import db_handler

from discord.ext import commands
import discord
from datetime import datetime, timedelta, date


def init(client):
    async def birthday(context, add=True):
        m = context.message
        if m.author.guild_permissions.administrator:
            split = m.content.split(" ")
            if len(split) > 2:
                i = 1
                s = ""
                f = ""
                while i < len(split):
                    name = split[i]
                    bday = split[i + 1]
                    try:
                        birth_date = datetime.strptime(bday, "%d/%m").date()
                        print(birth_date)
                        if add:
                            db_handler.add_birthday(name, birth_date)
                        else:
                            db_handler.remove_birthday(name, birth_date)
                        s += name + ", "
                    except ValueError:
                        f += name + ", "
                    i += 2
                s = "Successfully added birthdays for " + s[:-2] + ". " if s != "" else ""
                f = "Failed to add for " + f[:-2] + "." if f != "" else ""
                await context.send(s + f)
            else:
                await context.send("Please provide at least one pair.")
        else:
            await context.send("You don't have permissions for that!")

    class Birthdays(commands.Cog):
        @commands.command(pass_context=True)
        async def add_birthday(self, context):
            """Adds a birthday for an AC character. You can give a list paired by name-date to add multiple. Date must be dd/mm.
            Usage: %add_birthday name date"""
            await birthday(context)

        @commands.command(pass_context=True)
        async def remove_birthday(self, context):
            """Removes a birthday for an AC character. You can give a list paired by name-date to add multiple. Date must be dd/mm.
            Usage: %remove_birthday name date"""
            await birthday(context, add=False)

    class Events(commands.Cog):
        @commands.command(pass_context=True)
        async def add_event(self, context):
            """Schedules an event. Date must be dd/mm/yyyy.
            Usage: %add_event name date"""
            m = context.message
            if m.author.guild_permissions.administrator:
                split = m.content.split(" ")
                if len(split) >= 3:
                    if split[1] == "-o":
                        one_time = True
                        name = " ".join(split[2:-1])
                    else:
                        one_time = False
                        name = " ".join(split[1:-1])
                    event_date = split[-1]
                    try:
                        edate = datetime.strptime(event_date, "%d/%m/%Y").date()
                        db_handler.add_event(name, edate, one_time)
                        await context.send("Added event.")
                    except ValueError:
                        await context.send("Wrong date format.")
                else:
                    await context.send("Please provide a name and a date.")
            else:
                await context.send("You don't have permissions for that!")

        @commands.command(pass_context=True)
        async def remove_event(self, context):
            """Removes an event.
            Usage: %add_event name"""
            m = context.message
            if m.author.guild_permissions.administrator:
                split = m.content.split(" ")
                if len(split) >= 2:
                    name = " ".join(split[1:])
                    db_handler.remove_event(name)
                    await context.send("Removed event.")
                else:
                    await context.send("Please provide a name.")
            else:
                await context.send("You don't have permissions for that!")

        @commands.command(pass_context=True)
        async def list_events(self, context):
            """Lists all events.
            Usage: %list_events"""
            m = context.message
            if m.author.guild_permissions.administrator:
                s = ""
                for name in db_handler.db['events']:
                    s += name + " - " + db_handler.get_event_date(name)[0] + "\n"
                await context.send(s)
            else:
                await context.send("You don't have permissions for that!")

    class Utility(commands.Cog):
        @commands.command(pass_context=True)
        async def set_channel(self, context):
            """Sets the channel for events and bdays.
            Usage: %set_channel"""
            m = context.message
            if m.author.guild_permissions.administrator:
                if len(m.channel_mentions) == 1:
                    channel = m.channel_mentions[0]
                    cid = channel.id
                    gid = channel.guild.id
                else:
                    cid = m.channel.id
                    gid = m.guild.id
                db_handler.set_channel(gid, cid)
                await context.send("Successfully configured channel!")
            else:
                await context.send("You don't have permissions for that!")

        @commands.command(pass_context=True)
        async def set_role(self, context):
            """Sets the channel for events and bdays.
            Usage: %set_channel"""
            m = context.message
            if m.author.guild_permissions.administrator:
                if len(m.role_mentions) == 1:
                    role = m.role_mentions[0]
                    rid = role.id
                    gid = role.guild.id
                    db_handler.set_role(gid, rid)
                    await context.send("Successfully configured role!")
                else:
                    await context.send("Please provide a role.")
            else:
                await context.send("You don't have permissions for that!")

    class Flairing(commands.Cog):
        @commands.command(pass_context=True)
        async def rooli(self, context):
            """Gives the user the requested role (if on rank list)"""
            m = context.message
            u = m.author
            pos = m.content.find(" ")
            if pos > 0:
                name = m.content[pos:].strip()
                role = discord.utils.get(m.guild.roles, name=name)
                if name in db_handler.get_flairs():
                    await u.add_roles(role)
                    await context.send("Liityit rooliin {}.".format(role.name))
                else:
                    await context.send("Ei roolia nimeltä {}!".format(name))
            else:
                await context.send("Kerro roolin nimi")

        @commands.command(pass_context=True)
        async def poistu(self, context):
            """Removes requested role from user."""
            m = context.message
            u = m.author
            pos = m.content.find(" ")
            if pos > 0:
                name = m.content[pos:].strip()
                role = discord.utils.get(m.guild.roles, name=name)
                if role in u.roles and name in db_handler.get_flairs():
                    await u.remove_roles(role)
                    await context.send("Poistuit roolista {}.".format(role.name))
                else:
                    await context.send("Ei roolia nimeltä {}!".format(name))
            else:
                await context.send("Kerro roolin nimi")

        @commands.command(aliases=["create_rank"], pass_context=True)
        async def add_rooli(self, context):
            """Adds a role to allowed ranks. If the role doesn't exist, creates it.
            Only usable with manage roles permission."""
            m = context.message
            u = m.author
            if u.guild_permissions.manage_roles:
                pos = m.content.find(" ")
                if pos > 0:
                    name = m.content[pos:].strip()
                    role = discord.utils.get(m.guild.roles, name=name)
                    if role is not None:
                        await context.send("Added role {}.".format(role.name))
                        db_handler.add_flair(name)
                    else:
                        role = await m.guild.create_role(name=name)
                        await context.send("Created role {}.".format(role.name))
                        db_handler.add_flair(name)
                else:
                    await context.send("Please provide a name.")
            else:
                await context.send("You don't have permission to use this command.")

        @commands.command(pass_context=True)
        async def remove_rooli(self, context):
            """Removes a role from allowed ranks, without deleting the role.
            Only usable with manage roles permission."""
            m = context.message
            u = m.author
            if u.guild_permissions.manage_roles:
                pos = m.content.find(" ")
                if pos > 0:
                    name = m.content[pos:].strip()
                    if name in db_handler.get_flairs():
                        await context.send("Removed role {}.".format(name))
                        db_handler.remove_flair(name)
                    else:
                        await context.send("This is not a valid role.")
                else:
                    await context.send("Please provide a name.")
            else:
                await context.send("You don't have permission to use this command.")

        @commands.command(pass_context=True)
        async def delete_rooli(self, context):
            """Deletes a role in allowed ranks.
            Only usable with manage roles permission."""
            m = context.message
            u = m.author
            if u.guild_permissions.manage_roles:
                pos = m.content.find(" ")
                if pos > 0:
                    name = m.content[pos:].strip()
                    if name in db_handler.get_flairs():
                        role = discord.utils.get(m.guild.roles, name=name)
                        await context.send("Deleted role {}.".format(name))
                        db_handler.remove_flair(name)
                        await role.delete()
                    else:
                        await context.send("This is not a valid role.")
                else:
                    await context.send("Please provide a name.")
            else:
                await context.send("You don't have permission to use this command.")

        @commands.command(pass_context=True)
        async def list_rooli(self, context):
            """Lists all ranks."""
            m = context.message
            u = m.author
            if u.guild_permissions.manage_roles:
                s = ""
                for name in db_handler.get_flairs():
                    s += name + ":\t" + str(len(user_list(name, m.guild))) + " käyttäjää\n"
                await context.send(s.strip() if s is not "" else "/")
            else:
                await context.send("You don't have permission to use this command.")

    client.add_cog(Birthdays())
    client.add_cog(Events())
    client.add_cog(Utility())
    client.add_cog(Flairing())

    @client.event
    async def on_member_join(member):
        _, rid = db_handler.get_role()
        role = member.guild.get_role(rid)
        print(role)
        # await member.add_roles(role)

    def secs():
        x = datetime.today()
        x_temp = x.replace(hour=5, minute=0, second=0, microsecond=0)
        y = x_temp if x_temp > x else x_temp + timedelta(days=1)
        delta_t = y - x
        return delta_t.seconds + 1

    async def send_events():
        AsyncTimer(secs(), send_events)
        print(secs())

        coming = ""
        now = ""

        remove = []

        events = db_handler.get_events()
        for event in events:
            event_info = db_handler.get_event_date(event)
            edate = datetime.strptime(event_info[0], "%d/%m/%Y").date()
            today = date.today()
            delta = edate - today
            if delta.days == 0:
                now += ":star2: Tapahtuma tänään: " if event_info[1] else "" + event + "\n"
                remove.append(event)
            elif delta.days < 0:
                remove.append(event)
            elif not event_info[1]:
                coming += ":star2: " + str(delta.days) + " päivää tapahtumaan: " + event + "\n"

        for event in remove:
            db_handler.remove_event(event)

        s = now + "\n" + coming + "\n"

        birthdays = db_handler.get_birthdays(date.today())
        for name in birthdays:
            s += ":birthday: Tänään syntymäpäivää viettää " + name + "\n"

        gid, cid = db_handler.get_channel()
        guild = client.get_guild(gid)
        channel = guild.get_channel(cid)
        await channel.send(s)

    AsyncTimer(secs(), send_events)


def user_list(name, s):
    u_list = []
    for member in s.members:
        for role in member.roles:
            if role.name == name:
                u_list.append(member.name)
    return u_list
