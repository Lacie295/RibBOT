# created by Sami Bosch on Wednesday, 27 November 2019

# This file contains all functions necessary to reply to messages
from asynctimer import AsyncTimer
import db_handler

from discord.ext import commands
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
                    name = " ".join(split[1:-1])
                    event_date = split[-1]
                    try:
                        edate = datetime.strptime(event_date, "%d/%m/%Y").date()
                        db_handler.add_event(name, edate)
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
                    s += name + " - " + db_handler.get_event_date(name) + "\n"
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

    client.add_cog(Birthdays())
    client.add_cog(Events())
    client.add_cog(Utility())

    @client.event
    async def on_member_join(member):
        _, rid = db_handler.get_role()
        role = member.guild.get_role(rid)
        print(role)
        await member.add_roles(role)

    def secs():
        x = datetime.today()
        x_temp = x.replace(hour=5, minute=0, second=0, microsecond=0)
        y = x_temp if x_temp > x else x_temp + timedelta(days=1)
        delta_t = y - x
        return (delta_t.seconds + 1) % 60

    async def send_events():
        AsyncTimer(secs(), send_events)

        coming = ""
        now = ""

        remove = []

        events = db_handler.get_events()
        for event in events:
            edate = datetime.strptime(db_handler.get_event_date(event), "%d/%m/%Y").date()
            today = date.today()
            delta = edate - today
            if delta.days == 0:
                now += ":star2: Tapahtuma tänään: " + event + "\n"
                remove.append(event)
            elif delta.days < 0:
                remove.append(event)
            else:
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
