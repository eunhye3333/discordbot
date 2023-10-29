import discord
from discord.ext import commands
from datetime import datetime, timedelta, timezone

TOKEN = 'token'
CHANNEL_ID = 'channel'

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True
intents.messages = True

bot = commands.Bot(command_prefix='!', intents=intents)


@bot.event
async def on_ready():
    print(f'Login bot: {bot.user}')


# @bot.command()
# async def start_thread(ctx):
#     channel = ctx.channel  # 현재 커맨드가 실행된 채널을 가져옵니다.
#     thread_name = "New Thread"  # 생성할 스레드의 이름을 설정합니다.
#
#     # create_thread 메서드를 사용하여 스레드를 생성합니다.
#     thread = await channel.create_thread(name=thread_name)
#
#     await ctx.send(f"새로운 스레드 '{thread.name}'이 생성되었습니다!")


# @bot.event
# async def on_thread_create(thread):
#     channel = thread.parent if isinstance(thread, discord.Thread) else thread.channel
#     member_name = thread.name
#     members = channel.guild.members
#     found_members = [member for member in members if member.name == member_name]
#
#     if found_members:
#         member_id = found_members[0].id
#         user = await bot.fetch_user(member_id)
#         print('success')
# print(f'A new thread has been created in #{channel.name}')


# 멤버 입장 시 포럼 - 스레드 생성
@bot.event
async def on_member_join(member):
    try:
        channel = bot.get_channel(int(CHANNEL_ID))

        if channel is not None:
            thread = await channel.create_thread(name=member.name, content=f'<@{member.id}>')
            await thread.thread.add_user(member)
    except Exception as e:
        # 오류 처리 로직 구현
        print(f"An error occurred during member join: {e}")


# 멤버 닉네임 변경 시 포럼 - 스레드 제목 수정
@bot.event
async def on_member_update(before, after):
    if before.nick != after.nick:
        # 멤버의 닉네임이 변경되었을 때 실행되는 코드
        if before.nick:
            old_nickname = before.nick
        else:
            old_nickname = before.name
        new_nickname = after.nick  # 새로운 닉네임

        channel = bot.get_channel(int(CHANNEL_ID))

        for thread in channel.threads:
            if thread.name == old_nickname:
                thread_members = await thread.fetch_members()
                if thread_members and thread_members is not None:
                    for thread_member in thread_members:
                        if thread_member.id == after.id:
                            await thread.edit(name=new_nickname)
                            print(f"Member {after.name} changed nickname from '{old_nickname}' to '{new_nickname}'")


# 주간 개인 과제 확인 (멤버 리스트로 확인)
@bot.command()
async def we(ctx):
    channel = bot.get_channel(int(CHANNEL_ID))

    if channel is None:
        await ctx.send('채널을 확인할 수 없습니다')
        return

    threads = channel.threads

    guild = channel.guild
    member_list = guild.members
    penalty_members = {member.id: member for member in member_list}

    count = 0

    await ctx.send('과제 확인 시작')
    for thread in threads:
        message_id = thread.last_message_id
        try:
            message = await thread.fetch_message(int(message_id))
        except Exception as e:
            continue

        done_member = message.author
        if done_member.bot:
            continue

        # UTC 시간을 KST로 변환
        kst_timezone = timezone(timedelta(hours=9))  # 한국 표준시(KST)
        created_at_kst = message.created_at.astimezone(kst_timezone)

        if message.edited_at:
            edited_at_kst = message.edited_at.astimezone(kst_timezone)
        else:
            edited_at_kst = created_at_kst

        # 현재 시간과 비교할 범위 계산 (KST)
        now_kst = datetime.now(kst_timezone)
        start_of_week_kst = now_kst - timedelta(days=now_kst.weekday() + 7)

        # 메시지 생성 날짜와 편집 날짜 확인 (UTC -> KST)
        created_at_in_range = (
                start_of_week_kst.date() <= created_at_kst.date() <= now_kst.date()
        )

        edited_at_in_range = (
                start_of_week_kst.date() <= edited_at_kst.date() <= now_kst.date()
        )

        if created_at_in_range or edited_at_in_range:
            done_member_id = done_member.id
            if done_member_id in penalty_members:
                del penalty_members[done_member_id]

            done_member_nick = done_member.nick

            if done_member_nick is None:
                done_member_nick = done_member.display_name
            await ctx.send(f'{done_member_nick} ({created_at_kst.date()})')
            count += 1

    await ctx.send(f'과제 확인 완료: 총 {count}명')
    await ctx.send('-----------------------\n과제 미수행 멤버')

    for key in penalty_members:
        penalty_member = penalty_members[key]
        if penalty_member.bot:
            continue
        penalty_member_nick = penalty_member.nick

        if penalty_member_nick is None:
            penalty_member_nick = penalty_member.display_name
        await ctx.send(f'{penalty_member_nick}')


# 주간 개인 과제 확인 (스레드 이름으로 확인)
@bot.command()
async def wa(ctx):
    channel = bot.get_channel(int(CHANNEL_ID))

    if channel is None:
        await ctx.send('채널을 확인할 수 없습니다')
        return

    threads = channel.threads
    penalty_members = []
    count = 0

    await ctx.send('과제 확인 시작')
    for thread in threads:
        message_id = thread.last_message_id
        try:
            message = await thread.fetch_message(int(message_id))
        except Exception as e:
            continue

        # UTC 시간을 KST로 변환
        kst_timezone = timezone(timedelta(hours=9))  # 한국 표준시(KST)
        created_at_kst = message.created_at.astimezone(kst_timezone)

        if message.edited_at:
            edited_at_kst = message.edited_at.astimezone(kst_timezone)
        else:
            edited_at_kst = created_at_kst

        # 현재 시간과 비교할 범위 계산 (KST)
        now_kst = datetime.now(kst_timezone)
        start_of_week_kst = now_kst - timedelta(days=7)

        # 메시지 생성 날짜와 편집 날짜 확인 (UTC -> KST)
        created_at_in_range = (
                start_of_week_kst.date() <= created_at_kst.date() <= now_kst.date()
        )

        edited_at_in_range = (
                start_of_week_kst.date() <= edited_at_kst.date() <= now_kst.date()
        )

        if created_at_in_range or edited_at_in_range:
            done_member = message.author
            done_member_nick = done_member.nick

            if done_member_nick is None:
                done_member_nick = done_member.display_name

            if done_member_nick == message.channel.name:
                if done_member.bot:
                    continue
                await ctx.send(f'{done_member_nick} ({created_at_kst.date()})')
                count += 1
            else:
                penalty_members.append(message.channel.name)
        else:
            penalty_members.append(message.channel.name)
    await ctx.send(f'과제 확인 완료: 총 {count}명')
    await ctx.send('-----------------------\n과제 미수행 멤버')
    output = ', '.join(str(x) for x in penalty_members)
    await ctx.send(f'[{output}] 총 {len(penalty_members)}명')


bot.run(TOKEN)
