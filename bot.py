import discord
from discord.ext import commands
from discord.ui import Select, View, Button
import os

# ⚠️ 여기 아래 2가지 기본 정보만 내 것에 맞게 수정하세요!
BOT_TOKEN = os.environ.get("DISCORD_TOKEN")
MY_ACCOUNT_INFO = "https://qr.kakaopay.com/FSPRjaCAp"
ADMIN_USER_ID = 1383372151498997790

# 🌌 판매할 라이벌스 스박 제품 리스트 (구글 드라이브 링크를 넣어줍니다!)
SKYBOX_PRODUCTS = {
    "1": {"name": "stellive tell your world skybox", "price": "4500", "url": "https://drive.google.com/drive/folders/1BUfyGYMjL_uowfF6ojXGvJeyH7VGPEj3?usp=sharing"},
}

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

# 🌌 [수정해야 할 영역] 코드 중간 @bot.event 바로 윗부분을 찾으세요!

# 👇 이 3줄 코드를 새로 추가해 줍니다! (렌더 시스템에게 가짜 웹 주소를 던져서 1초 만에 초록불을 띄우는 마법의 코드)
from aiohttp import web
async def handle(request): return web.Response(text="LIVE")
bot.loop.create_task(web._run_app(web.Application([web.get('/', handle)]), port=10000))

@bot.event
async def on_ready():
    print(f"🤖 라이벌스 파일 자판기 봇 로그인 완료: {bot.user.name}")
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
        super().__init__(placeholder="🛒 구매하실 라이벌스 스박을 선택해 주세요...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        selected_key = self.values[0]
        product = SKYBOX_PRODUCTS[selected_key]
        
        pay_embed = discord.Embed(
            title=f"💸 구매 신청: {product['name']}",
            description=f"**💵 상품 가격:** {product['price']}원\n\n아래 카카오페이 링크로 금액을 송금하신 후 **[입금 완료]** 버튼을 눌러주세요.\n\n**📌 송금처:** {MY_ACCOUNT_INFO}\n\n*주의: 관리자가 입금 확인 시 6개 텍스처 파일 다운로드 주소가 발급됩니다.*",
            color=discord.Color.orange()
        )
        
        done_button = Button(label="입금 완료 🌟", style=discord.ButtonStyle.blurple)
        
        async def done_callback(done_inter: discord.Interaction):
            await done_inter.response.send_message("⚙️ 관리자에게 입금 확인 요청을 보냈습니다. 잠시만 기다려주세요!", ephemeral=True)
            
            admin_user = await bot.fetch_user(ADMIN_USER_ID)
            admin_embed = discord.Embed(
                title="🔔 [라이벌스 스박 구매 요청 발생]",
                description=(
                    f"**📦 신청 상품:** {product['name']}\n"
                    f"**💵 손님이 내야 할 진짜 가격:** {product['price']}원\n\n"
                    f"**👤 구매 요청자:** {done_inter.user.mention} ({done_inter.user.name})\n\n"
                    f"핸드폰 카카오톡 알림 창을 확인하여 **정확히 {product['price']}원**이 입금되었다면 아래 [승인]을 눌러주세요."
                ),
                color=discord.Color.red()
            )
            
            approve_btn = Button(label="승인 (다운로드 링크 발급)", style=discord.ButtonStyle.success)
            reject_btn = Button(label="거절 (취소 처리)", style=discord.ButtonStyle.danger)
            
            async def approve_callback(app_inter: discord.Interaction):
                try:
                    await done_inter.user.send(
                        f"🌌 **{product['name']} 구매가 완료되었습니다!**\n\n"
                        f"**📂 [라이벌스 스카이박스 6개 파일 다운로드]**\n{product['url']}\n\n"
                        f"💡 **적용 방법:**\n"
                        f"다운로드한 파일들을 압축 해제하신 후, `Fishstrap` 환경의 `platform content > pc > textures > sky` 폴더에 기존 파일들과 교체(덮어쓰기)해 주세요!\n\n"
                        f"⚠️ *주의: 무단 파일 유출 시 불이익을 받을 수 있습니다.*"
                    )
                    await app_inter.response.send_message(f"✅ 승인 완료! {done_inter.user.name}님에게 다운로드 주소를 갠디로 보냈습니다.", ephemeral=True)
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
        title="🤖 SKYBOX STUDIO (스카이박스 전문 상점)",
        description=(
            "🇰🇷 **한국어 • 🇺🇸 English**\n\n"
            "📥 아래 메뉴를 눌러 카테고리별 상품 선택, 금액 결제 및 파일 다운로드를 한 번에 이용하실 수 있습니다.\n\n"
            "**🔹 등록 카테고리:** 1개 • **🔹 판매 상품:** 멀티 보유 중\n\n"
            "──────────────────────────────\n"
            " 원하는 스카이박스 종류를 아래 선택 메뉴에서 골라보세요!\n"
            " Select a function using the dropdown menu below."
        ),
        color=discord.Color.from_rgb(43, 88, 255)
    )
    
    embed.set_image(url="https://unsplash.com") 
    embed.set_footer(text="⚡ 24 Hours Unlimited Skybox Vending Machine", icon_url=interaction.user.display_avatar.url)

    view = View()
    view.add_item(SkyboxSelect())
    await interaction.followup.send(embed=embed, view=view)

bot.run(BOT_TOKEN)
