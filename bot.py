import discord
from discord.ext import commands
from discord.ui import Select, View, Button

import os
import discord
from discord.ext import commands
from discord.ui import Select, View, Button

BOT_TOKEN = os.environ.get("DISCORD_TOKEN")
MY_ACCOUNT_INFO = "https://qr.kakaopay.com/FSPRjaCAp"
ADMIN_USER_ID = 1383372151498997790

SKYBOX_PRODUCTS = {
    "1": {"name": "stellive tell your world skybox", "price": "4500", "url": "https://drive.google.com/drive/folders/1BUfyGYMjL_uowfF6ojXGvJeyH7VGPEj3?usp=sharing"},
}

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"🤖 멀티 자판기 봇 로그인 완료: {bot.user.name}")
    try:
        await bot.tree.sync()
        print("✅ 슬래시 명령어 동기화 완료")
    except Exception as e: print(e)

class SkyboxSelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label=f"{info['name']} ({info['price']}원)", 
                description="선택 시 결제 안내 메시지가 나타납니다.", 
                value=key
            ) for key, info in SKYBOX_PRODUCTS.items()
        ]
        super().__init__(placeholder="🛒 구매하실 스카이박스를 선택해 주세요...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        selected_key = self.values[0]
        product = SKYBOX_PRODUCTS[selected_key]
        
        pay_embed = discord.Embed(
            title=f"💸 구매 신청: {product['name']}",
            description=f"**💵 상품 가격:** {product['price']}원\n\n아래 카카오페이 링크로 금액을 송금하신 후 **[입금 완료]** 버튼을 눌러주세요.\n\n**📌 송금처:** {MY_ACCOUNT_INFO}\n\n*주의: 관리자가 입금 확인 시 스박 ID가 발급됩니다.*",
            color=discord.Color.orange()
        )
        
        done_button = Button(label="입금 완료 🌟", style=discord.ButtonStyle.blurple)
        
        async def done_callback(done_inter: discord.Interaction):
            await done_inter.response.send_message("⚙️ 관리자에게 입금 확인 요청을 보냈습니다. 잠시만 기다려주세요!", ephemeral=True)
            
            admin_user = await bot.fetch_user(ADMIN_USER_ID)
            admin_embed = discord.Embed(
                title="🔔 [스박 구매 요청 발생]",
                description=f"**구매 상품:** {product['name']} ({product['price']}원)\n**구매 요청자:** {done_inter.user.mention} ({done_inter.user.name})\n\n카카오페이에 입금이 확인되었다면 아래 [승인]을 눌러주세요.",
                color=discord.Color.red()
            )
            
            approve_btn = Button(label="승인 (스박 발급)", style=discord.ButtonStyle.success)
            reject_btn = Button(label="거절 (취소 처리)", style=discord.ButtonStyle.danger)
            
            async def approve_callback(app_inter: discord.Interaction):
                try:
                    await done_inter.user.send(
                        f"🌌 **{product['name']} 구매가 완료되었습니다!**\n\n"
                        f"**[로블록스 라이벌스 스박 url]**\n`{product['url']}`\n\n"
                        f"⚠️ *주의: 타인에게 무단 유출 시 불이익을 받을 수 있습니다.*"
                    )
                    await app_inter.response.send_message(f"✅ 승인 완료! {done_inter.user.name}님에게 스박 url를 전송했습니다.", ephemeral=True)
                except discord.Forbidden:
                    await app_inter.response.send_message(f"❌ 발송 실패: {done_inter.user.name}님이 DM을 차단해 두었습니다.", ephemeral=True)
            
            async def reject_callback(rej_inter: discord.Interaction):
                try: await done_inter.user.send(f"❌ '{product['name']}' 구매 요청이 거절되었거나 입금이 확인되지 않았습니다.")
                except: pass
                await rej_inter.response.send_message("❌ 구매 요청을 거절 처리했습니다.", ephemeral=True)

            approve_btn.callback = approve_callback
            reject_btn.callback = reject_callback
            admin_view = View(); admin_view.add_item(approve_btn); admin_view.add_item(reject_btn)
            await admin_user.send(embed=admin_embed, view=admin_view)

        done_button.callback = done_callback
        pay_view = View(); pay_view.add_item(done_button)
        await interaction.response.send_message(embed=pay_embed, view=pay_view, ephemeral=True)

@bot.tree.command(name="가판대생성", description="스카이박스 멀티 상점 가판대를 생성합니다.")
async def create_shop(interaction: discord.Interaction):
    await interaction.response.defer()

    embed = discord.Embed(
        title="🌌 로블록스 라이벌스 스카이박스 전문 상점",
        description="원하시는 스카이박스 종류를 아래 메뉴에서 골라보세요!\n\n**💰 결제 수단:** 카카오페이 전용",
        color=discord.Color.blue()
    )
    view = View()
    view.add_item(SkyboxSelect())
    await interaction.followup.send(embed=embed, view=view)

bot.run(BOT_TOKEN)
