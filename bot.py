import discord
from discord.ext import commands
from discord.ui import View, Button
import os
from aiohttp import web

# ⚠️ [필독] 여기 상단 3가지 변수 정보가 내 주소와 ID에 맞게 적혀있는지만 꼭 확인해 주세요!
BOT_TOKEN = os.environ.get("DISCORD_TOKEN")
MY_ACCOUNT_INFO = "https://qr.kakaopay.com/FSPRjaCAp"
ADMIN_USER_ID = 1383372151498997790

# 🌌 판매할 라이벌스 스박 제품 리스트
SKYBOX_PRODUCTS = {
    "1": {
        "name": "🌌 우주 은하수 스박 (6개 파일 세트)", 
        "price": "1000", 
        "url": "여기에_구글_드라이브_폴더_공유_링크를_붙여넣으세요"
    },
    "2": {
        "name": "🌅 핑크빛 노을 스박 (6개 파일 세트)", 
        "price": "1500", 
        "url": "여기에_두번째_구글_드라이브_링크_입력"
    },
}

# 렌더 무한 대기 렉 방지용 가짜 웹 서버
async def handle(request): return web.Response(text="LIVE")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"🤖 라이벌스 파일 자판기 봇 로그인 완료: {bot.user.name}")
    try:
        await bot.tree.sync()
        print("✅ 슬래시 명령어 동기화 완료")
    except Exception as e: print(e)

@bot.event
async def setup_hook():
    app = web.Application(); app.add_routes([web.get('/', handle)])
    runner = web.AppRunner(app); await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 10000); bot.loop.create_task(site.start())

# 🛒 [버튼형 상점 뷰] 상품목록, 구매 3개 사각형 버튼 시스템
class ShopView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="상품목록 📦", style=discord.ButtonStyle.secondary)
    async def list_btn(self, interaction: discord.Interaction, button: Button):
        # ⚡ 버튼 클릭 즉시 디스코드 3초 만료 타이머를 일시정지 시킵니다!
        await interaction.response.defer(ephemeral=True) 
        
        product_text = ""
        for key, info in SKYBOX_PRODUCTS.items():
            product_text += f"**[{key}번] {info['name']}**\n┗ 💵 가격: {info['price']}원\n\n"
        
        embed = discord.Embed(
            title="📂 현재 판매 중인 스카이박스 목록",
            description=product_text + "*구매를 원하시면 [구매] 버튼을 누른 뒤 상품 번호를 입력해 주세요.*",
            color=discord.Color.blue()
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

    @discord.ui.button(label="구매 💳", style=discord.ButtonStyle.primary)
    async def buy_btn(self, interaction: discord.Interaction, button: Button):
        # ⚠️ 입력창(모달) 팝업을 띄우는 특수 버튼이므로 모달 본체에서 타이머를 지연시킵니다.
        class BuyModal(discord.ui.Modal, title="🛒 상품 구매 신청"):
            num_input = discord.ui.TextInput(label="구매할 상품 번호를 입력하세요", placeholder="예: 1", min_length=1, max_length=2)
            
            async def on_submit(self, modal_inter: discord.Interaction):
                # ⚡ 번호 입력 후 '제출' 누르는 순간 3초 타이머 즉시 일시정지!
                await modal_inter.response.defer(ephemeral=True)
                
                p_id = self.num_input.value
                if p_id not in SKYBOX_PRODUCTS:
                    await modal_inter.followup.send("❌ 존재하지 않는 상품 번호입니다. [상품목록]을 먼저 확인해 주세요.", ephemeral=True)
                    return
                
                product = SKYBOX_PRODUCTS[p_id]
                pay_embed = discord.Embed(
                    title=f"💸 구매 신청 완료: {product['name']}",
                    description=f"**💵 상품 가격:** {product['price']}원\n\n카카오페이로 금액을 송금하신 후 아래 **[입금 완료]** 버튼을 꼭 눌러주세요!\n\n📌 **송금처:** {MY_ACCOUNT_INFO}",
                    color=discord.Color.orange()
                )
                
                done_btn = Button(label="입금 완료 🌟", style=discord.ButtonStyle.blurple)
                
                async def done_callback(done_inter: discord.Interaction):
                    # ⚡ 입금 완료 버튼 클릭 즉시 3초 타이머 일시정지!
                    await done_inter.response.defer(ephemeral=True)
                    await done_inter.followup.send("⚙️ 관리자에게 입금 확인 요청을 보냈습니다. 잠시만 기다려주세요!", ephemeral=True)
                    
                    admin_user = await bot.fetch_user(ADMIN_USER_ID)
                    admin_embed = discord.Embed(
                        title="🔔 [라이벌스 스박 구매 요청 발생]",
                        description=(
                            f"**📦 신청 상품:** {product['name']}\n"
                            f"**💵 손님이 내야 할 진짜 가격:** {product['price']}원\n\n"
                            f"**👤 구매 요청자:** {done_inter.user.mention} ({done_inter.user.name})\n\n"
                            f"카카오톡 알림 창을 확인하여 **정확히 {product['price']}원**이 입금되었다면 아래 [승인]을 눌러주세요."
                        ),
                        color=discord.Color.red()
                    )
                    
                    approve_btn = Button(label="승인 (다운로드 링크 발급)", style=discord.ButtonStyle.success)
                    reject_btn = Button(label="거절 (취소 처리)", style=discord.ButtonStyle.danger)
                    
                    async def approve_callback(app_inter: discord.Interaction):
                        await app_inter.response.defer(ephemeral=True)
                        try:
                            await done_inter.user.send(
                                f"🌌 **{product['name']} 구매가 완료되었습니다!**\n\n"
                                f"**📂 [라이벌스 스카이박스 6개 파일 다운로드]**\n{product['url']}\n\n"
                                f"💡 **적용 방법:**\n다운로드한 파일들을 압축 해제하신 후, `Fishstrap` 환경의 `platform content > pc > textures > sky` 폴더에 기존 파일들과 교체(덮어쓰기)해 주세요!"
                            )
                            await app_inter.followup.send(f"✅ 승인 완료! {done_inter.user.name}님에게 다운로드 주소를 보냈습니다.", ephemeral=True)
                        except discord.Forbidden:
                            await app_inter.followup.send(f"❌ 발송 실패: {done_inter.user.name}님이 DM을 차단해 두었습니다.", ephemeral=True)
                    
                    async def reject_callback(rej_inter: discord.Interaction):
                        await rej_inter.response.defer(ephemeral=True)
                        try: await done_inter.user.send(f"❌ '{product['name']}' 구매 요청이 거절되었거나 입금이 확인되지 않았습니다.")
                        except: pass
                        await rej_inter.followup.send("❌ 구매 요청을 거절 처리했습니다.", ephemeral=True)

                    approve_btn.callback = approve_callback; reject_btn.callback = reject_callback
                    admin_view = View(); admin_view.add_item(approve_btn); admin_view.add_item(reject_btn)
                    await admin_user.send(embed=admin_embed, view=admin_view)

                done_btn.callback = done_callback
                pay_view = View(); pay_view.add_item(done_btn)
                await modal_inter.followup.send(embed=pay_embed, view=pay_view, ephemeral=True)

        await interaction.response.send_modal(BuyModal())

@bot.tree.command(name="가판대생성", description="스카이박스 멀티 상점 가판대를 생성합니다.")
async def create_shop(interaction: discord.Interaction):
    await interaction.response.defer() 
    
    embed = discord.Embed(
        title="🤖 SKYBOX STUDIO (스카이박스 전문 상점)",
        description=(
            "🇰🇷 **한국어 • 🇺🇸 English**\n\n"
            "📥 아래 버튼들을 눌러 포인트 충전 안내, 상품 선택, 금액 결제 및 파일 다운로드를 한 번에 이용하실 수 있습니다.\n\n"
            "**🔹 등록 카테고리:** 1개 • **🔹 판매 상품:** 멀티 보유 중\n\n"
            "──────────────────────────────\n"
            "원하시는 기능을 아래 버튼 메뉴에서 골라보세요!\n"
            "Select a function using the button menu below."
        ),
        color=discord.Color.from_rgb(43, 88, 255)
    )
    embed.set_image(url="https://unsplash.com") 
    embed.set_footer(text="⚡ 24 Hours Unlimited Skybox Vending Machine", icon_url=interaction.user.display_avatar.url)

    await interaction.followup.send(embed=embed, view=ShopView())

bot.run(BOT_TOKEN)
